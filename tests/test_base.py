"""Unit tests for the shared phonemizer base helpers."""
from mwl_phonemizer.base import Dialects, MirandesePhonemizer


def test_strip_markers():
    assert MirandesePhonemizer.strip_markers("ˈe(j).ʒɛmˈplu") == "ˈejʒɛmˈplu"
    assert MirandesePhonemizer.strip_markers("a.b.c") == "abc"


def test_strip_stress():
    assert MirandesePhonemizer.strip_stress("miɾɐ̃ˈdes̺") == "miɾɐ̃des̺"
    assert MirandesePhonemizer.strip_stress("ˈaˌb") == "ab"


def test_word_edit_distance():
    assert MirandesePhonemizer.word_edit_distance("abc", "abc") == 0
    assert MirandesePhonemizer.word_edit_distance("abc", "abd") == 1


def test_dialects_enum():
    assert Dialects.CENTRAL == "central"
    assert Dialects.RAIANO == "raiano"
    assert Dialects.SENDINESE == "sendinese"


def test_base_loads_gold_dicts():
    pho = MirandesePhonemizer()
    assert pho.GOLD
    assert pho.RAIANO_GOLD is not None
    assert pho.SENDINESE_GOLD is not None
    # markers are stripped on load
    assert all("." not in v and "(" not in v for v in pho.GOLD.values())


def test_phonemize_sentence_preserves_punctuation():
    pho = MirandesePhonemizer()
    # any word known in the gold dict round-trips with punctuation kept
    word = next(iter(pho.GOLD))
    out = pho.phonemize_sentence(f"{word}, {word}!")
    assert "," in out and "!" in out
