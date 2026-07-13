"""Phoneme Error Rate (PER) benchmark against the native-speaker gold.

Two systems are scored:

- **o2i base** — raw ``orthography2ipa`` lattice transcription.
- **o2i + CRF** — lattice base with the CRF correction layer.

The CRF is reported two ways:

- *fit to gold*: trained on the full gold dictionary and scored on that same
  dictionary — an upper bound, not a generalization estimate.
- *5-fold CV*: each word is scored by a CRF trained without it (5 folds),
  which estimates out-of-dictionary performance.

PER = total character edit distance / total gold length, computed on
marker-stripped IPA both with stress markers ("stressed") and without
("stress-agnostic"). Gold lookup is bypassed throughout — every score
reflects the model, never the dictionary.

Run ``python -m mwl_phonemizer.evaluate [dialect]`` to print the table.
"""

import random
from typing import Callable

import editdistance

from mwl_phonemizer import MirandesePhonemizer, strip_markers, strip_stress
from mwl_phonemizer.crf import CRFCorrector
from mwl_phonemizer.gold import GOLD


def _gold_pairs(dialect: str) -> list[tuple[str, str]]:
    return [(w, strip_markers(ipa)) for w, ipa in GOLD[dialect].items()]


def score(predict: Callable[[str], str],
          pairs: list[tuple[str, str]]) -> dict:
    """PER of ``predict`` over ``(word, gold_ipa)`` *pairs*.

    Returns ``per`` (stressed), ``per_no_stress``, ``counts`` and per-word
    ``details`` for every non-exact match.
    """
    total_ed = total_ref = 0
    total_ed_ns = total_ref_ns = 0
    details = []
    for word, gold in pairs:
        hyp = predict(word)
        ed = editdistance.eval(hyp, gold)
        total_ed += ed
        total_ref += len(gold)
        gold_ns, hyp_ns = strip_stress(gold), strip_stress(hyp)
        total_ed_ns += editdistance.eval(hyp_ns, gold_ns)
        total_ref_ns += len(gold_ns)
        if ed:
            details.append({"word": word, "gold": gold, "hyp": hyp, "ed": ed})
    return {
        "per": total_ed / total_ref if total_ref else 0.0,
        "per_no_stress": total_ed_ns / total_ref_ns if total_ref_ns else 0.0,
        "counts": len(pairs),
        "details": details,
    }


def evaluate_base(dialect: str = "mwl") -> dict:
    """PER of the raw orthography2ipa transcription on the gold."""
    pho = MirandesePhonemizer(dialect=dialect, use_crf=False)
    return score(lambda w: pho.phonemize_word(w, lookup=False),
                 _gold_pairs(dialect))


def evaluate_crf(dialect: str = "mwl") -> dict:
    """PER of o2i + CRF trained on the full gold ("fit to gold")."""
    pho = MirandesePhonemizer(dialect=dialect, use_crf=True)
    return score(lambda w: pho.phonemize_word(w, lookup=False),
                 _gold_pairs(dialect))


def cross_validate(dialect: str = "mwl", folds: int = 5, seed: int = 42) -> dict:
    """K-fold cross-validated PER of o2i + CRF.

    Every gold word is scored exactly once, by a CRF trained on the other
    folds, so the aggregate PER estimates out-of-dictionary performance.
    """
    pairs = _gold_pairs(dialect)
    rng = random.Random(seed)
    rng.shuffle(pairs)
    pho = MirandesePhonemizer(dialect=dialect, use_crf=False)
    scored: list[tuple[str, str, str]] = []  # word, gold, hyp
    for k in range(folds):
        test = pairs[k::folds]
        train = [p for i, p in enumerate(pairs) if i % folds != k]
        crf = CRFCorrector(pho.g2p).train(train)
        for word, gold in test:
            scored.append((word, gold, crf.predict(word)))
    hyp_by_word = {w: h for w, _, h in scored}
    return score(lambda w: hyp_by_word[w], [(w, g) for w, g, _ in scored])


def main(dialect: str = "mwl") -> None:
    base = evaluate_base(dialect)
    fit = evaluate_crf(dialect)
    cv = cross_validate(dialect)

    print(f"Mirandese PER benchmark — dialect {dialect!r}, "
          f"{base['counts']} gold words\n")
    print(f"{'system':<28} {'PER':>8} {'PER (no stress)':>16}")
    print("-" * 54)
    for name, s in (("o2i base", base),
                    ("o2i + CRF (fit to gold)", fit),
                    ("o2i + CRF (5-fold CV)", cv)):
        print(f"{name:<28} {s['per']:>7.2%} {s['per_no_stress']:>15.2%}")

    print(f"\no2i base mismatches: {len(base['details'])}, "
          f"CRF fit-to-gold mismatches: {len(fit['details'])}, "
          f"CRF 5-fold-CV mismatches: {len(cv['details'])}")


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "mwl")
