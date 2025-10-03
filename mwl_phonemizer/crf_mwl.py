import random

from mwl_phonemizer.base import MirandesePhonemizer, Dialects
import sklearn_crfsuite
import Levenshtein as lev
from enum import Enum
import joblib


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

    ops = lev.editops(es, gd)
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


class CRFPhonemizer(MirandesePhonemizer):
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
        if crf_model_path and os.path.exists(crf_model_path):
            self.load_model(crf_model_path)
        elif train_data:
            self.train_crf(train_data)
        else:
            self.train_on_gold()

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
        # Simple character-level features for CRF
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
            if self.strategy == AlignmentStrategy.LEV:
                ipa_aligned, gold_aligned = align_with_lev(str_input, gold_ipa)
            else:
                ipa_aligned, gold_aligned = align_pad(str_input, gold_ipa)
            X.append(self.extract_features(ipa_aligned))
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

    # --- Compute PER (Phoneme Error Rate) ---  # TODO - move this to evaluate_on_gold
    total_ref_len_stress = sum(len(v) for v in phonemizer.GOLD.values())
    total_ref_len_no_stress = sum(len(phonemizer.strip_stress(v)) for v in phonemizer.GOLD.values())

    per = stats['avg_edit_distance'] * stats['counts'] / total_ref_len_stress

    per_no_stress = stats['avg_edit_distance_no_stress'] * stats['counts'] / total_ref_len_no_stress

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