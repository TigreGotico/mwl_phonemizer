import os
import random

from mwl_phonemizer.base import MirandesePhonemizer, Dialects, DIALECT_TO_SPEC_CODE
import sklearn_crfsuite
from rapidfuzz.distance import Levenshtein
from enum import Enum
import joblib

from orthography2ipa import G2P


class AlignmentStrategy(str, Enum):
    PAD = "pad"
    LEV = "lev"


def align_with_lev(espeak_seq: str, gold_seq: str):
    """
    Align espeak IPA and gold IPA using Levenshtein editops.
    Returns two equal-length lists (espeak_aligned, gold_aligned),
    where gaps are represented as '+' or '-'.
    """
    es = list(espeak_seq)
    gd = list(gold_seq)

    ops = [(e.tag, e.src_pos, e.dest_pos) for e in Levenshtein.editops(es, gd)]
    es_aligned, gd_aligned = [], []
    i, j = 0, 0

    for op, src, tgt in ops:
        # copy until op position
        while i < src and j < tgt:
            es_aligned.append(es[i]);
            gd_aligned.append(gd[j])
            i += 1;
            j += 1

        if op == "replace":
            es_aligned.append(es[i]);
            gd_aligned.append(gd[j])
            i += 1;
            j += 1
        elif op == "insert":  # insert in gold
            es_aligned.append(".");
            gd_aligned.append(gd[j])
            j += 1
        elif op == "delete":  # delete from espeak
            es_aligned.append(es[i]);
            gd_aligned.append(".")
            i += 1

    # copy remaining tail
    while i < len(es) and j < len(gd):
        es_aligned.append(es[i]);
        gd_aligned.append(gd[j])
        i += 1;
        j += 1
    while i < len(es):
        es_aligned.append(es[i]);
        gd_aligned.append(".")
        i += 1
    while j < len(gd):
        es_aligned.append(".");
        gd_aligned.append(gd[j])
        j += 1

    return es_aligned, gd_aligned


def align_pad(ipa_seq: str, gold_seq: str):
    # If word and IPA lengths differ, use character-level alignment with padding
    ipa_aligned = list(ipa_seq)
    gd_aligned = list(gold_seq)
    while len(ipa_aligned) < len(gd_aligned):
        ipa_aligned.append(".")
    while len(ipa_aligned) > len(gd_aligned):
        gd_aligned.append(".")
    return ipa_aligned, gd_aligned


def align_gold_to_graphemes(top1_seq: list[str], gold_ipa: str) -> list[str]:
    """Distribute a gold IPA string over o2i grapheme slots, 1:1.

    ``orthography2ipa`` tokenizes a word into maximal-munch **graphemes**
    (``lh``, ``gu``, ``ie`` … are single tokens) and, per grapheme, offers a
    top-1 IPA guess. To train a CRF whose feature sequence is per-grapheme,
    the gold IPA labels must line up with that grapheme sequence — one label
    per grapheme, not per raw character.

    This aligner concatenates the per-grapheme top-1 guesses into a single
    predicted IPA string (remembering which grapheme owns each predicted
    character), then char-aligns that prediction to the gold IPA with
    rapidfuzz Levenshtein ``opcodes``. Every gold character is attributed to
    the grapheme that owns the predicted character it aligns to; gold
    characters with no predicted counterpart (insertions) attach to the
    preceding grapheme. The alignment is monotonic, so the returned labels —
    one per grapheme, each a possibly multi-character or empty IPA string —
    concatenate back to the gold IPA and line up 1:1 with the o2i feature
    sequence.
    """
    n = len(top1_seq)
    labels = ["" for _ in range(n)]
    if n == 0:
        return labels

    pred_chars: list[str] = []
    owner: list[int] = []
    for gi, ipa in enumerate(top1_seq):
        for ch in ipa:
            pred_chars.append(ch)
            owner.append(gi)

    gold_chars = list(gold_ipa)
    if not pred_chars:
        # no grapheme offered any IPA guess; dump gold on the first slot
        labels[0] = gold_ipa
        return labels

    for op in Levenshtein.opcodes(pred_chars, gold_chars):
        tag, i1, i2, j1, j2 = (op.tag, op.src_start, op.src_end,
                               op.dest_start, op.dest_end)
        if tag in ("equal", "replace"):
            span = i2 - i1
            for k in range(j2 - j1):
                pi = i1 + min(k, span - 1)
                labels[owner[pi]] += gold_chars[j1 + k]
        elif tag == "insert":
            # gold char(s) with no predicted counterpart: attach to the
            # preceding grapheme (or the first slot at word start)
            oi = owner[i1 - 1] if i1 > 0 else owner[0]
            for k in range(j1, j2):
                labels[oi] += gold_chars[k]
        # "delete": predicted char absent from gold -> nothing to assign
    return labels


