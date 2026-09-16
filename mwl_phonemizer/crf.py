"""CRF correction layer over the ``orthography2ipa`` Mirandese lattice.

The corrector is a linear-chain CRF (``sklearn_crfsuite``) whose feature
sequence is the per-grapheme feature export from ``G2P(spec).features(word)``
— phonological-class predicates, word-local grapheme neighbours, the ranked
candidate lattice's top-1/cost, per-word confidence — one dict per grapheme.
Gold IPA labels are aligned to that grapheme tokenization by
:func:`align_gold_to_graphemes`, so labels line up 1:1 with the features.

Two design choices keep the model from overfitting the small gold dictionary:

- **Copy sentinel** — a grapheme whose gold IPA equals the lattice's top-1
  guess is labelled ``"="`` (copy). Most graphemes are already correct, so
  the label space collapses and unseen contexts default to trusting the
  lattice instead of hallucinating a segment.
- **Stress is delegated** — the CRF is trained on stress-stripped IPA and
  only corrects segments; the stress mark is applied afterwards with the
  spec's own ``StressRules`` (the same machinery ``G2P.transcribe_word``
  uses), so stress placement never depends on the tiny training set.
"""

import joblib
import sklearn_crfsuite
from rapidfuzz.distance import Levenshtein

from orthography2ipa import G2P
from orthography2ipa.stress import apply_stress_mark, detect_stress

#: CRF label meaning "emit this grapheme's lattice top-1 IPA unchanged"
COPY = "="


def strip_stress(ipa: str) -> str:
    """Drop primary/secondary stress markers."""
    return ipa.replace("ˈ", "").replace("ˌ", "")


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


class CRFCorrector:
    """Word-level IPA corrector trained on o2i features + gold IPA labels.

    ``predict(word)`` returns the full corrected IPA for *word*: the CRF emits
    one label per o2i grapheme — the :data:`COPY` sentinel (keep the lattice
    top-1) or a replacement IPA string (possibly empty, possibly
    multi-character) — the labels are concatenated and the spec's stress rules
    place the stress mark.
    """

    def __init__(self, g2p: G2P,
                 algorithm: str = "lbfgs",
                 c1: float = 0.1,
                 c2: float = 0.1,
                 max_iterations: int = 100,
                 all_possible_transitions: bool = False):
        self.g2p = g2p
        self.algorithm = algorithm
        self.c1 = c1
        self.c2 = c2
        self.max_iterations = max_iterations
        self.all_possible_transitions = all_possible_transitions
        self.model: sklearn_crfsuite.CRF | None = None

    def features(self, word: str) -> tuple[list[dict], list[str]]:
        """Per-grapheme o2i feature dicts + top-1 IPA guesses for *word*.

        Returns ``(features, top1)`` where ``features`` is the CRF feature
        sequence (one flat, scalar, ``None``-free dict per grapheme) and
        ``top1`` is the parallel list of per-grapheme top-1 IPA guesses used
        for gold-label alignment.
        """
        features: list[dict] = []
        top1: list[str] = []
        for wf in self.g2p.features(word):
            for d in wf.as_dicts():
                top1.append(d.get("top1_ipa") or "")
                # crfsuite feature values must be str/bool/int/float, not None
                features.append({k: ("" if v is None else v)
                                 for k, v in d.items()})
        return features, top1

    def train(self, pairs: list[tuple[str, str]]) -> "CRFCorrector":
        """Fit the CRF on ``(word, gold_ipa)`` pairs and return ``self``."""
        X, y = [], []
        for word, gold_ipa in pairs:
            feats, top1 = self.features(word)
            if not feats:
                continue
            labels = align_gold_to_graphemes(top1, strip_stress(gold_ipa))
            X.append(feats)
            y.append([COPY if lbl == t else lbl
                      for lbl, t in zip(labels, top1)])
        self.model = sklearn_crfsuite.CRF(
            algorithm=self.algorithm,
            c1=self.c1,
            c2=self.c2,
            max_iterations=self.max_iterations,
            all_possible_transitions=self.all_possible_transitions,
        )
        self.model.fit(X, y)
        return self

    def predict(self, word: str) -> str:
        """Corrected IPA for *word* (empty string if it has no graphemes)."""
        if self.model is None:
            raise ValueError("CRF model is not trained or loaded")
        feats, top1 = self.features(word)
        if not feats:
            return ""
        labels = self.model.predict_single(feats)
        ipa = "".join(t if lbl == COPY else lbl
                      for lbl, t in zip(labels, top1))
        return self._apply_stress(word, ipa)

    def _apply_stress(self, word: str, ipa: str) -> str:
        """Place the stress mark with the spec's own ``StressRules``."""
        rules = self.g2p.spec.stress
        if rules is None or not ipa:
            return ipa
        try:
            idx = detect_stress(word, rules, lang=self.g2p.lang)
            return apply_stress_mark(ipa, rules, idx)
        except Exception:
            return ipa

    def save(self, path: str) -> None:
        joblib.dump(self.model, path)

    def load(self, path: str) -> "CRFCorrector":
        self.model = joblib.load(path)
        return self
