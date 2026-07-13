"""Unit tests for the o2i grapheme-based CRF feature/label alignment.

The CRF backend trains on ``orthography2ipa``'s per-grapheme feature export
(``G2P(spec).features(word)``). For that to work, the gold IPA labels must be
distributed over the o2i grapheme tokens 1:1 — that is what
:func:`align_gold_to_graphemes` does. These tests pin the alignment invariants
that keep features and labels the same length per word.
"""
from orthography2ipa import G2P

from mwl_phonemizer.crf_mwl import (
    CRFPhonemizer,
    align_gold_to_graphemes,
)


class TestAlignGoldToGraphemes:
    def test_labels_are_one_per_grapheme(self):
        top1 = ["ʎ", "ɛ", "ŋ", "ɡ", "ɐ"]
        labels = align_gold_to_graphemes(top1, "ʎɛ̃ɡwɐ")
        assert len(labels) == len(top1)

    def test_labels_concatenate_back_to_gold(self):
        # every gold character must be attributed to exactly one grapheme
        top1 = ["t", "jɛ", "r", "ɐ"]
        gold = "tjɛrɐ"
        labels = align_gold_to_graphemes(top1, gold)
        assert "".join(labels) == gold

    def test_multichar_grapheme_label(self):
        # a digraph grapheme can carry a multi-character IPA label
        top1 = ["b", "wo", "n", "u"]
        labels = align_gold_to_graphemes(top1, "bwonu")
        assert "".join(labels) == "bwonu"
        assert len(labels) == 4

    def test_empty_grapheme_sequence(self):
        assert align_gold_to_graphemes([], "abc") == []

    def test_no_ipa_guess_falls_back_to_first_slot(self):
        # graphemes with no top-1 guess still get a valid (recoverable) label
        labels = align_gold_to_graphemes(["", ""], "xy")
        assert "".join(labels) == "xy"
        assert len(labels) == 2


class TestFeatureLabelLengthMatch:
    """Features and labels must be the same length for every gold word."""

    def test_feature_and_label_lengths_match_on_gold(self):
        phon = CRFPhonemizer()
        g2p = G2P("mwl")
        for word, gold in list(phon.GOLD.items()):
            feats, top1 = phon._grapheme_records(word)
            if not feats:
                continue
            labels = align_gold_to_graphemes(
                top1, phon.strip_stress(phon.strip_markers(gold)))
            assert len(feats) == len(labels) == len(top1), word

    def test_grapheme_features_are_scalar_and_not_none(self):
        # crfsuite rejects None-valued features
        phon = CRFPhonemizer()
        feats, _ = phon._grapheme_records("lhéngua")
        assert feats
        for d in feats:
            for v in d.values():
                assert v is not None
                assert isinstance(v, (str, bool, int, float))
