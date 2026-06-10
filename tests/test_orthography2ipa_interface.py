"""Tests for the orthography2ipa interface conformance and differential audit.

Validates:
- MirandesePhonemizer (and all backends) implement G2PPlugin
- transcribe() == phonemize_sentence(), transcribe_word() == phonemize()
- language_codes per dialect
- differential audit: g2p.json grapheme candidates vs orthography2ipa mwl spec
  (informational gate — agree >= differ; known divergences: j ʒ-vs-ʝ, ç s̻-vs-t͡s)
"""
import json
import os

import pytest

import orthography2ipa
from orthography2ipa.g2p_plugin import G2PPlugin, WordContext

from mwl_phonemizer.base import Dialects, MirandesePhonemizer, spec_for, DIALECT_TO_SPEC_CODE
from mwl_phonemizer.orthography_hand_rules import OrthographyRulesMWL
from mwl_phonemizer.char_lookup_mwl import LookupTableMWL
from mwl_phonemizer.ngram_mwl import NgramMWLPhonemizer
from mwl_phonemizer.crf_mwl import CRFPhonemizer
from mwl_phonemizer.crf_ortho_mwl import CRFOrthoCorrector


# ---------------------------------------------------------------------------
# Interface conformance
# ---------------------------------------------------------------------------

class TestInterface:
    """All concrete backends must implement the shared G2PPlugin base."""

    @pytest.fixture(params=[
        "rules",
        "lookup",
        "ngram",
        "crf",
        "crf_ortho",
    ])
    def plugin(self, request):
        mapping = {
            "rules": OrthographyRulesMWL,
            "lookup": LookupTableMWL,
            "ngram": NgramMWLPhonemizer,
            "crf": CRFPhonemizer,
            "crf_ortho": CRFOrthoCorrector,
        }
        return mapping[request.param]()

    def test_implements_g2p_plugin(self, plugin):
        assert isinstance(plugin, G2PPlugin)

    def test_language_codes_contains_mwl(self, plugin):
        assert "mwl" in plugin.language_codes

    def test_transcribe_equals_phonemize_sentence(self, plugin):
        text = "mui bien"
        assert plugin.transcribe(text) == plugin.phonemize_sentence(text)

    def test_transcribe_word_equals_phonemize(self, plugin):
        word = "bien"
        assert plugin.transcribe_word(word) == plugin.phonemize(word)

    def test_transcribe_word_accepts_context(self, plugin):
        ctx = WordContext(prev_word="mui", next_word=None)
        result = plugin.transcribe_word("bien", context=ctx)
        assert isinstance(result, str)


class TestLanguageCodes:
    def test_central_dialect_codes(self):
        p = OrthographyRulesMWL(dialect=Dialects.CENTRAL)
        assert p.language_codes == ["mwl"]

    def test_raiano_dialect_codes(self):
        p = OrthographyRulesMWL(dialect=Dialects.RAIANO)
        # RAIANO has no dedicated spec yet; maps to base mwl
        assert p.language_codes == ["mwl"]

    def test_sendinese_dialect_codes(self):
        p = OrthographyRulesMWL(dialect=Dialects.SENDINESE)
        assert "mwl" in p.language_codes
        assert "mwl-x-sendim" in p.language_codes


# ---------------------------------------------------------------------------
# Dialect ↔ spec helper
# ---------------------------------------------------------------------------

class TestSpecFor:
    def test_central_returns_mwl_spec(self):
        spec = spec_for(Dialects.CENTRAL)
        assert spec.code == "mwl"

    def test_sendinese_returns_sendim_spec(self):
        spec = spec_for(Dialects.SENDINESE)
        assert spec.code == "mwl-x-sendim"

    def test_raiano_returns_mwl_spec(self):
        spec = spec_for(Dialects.RAIANO)
        assert spec.code == "mwl"

    def test_dialect_to_spec_code_complete(self):
        for d in Dialects:
            assert d in DIALECT_TO_SPEC_CODE, f"Dialect {d} missing from DIALECT_TO_SPEC_CODE"


# ---------------------------------------------------------------------------
# Differential audit
# ---------------------------------------------------------------------------

class TestDifferentialGraphemes:
    """Audit g2p.json grapheme candidates against the orthography2ipa mwl spec.

    Informational gate: the local g2p.json table stays authoritative;
    this test pins the agreement level so drift on either side is visible.

    Known divergences being adjudicated upstream (Phase M0):
      - j:  g2p.json has ʒ,  spec has ʝ
      - ç:  g2p.json has z̻,  spec has t͡s (Mirandese affricate vs. fricative)
    These are expected and do NOT cause a test failure as long as agree >= differ.
    """

    def test_graphemes_agree_with_spec(self, capsys):
        g2p_path = os.path.join(os.path.dirname(__file__), "..", "mwl_phonemizer", "g2p.json")
        with open(g2p_path, encoding="utf-8") as f:
            g2p = json.load(f)

        spec = orthography2ipa.get("mwl")
        agree, differ = [], []

        for grapheme, candidates in g2p.items():
            spec_candidates = spec.graphemes.get(grapheme)
            if spec_candidates is None:
                continue  # multi-char or word-specific entry not in spec — skip
            # agree if at least one candidate appears in the spec set
            shared = [c for c in candidates if c in spec_candidates]
            if shared:
                agree.append((grapheme, candidates, spec_candidates))
            else:
                differ.append((grapheme, candidates, spec_candidates))

        with capsys.disabled():
            print(f"\n[differential audit] agree={len(agree)}  differ={len(differ)}")
            if differ:
                print("Divergences (g2p.json vs spec):")
                for g, local, remote in differ:
                    print(f"  {g!r:12s}  local={local}  spec={remote}")

        assert len(agree) >= len(differ), (
            f"g2p.json and the mwl spec diverged too much: "
            f"agree={len(agree)}, differ={len(differ)}\n"
            f"Divergences: {[(g, l, r) for g, l, r in differ]}"
        )
