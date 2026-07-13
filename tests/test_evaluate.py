"""Tests for the PER benchmark, including regression bounds.

The bounds are upper limits on the measured PER: a system that improves keeps
passing, a regression fails CI. Tighten them when an improvement lands.
"""
import pytest

from mwl_phonemizer.evaluate import (cross_validate, evaluate_base,
                                     evaluate_crf, score)


@pytest.fixture(scope="module")
def base():
    return evaluate_base("mwl")


@pytest.fixture(scope="module")
def fit():
    return evaluate_crf("mwl")


@pytest.fixture(scope="module")
def cv():
    return cross_validate("mwl")


def test_score_exact_match():
    s = score(lambda w: {"a": "ˈab"}[w], [("a", "ˈab")])
    assert s["per"] == 0.0
    assert s["per_no_stress"] == 0.0
    assert s["details"] == []


def test_score_counts_edits():
    s = score(lambda w: "ˈax", [("a", "ˈab")])
    assert s["per"] == pytest.approx(1 / 3)
    assert s["per_no_stress"] == pytest.approx(1 / 2)
    assert s["details"][0]["ed"] == 1


def test_all_gold_words_scored(base, fit, cv):
    assert base["counts"] == fit["counts"] == cv["counts"] >= 200


# regression bounds: (max PER, max stress-agnostic PER), measured values
# 22.33%/19.60% (base), 6.99%/1.92% (fit), 21.49%/18.79% (5-fold CV)
def test_base_per_bounds(base):
    assert base["per"] <= 0.25
    assert base["per_no_stress"] <= 0.22


def test_crf_fit_per_bounds(fit):
    assert fit["per"] <= 0.10
    assert fit["per_no_stress"] <= 0.04


def test_crf_cv_per_bounds(cv):
    assert cv["per"] <= 0.24
    assert cv["per_no_stress"] <= 0.21


def test_crf_improves_over_base(base, fit, cv):
    assert fit["per"] < base["per"]
    assert fit["per_no_stress"] < base["per_no_stress"]
    assert cv["per"] <= base["per"]
    assert cv["per_no_stress"] <= base["per_no_stress"]