class CRFPhonemizer(MirandesePhonemizer):
    """CRF grapheme-to-phoneme backend trained on ``orthography2ipa`` features.

    The feature sequence is the linguistically-grounded per-grapheme feature
    export from ``G2P(spec).features(word)`` (phonological-class predicates,
    word-local grapheme neighbours, the ranked candidate lattice's top-1/cost,
    per-word confidence …) instead of a hand-rolled ±3 character window. Gold
    IPA labels are aligned to that grapheme tokenization via
    :func:`align_gold_to_graphemes`, so labels line up 1:1 with the features.

    Subclasses that feed the CRF something other than orthographic Mirandese
    text (e.g. an IPA→IPA corrector) select ``feature_backend="char"`` to fall
    back to the character-window features + Levenshtein label alignment.
    """

    #: "o2i" -> per-grapheme features from orthography2ipa (default);
    #: "char" -> character-window features + char-level Levenshtein alignment.
    feature_backend = "o2i"

    def __init__(self, crf_model_path: str | None = None,
                 strategy=AlignmentStrategy.LEV,
                 algorithm='lbfgs',
                 c1=0.1,
                 c2=0.1,
                 max_iterations=100,
                 all_possible_transitions=False,
                 apply_manual_fixes=False,
                 ignore_stress=True,
                 train_data: list[tuple[str,str]] | None = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crf_model_path = crf_model_path
        self.algorithm = algorithm
        self.c1 = c1
        self.c2 = c2
        self.max_iterations = max_iterations
        self.all_possible_transitions = all_possible_transitions
        self.strategy = strategy
        self.manual_fixes = apply_manual_fixes
        self.model = None
        self.ignore_stress = ignore_stress
        self._g2p = None
        if crf_model_path and os.path.exists(crf_model_path):
            self.load_model(crf_model_path)
        elif train_data:
            self.train_crf(train_data)
        else:
            self.train_on_gold()

    # ------------------------------------------------------------------
    # orthography2ipa feature export
    # ------------------------------------------------------------------
    def _o2i(self) -> G2P:
        """Return (and cache) the ``G2P`` engine for this instance's spec."""
        if self._g2p is None:
            code = DIALECT_TO_SPEC_CODE.get(self.dialect, "mwl")
            self._g2p = G2P(code)
        return self._g2p

    def _grapheme_records(self, text: str):
        """Per-grapheme o2i feature dicts + top-1 IPA guesses for *text*.

        Returns ``(features, top1)`` where ``features`` is the CRF feature
        sequence (one flat, scalar, ``None``-free dict per grapheme) and
        ``top1`` is the parallel list of per-grapheme top-1 IPA guesses used
        for gold-label alignment.
        """
        features: list[dict] = []
        top1: list[str] = []
        for wf in self._o2i().features(text):
            for d in wf.as_dicts():
                top1.append(d.get("top1_ipa") or "")
                # crfsuite feature values must be str/bool/int/float, not None
                features.append({k: ("" if v is None else v)
                                 for k, v in d.items()})
        return features, top1

    def train_on_gold(self):
        # Prepare training data from GOLD dictionary
        train_data = [(self.grapheme_transforms(word), gold)
                      for word, gold in self.GOLD.items()]
        # Train CRF
        self.train_crf(train_data)

    def _apply_postfixes(self, word: str, phonemes: str) -> str:
        # due to the way alignmenet is approximated
        # the CRF often learns to drop the last phoneme
        # this hack adds back some of those based on simple heuristics
        if not word or not phonemes:
            return ""
        w_ends_with_vowel = word[-1] in "aáeéiíoóuú"
        p_ends_with_vowel = phonemes[-1] in ["a", "ɐ",
                                             "ɛ", "ɨ",
                                             "i", "j",
                                             "ɔ", "o", "ʊ",
                                             "u", "w", "ũ"]

        fixed_phonemes = phonemes
        if w_ends_with_vowel and not p_ends_with_vowel:
            # guess missing vowel
            if word[-1] == "a":
                fixed_phonemes += "ɐ"
            elif word[-1] == "á":
                fixed_phonemes += "a"
            elif word[-1] == "e":
                fixed_phonemes += "ɨ"
            elif word[-1] == "é":
                fixed_phonemes += "ɛ"
            elif word[-1] == "i":
                fixed_phonemes += "i"
            elif word[-1] == "ó":
                fixed_phonemes += "ɔ"
            elif word[-1] == "o":
                fixed_phonemes += "u"
            elif word[-1] == "u":
                fixed_phonemes += "u"

        elif p_ends_with_vowel and not w_ends_with_vowel:
            # guess missing consonant
            if word[-1] == "ç":
                fixed_phonemes += "s̻"
            elif word[-1] == "s":
                fixed_phonemes += "s̻"
            elif word[-1] == "n":
                fixed_phonemes += "n"
            elif word[-1] == "r":
                fixed_phonemes += "r"
            elif word[-1] == "l":
                fixed_phonemes += "l"

        return fixed_phonemes

    def extract_features(self, str_input):
        """Feature sequence for one input token.

        With ``feature_backend == "o2i"`` (default) this returns the
        per-grapheme ``orthography2ipa`` feature dicts for *str_input*. With
        ``"char"`` it returns the legacy per-character ±3 window features
        (used by IPA→IPA corrector subclasses whose input is not orthographic
        Mirandese text).
        """
        if self.feature_backend == "o2i":
            features, _ = self._grapheme_records(str_input)
            return features
        return self._extract_char_features(str_input)

    @staticmethod
    def _extract_char_features(str_input):
        # Simple character-level ±3 window features for CRF.
        features = []
        for i, char in enumerate(str_input):
            feats = {
                'char': char,
                'is_first': i == 0,
                'is_last': i == len(str_input) - 1,
                'prev_char': '' if i == 0 else str_input[i - 1],
                'next_char': '' if i == len(str_input) - 1 else str_input[i + 1],
                'prev_char2': '' if i < 2 else str_input[i - 2],
                'next_char2': '' if i >= len(str_input) - 2 else str_input[i + 2],
                'prev_char3': '' if i < 3 else str_input[i - 3],
                'next_char3': '' if i >= len(str_input) - 3 else str_input[i + 3]
            }
            features.append(feats)
        return features

    def train_crf(self, train_data):
        X, y = [], []
        random.shuffle(train_data)
        for str_input, gold_ipa in train_data:
            gold_ipa = self.strip_markers(gold_ipa)
            str_input = self.strip_markers(str_input)
            if self.ignore_stress:
                str_input = self.strip_stress(str_input)
                gold_ipa = self.strip_stress(gold_ipa)

            if self.feature_backend == "o2i":
                # features + labels both keyed on the o2i grapheme tokens
                feats, top1 = self._grapheme_records(str_input)
                if not feats:
                    continue
                labels = align_gold_to_graphemes(top1, gold_ipa)
                X.append(feats)
                y.append(labels)
            else:
                # legacy char-window path (IPA->IPA corrector subclasses)
                if self.strategy == AlignmentStrategy.LEV:
                    ipa_aligned, gold_aligned = align_with_lev(str_input, gold_ipa)
                else:
                    ipa_aligned, gold_aligned = align_pad(str_input, gold_ipa)
                X.append(self._extract_char_features(ipa_aligned))
                y.append(gold_aligned)

        self.model = sklearn_crfsuite.CRF(
            algorithm=self.algorithm,
            c1=self.c1,
            c2=self.c2,
            max_iterations=self.max_iterations,
            all_possible_transitions=self.all_possible_transitions
        )
        self.model.fit(X, y)

        if self.crf_model_path:
            self.save_model(self.crf_model_path)

    def grapheme_transforms(self, str_input: str) -> str:
        # help pronounciation with grapheme transformations
        return str_input

    def phonemize(self, word: str, lookup_word: bool = True) -> str:
        word = word.lower().strip()
        if lookup_word and word in self.GOLD:
            return self.GOLD[word]
        if not self.model:
            raise ValueError("CRF model is not trained or loaded.")
        tx_word = self.grapheme_transforms(word)
        features = self.extract_features(tx_word)
        if not features:
            return ""
        pred = self.model.predict_single(features)
        phones = ''.join(pred)
        return self._postprocess(word, phones)

    def _postprocess(self, word: str, phones: str) -> str:
        # remove artifacts from alignment
        phones = phones.replace(".", "")
        if self.manual_fixes:
            phones = self._apply_postfixes(word, phones)
        return phones

    def save_model(self, path: str):
        joblib.dump(self.model, path)

    def load_model(self, path: str):
        self.model = joblib.load(path)


if __name__ == "__main__":
    phonemizer = CRFPhonemizer(dialect=Dialects.CENTRAL)

    # Evaluate on the same data (overfitting expected due to small dataset)
    stats = phonemizer.evaluate_on_gold(limit=None, detailed=False, show_changes=False)

    # PER is computed inside evaluate_on_gold (see base.MirandesePhonemizer).
    per = stats['per']
    per_no_stress = stats['per_no_stress']

    # --- Print Summary Metrics ---
    print("\n" + "=" * 50)
    print("      Mirandese Phonemizer Rule Evaluation")
    print("=" * 50)
    print(f"Total Words Evaluated: {stats['counts']}\n")

    print("## Phoneme Error Rate (PER, Full IPA Match, includes stress)")
    print(f"PER:    {per:.2%}")

    print("\n## Phoneme Error Rate (PER, Stress-Agnostic)")
    print(f"PER:    {per_no_stress:.2%}")

    # --- Print only 'wrong' words (ED > 0) ---
    print("\n--- Incorrectly Phonemized Words (Full IPA Match ED > 0) ---")
    wrong_words = stats.get("details", [])

    if wrong_words:
        print(f"Total Incorrect: {len(wrong_words)} words\n")

        # Print a header for the detailed list
        print(f"{'Word':<20} | {'Gold':<15} | {'Phonemized':<15} | {'ED After':<8}")
        print("-" * 75)

        # Print the detailed list
        for d in wrong_words:
            print(
                f"{d['word']:<20} | {d['gold']:<15} | {d['phonemes']:<15} | {d['ed']:<8}")
    else:
        print("All words achieved an exact match (100% Accuracy)!")
