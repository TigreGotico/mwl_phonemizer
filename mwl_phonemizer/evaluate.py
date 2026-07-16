"""Phoneme Error Rate (PER) benchmarks for the Mirandese phonemizer.

Two independent gold sets are scored:

- **Sentence gold** (primary) — the research-grounded, blind-judge-verified
  20-sentence sets ``orthography2ipa`` ships for ``mwl``, ``mwl-x-sendim`` and
  ``mwl-x-ifanes`` (``data/gold/portuguese_tts/``). This is held out from
  everything the library trains on, so it measures the deployed default
  honestly. The sandhi-aware lattice reproduces it essentially exactly.
- **Word dictionary** (secondary) — the ~200-word native-speaker dictionary
  bundled in :mod:`mwl_phonemizer.gold` (Hugging Face ``mirandese_g2p``). It
  uses a finer, different transcription convention; the optional CRF is trained
  and scored on it.

PER = total character edit distance / total gold length on marker-stripped IPA,
reported with stress marks ("PER") and without ("PER no-stress"). Gold lookup is
bypassed throughout, so every score reflects the model, never the dictionary.

Run ``python -m mwl_phonemizer.evaluate [dialect]`` to print the tables.
"""

import csv
import os
import random
from typing import Callable

import editdistance
import orthography2ipa

from mwl_phonemizer import MirandesePhonemizer, strip_markers, strip_stress
from mwl_phonemizer.crf import CRFCorrector
from mwl_phonemizer.gold import GOLD

_GOLD_DIR = os.path.join(os.path.dirname(orthography2ipa.__file__),
                         "data", "gold", "portuguese_tts")


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

#: orthographic punctuation the phonemizer preserves in output but the gold IPA
#: omits — dropped on both sides so PER reflects phonology, not punctuation.
_PUNCT = ".,;:!?¿¡\"'’“”()[]—–-"


def _collapse(ipa: str) -> str:
    """Marker- and punctuation-stripped, whitespace-free IPA for scoring."""
    ipa = strip_markers(ipa).replace(" ", "")
    return "".join(c for c in ipa if c not in _PUNCT)


def score(predict: Callable[[str], str],
          pairs: list[tuple[str, str]]) -> dict:
    """PER of ``predict`` over ``(text, gold_ipa)`` *pairs*.

    Returns ``per`` (stressed), ``per_no_stress``, ``counts`` and per-item
    ``details`` for every non-exact match.
    """
    total_ed = total_ref = 0
    total_ed_ns = total_ref_ns = 0
    details = []
    for text, gold in pairs:
        gold_c, hyp_c = _collapse(gold), _collapse(predict(text))
        ed = editdistance.eval(hyp_c, gold_c)
        total_ed += ed
        total_ref += len(gold_c)
        gold_ns, hyp_ns = strip_stress(gold_c), strip_stress(hyp_c)
        total_ed_ns += editdistance.eval(hyp_ns, gold_ns)
        total_ref_ns += len(gold_ns)
        if ed:
            details.append({"text": text, "gold": gold_c, "hyp": hyp_c, "ed": ed})
    return {
        "per": total_ed / total_ref if total_ref else 0.0,
        "per_no_stress": total_ed_ns / total_ref_ns if total_ref_ns else 0.0,
        "counts": len(pairs),
        "details": details,
    }


# ---------------------------------------------------------------------------
# Sentence gold (primary)
# ---------------------------------------------------------------------------

def load_sentence_gold(dialect: str = "mwl") -> list[tuple[str, str]]:
    """``(sentence, gold_ipa)`` pairs from the ``orthography2ipa`` gold TSV.

    Raises :class:`FileNotFoundError` if the installed ``orthography2ipa`` does
    not ship the Mirandese gold for *dialect*.
    """
    path = os.path.join(_GOLD_DIR, f"{dialect}.tsv")
    with open(path, encoding="utf-8") as f:
        return [(row["sentence"], row["ipa"])
                for row in csv.DictReader(f, delimiter="\t")]


def evaluate_sentences(dialect: str = "mwl") -> dict:
    """PER of the deployed default (pure lattice) on the sentence gold."""
    pho = MirandesePhonemizer(dialect=dialect)
    return score(pho.phonemize, load_sentence_gold(dialect))


# ---------------------------------------------------------------------------
# Word dictionary (secondary)
# ---------------------------------------------------------------------------

def _word_pairs(dialect: str) -> list[tuple[str, str]]:
    return [(w, strip_markers(ipa)) for w, ipa in GOLD[dialect].items()]


def evaluate_base(dialect: str = "mwl") -> dict:
    """PER of the raw lattice on the word dictionary."""
    pho = MirandesePhonemizer(dialect=dialect, use_crf=False)
    return score(lambda w: pho.phonemize_word(w), _word_pairs(dialect))


def evaluate_crf(dialect: str = "mwl") -> dict:
    """PER of lattice + CRF trained on the full word dictionary ("fit")."""
    pho = MirandesePhonemizer(dialect=dialect, use_crf=True)
    return score(lambda w: pho.phonemize_word(w), _word_pairs(dialect))


def cross_validate(dialect: str = "mwl", folds: int = 5, seed: int = 42) -> dict:
    """K-fold cross-validated PER of lattice + CRF on the word dictionary.

    Every word is scored by a CRF trained without it, so the aggregate PER
    estimates out-of-dictionary performance.
    """
    pairs = _word_pairs(dialect)
    rng = random.Random(seed)
    rng.shuffle(pairs)
    pho = MirandesePhonemizer(dialect=dialect, use_crf=False)
    hyp_by_word: dict[str, str] = {}
    for k in range(folds):
        test = pairs[k::folds]
        train = [p for i, p in enumerate(pairs) if i % folds != k]
        crf = CRFCorrector(pho.g2p).train(train)
        for word, _ in test:
            hyp_by_word[word] = crf.predict(word)
    return score(lambda w: hyp_by_word[w], pairs)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _row(name: str, s: dict) -> None:
    print(f"{name:<32} {s['per']:>7.2%} {s['per_no_stress']:>15.2%}")


def main(dialect: str = "mwl") -> None:
    try:
        sent = evaluate_sentences(dialect)
        print(f"Sentence gold — dialect {dialect!r}, {sent['counts']} sentences\n")
        print(f"{'system':<32} {'PER':>7} {'PER (no stress)':>15}")
        print("-" * 56)
        _row("lattice (deployed default)", sent)
        print(f"\nsentence mismatches: {len(sent['details'])}\n")
    except FileNotFoundError:
        print(f"(installed orthography2ipa ships no sentence gold for {dialect!r})\n")

    base = evaluate_base(dialect)
    print(f"Word dictionary — dialect {dialect!r}, {base['counts']} words\n")
    print(f"{'system':<32} {'PER':>7} {'PER (no stress)':>15}")
    print("-" * 56)
    _row("lattice", base)
    _row("+ CRF (fit to dictionary)", evaluate_crf(dialect))
    _row("+ CRF (5-fold CV)", cross_validate(dialect))


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "mwl")
