"""Tests for the CRF corrector and gold-to-grapheme alignment."""
import pytest

from orthography2ipa import G2P

from mwl_phonemizer import strip_markers
from mwl_phonemizer.crf import (COPY, CRFCorrector, align_gold_to_graphemes,
                                strip_stress)
from mwl_phonemizer.gold import CENTRAL


@pytest.fixture(scope="module")
def g2p():
    return G2P("mwl")


@pytest.fixture(scope="module")
def corrector(g2p):
    pairs = [(w, strip_markers(ipa)) for w, ipa in CENTRAL.items()]
    return CRFCorrector(g2p).train(pairs)


class TestAlignment:
    def test_empty_grapheme_sequence(self):
        assert align_gold_to_graphemes([], "abc") == []

    def test_no_predictions_dumps_gold_on_first_slot(self):
        assert align_gold_to_graphemes(["", ""], "ab") == ["ab", ""]

    def test_identity(self):
        assert align_gold_to_graphemes(["a", "b", "c"], "abc") == ["a", "b", "c"]

    def test_replacement(self):
        assert align_gold_to_graphemes(["a", "b"], "ax") == ["a", "x"]

    def test_insertion_attaches_to_previous(self):
        assert align_gold_to_graphemes(["a", "b"], "axb") == ["ax", "b"]

    def test_deletion_gives_empty_label(self):
        assert align_gold_to_graphemes(["a", "b", "c"], "ac") == ["a", "", "c"]

    def test_labels_concatenate_to_gold(self, g2p, corrector):
        for word, gold in CENTRAL.items():
            gold = strip_stress(strip_markers(gold))
            _, top1 = corrector.features(word)
            if not top1:
                continue
            labels = align_gold_to_graphemes(top1, gold)
            assert "".join(labels) == gold, word


class TestCorrector:
    def test_features_are_scalar_and_not_none(self, corrector):
        feats, top1 = corrector.features("lhéngua")
        assert feats and len(feats) == len(top1)
        for d in feats:
            for v in d.values():
                assert v is not None
                assert isinstance(v, (str, bool, int, float))

    def test_copy_sentinel_in_label_space(self, corrector):
        assert COPY in corrector.model.classes_

    def test_predict_before_train_raises(self, g2p):
        with pytest.raises(ValueError):
            CRFCorrector(g2p).predict("lhéngua")

    def test_predict_empty_word(self, corrector):
        assert corrector.predict("") == ""

    def test_predict_returns_stressed_ipa(self, corrector):
        ipa = corrector.predict("amportante")
        assert ipa and "ˈ" in ipa

    def test_save_load_roundtrip(self, g2p, corrector, tmp_path):
        path = str(tmp_path / "model.crf")
        corrector.save(path)
        loaded = CRFCorrector(g2p).load(path)
        for word in ("amportante", "lhéngua", "fui"):
            assert loaded.predict(word) == corrector.predict(word)
