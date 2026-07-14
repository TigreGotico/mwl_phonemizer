"""Tests for the public MirandesePhonemizer API."""
import pytest


from mwl_phonemizer import (DIALECTS, MirandesePhonemizer, phonemize,
                            strip_markers, strip_stress)
from mwl_phonemizer.gold import CENTRAL, GOLD, RAIANO, SENDINESE


@pytest.fixture(scope="module")
def pho():
    return MirandesePhonemizer(dialect="mwl")


def test_strip_markers():
    assert strip_markers("ˈe(j).ʒɛmˈplu") == "ˈejʒɛmˈplu"
    assert strip_markers("a.b.c") == "abc"


def test_strip_stress():
    assert strip_stress("miɾɐ̃ˈdes̺") == "miɾɐ̃des̺"
    assert strip_stress("ˈaˌb") == "ab"


def test_gold_dicts():
    assert len(CENTRAL) >= 200
    assert SENDINESE and RAIANO
    assert set(GOLD) == set(DIALECTS)
    # sendim gold layers its overrides on top of the base entries
    assert GOLD["mwl-x-sendim"]["fuogo"] == SENDINESE["fuogo"]
    assert GOLD["mwl-x-sendim"]["abandono"] == CENTRAL["abandono"]


def test_unknown_dialect_raises():
    with pytest.raises(ValueError):
        MirandesePhonemizer(dialect="mwl-x-nope")


def test_gold_lookup(pho):
    # gold entries are returned verbatim (markers stripped)
    assert pho.phonemize("lhéngua") == strip_markers(CENTRAL["lhéngua"])
    assert pho.phonemize_word("Lhéngua") == strip_markers(CENTRAL["lhéngua"])


def test_multiword_gold_lookup(pho):
    assert pho.phonemize("tierra de miranda") == strip_markers(
        CENTRAL["tierra de miranda"])


def test_oov_word_is_transcribed(pho):
    ipa = pho.phonemize_word("zzzabcde", lookup=False)
    assert isinstance(ipa, str)
    out = pho.phonemize("amportante", lookup=False)
    assert out and "ɐ̃" in out


def test_sentence_preserves_punctuation(pho):
    out = pho.phonemize("lhéngua, mirandés!")
    assert "," in out and "!" in out
    assert strip_markers(CENTRAL["lhéngua"]) in out


def test_no_crf_falls_back_to_o2i_base():
    base = MirandesePhonemizer(dialect="mwl", use_crf=False)
    assert base.crf is None
    assert base.phonemize_word("amportante", lookup=False) == "ɐ̃puˈɾtɐ̃tɨ"
    assert base.phonemize_word("fui", lookup=False) == "ˈfuj"


def test_g2p_engine_surface(pho):
    # An engine built ON orthography2ipa, not a plugin TO it — nothing there
    # discovers or calls this. The surface is what matters, not inheritance.
    for method in ("transcribe", "transcribe_word"):
        assert callable(getattr(pho, method))
    assert pho.language_codes == ["mwl"]
    word = "lhéngua"
    assert pho.transcribe(word) == pho.phonemize(word)
    assert pho.transcribe_word(word) == pho.phonemize_word(word)


def test_dialect_language_codes():
    sendim = MirandesePhonemizer(dialect="mwl-x-sendim", use_crf=False)
    assert sendim.language_codes == ["mwl", "mwl-x-sendim"]
    assert sendim.phonemize("fuogo") == strip_markers(SENDINESE["fuogo"])


def test_module_level_phonemize():
    assert phonemize("lhéngua") == strip_markers(CENTRAL["lhéngua"])
    # cached default instance is reused
    from mwl_phonemizer import _default_phonemizer
    assert _default_phonemizer("mwl") is _default_phonemizer("mwl")


def test_crf_model_roundtrip(tmp_path, pho):
    path = str(tmp_path / "mwl.crf")
    pho.crf.save(path)
    loaded = MirandesePhonemizer(dialect="mwl", crf_model_path=path)
    for word in ("amportante", "lhéngua", "zeimosa"):
        assert (loaded.phonemize_word(word, lookup=False)
                == pho.phonemize_word(word, lookup=False))
