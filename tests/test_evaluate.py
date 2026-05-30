"""Tests for the shared evaluate_on_gold / PER computation."""
import pytest

from mwl_phonemizer.char_lookup_mwl import LookupTableMWL


@pytest.fixture(scope="module")
def stats():
    return LookupTableMWL().evaluate_on_gold()


def test_evaluate_returns_per_keys(stats):
    for key in ("per", "per_no_stress", "avg_edit_distance",
                "avg_edit_distance_no_stress", "counts"):
        assert key in stats


def test_per_is_a_rate(stats):
    assert 0.0 <= stats["per"] <= 1.5
    assert 0.0 <= stats["per_no_stress"] <= 1.5
    # stress-agnostic error is never larger than the full-IPA error here
    assert stats["per_no_stress"] <= stats["per"]


def test_per_matches_manual_computation(stats):
    pho = LookupTableMWL()
    total_ref_len = sum(len(v) for v in pho.GOLD.values())
    manual = stats["avg_edit_distance"] * stats["counts"] / total_ref_len
    assert stats["per"] == pytest.approx(manual)


def test_limit_restricts_corpus():
    s = LookupTableMWL().evaluate_on_gold(limit=10)
    assert s["counts"] == 10
