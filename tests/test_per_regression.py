"""Regression guard on the in-repo Phoneme Error Rate (PER) benchmark.

Each backend is scored against the bundled Mirandese gold dictionary. The
thresholds below are upper bounds on the measured PER: a backend that gets
*better* keeps passing, while a regression (higher PER) fails CI. Tighten the
bounds when an improvement lands.

The espeak/epitran backends depend on optional system tools / packages and are
skipped when unavailable.
"""
import shutil

import pytest

from mwl_phonemizer.char_lookup_mwl import LookupTableMWL
from mwl_phonemizer.ngram_mwl import NgramMWLPhonemizer
from mwl_phonemizer.orthography_hand_rules import OrthographyRulesMWL
from mwl_phonemizer.crf_mwl import CRFPhonemizer
from mwl_phonemizer.crf_ortho_mwl import CRFOrthoCorrector

# backend -> (max PER full-IPA, max PER stress-agnostic)
GOLD_PER_BOUNDS = {
    "lookup": (0.46, 0.39),
    "ngram": (0.45, 0.32),
    "rules": (0.37, 0.29),
    "crf": (0.22, 0.10),
    "crf_ortho": (0.16, 0.04),
}

BACKENDS = {
    "lookup": LookupTableMWL,
    "ngram": lambda: NgramMWLPhonemizer(n=4),
    "rules": OrthographyRulesMWL,
    "crf": CRFPhonemizer,
    "crf_ortho": CRFOrthoCorrector,
}


@pytest.mark.parametrize("name", sorted(GOLD_PER_BOUNDS))
def test_per_does_not_regress(name):
    max_per, max_per_no_stress = GOLD_PER_BOUNDS[name]
    stats = BACKENDS[name]().evaluate_on_gold()
    assert stats["per"] <= max_per, (
        f"{name}: PER {stats['per']:.4f} regressed above bound {max_per}")
    assert stats["per_no_stress"] <= max_per_no_stress, (
        f"{name}: stress-agnostic PER {stats['per_no_stress']:.4f} "
        f"regressed above bound {max_per_no_stress}")


@pytest.mark.skipif(shutil.which("espeak-ng") is None,
                    reason="espeak-ng not installed")
def test_espeak_correction_improves_per():
    from mwl_phonemizer.espeak_mwl import EspeakMWL
    stats = EspeakMWL().evaluate_against_base()
    # the correction rules must not make espeak output worse
    assert stats["per_after"] <= stats["per_before"]
