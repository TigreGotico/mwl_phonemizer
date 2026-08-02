"""Tests for mwl_phonemizer.number_utils — Mirandese number verbalization.

Expected forms are cited to Leite de Vasconcelos, *Estudos de Philologia
Mirandesa* vol. I, §189 (cardinals, pp. 347-351) and §190 (ordinals) where
attested; forms marked DERIVED in the module follow the periphrastic
``cardinal + -cientos`` rule Vasconcelos states for 600-900 (p. 349).
"""
import pytest

from mwl_phonemizer import MirandesePhonemizer
from mwl_phonemizer.number_utils import (
    MirandeseNumberParser, normalize_numbers, ATTESTED, DERIVED, DIALECTS,
)


@pytest.fixture(scope="module")
def parser():
    return MirandeseNumberParser("mwl")


class TestCardinalsAttested:
    """Cardinals spelled verbatim in Vasconcelos §189."""

    @pytest.mark.parametrize("n,expected", [
        (1, "un"), (2, "dous"), (3, "trés"), (4, "quatro"), (5, "cinco"),
        (6, "seis"), (7, "siête"), (8, "oito"), (9, "nuobe"), (10, "diêç"),
        (11, "ounze"), (12, "doze"), (13, "treze"), (14, "quatorze"),
        (15, "quinze"), (16, "dezaseis"), (17, "dezasiete"), (18, "dezuito"),
        (19, "dezanobe"), (20, "binte"), (30, "trinta"), (40, "quarenta"),
        (50, "cincoenta"), (60, "sessenta"), (70, "setenta"), (80, "uitenta"),
        (90, "nobenta"), (100, "cien"), (200, "duzentos"), (300, "trezentos"),
        (400, "quatrocientos"), (500, "cincocientos"), (1000, "mil"),
    ])
    def test_base(self, parser, n, expected):
        assert parser.cardinal(n) == expected


class TestCardinalsGender:
    def test_one_masc_fem(self, parser):
        assert parser.cardinal(1, "masculine") == "un"
        assert parser.cardinal(1, "feminine") == "ũa"

    def test_two_masc_fem(self, parser):
        # dous / dues — Vasconcelos §189, Obs. 3, p.351
        assert parser.cardinal(2, "masculine") == "dous"
        assert parser.cardinal(2, "feminine") == "dues"


class TestCompoundComposition:
    """Compound spellings composed from attested atoms with copulative *i*."""

    @pytest.mark.parametrize("n,expected", [
        (21, "binte i un"),
        (42, "quarenta i dous"),
        (101, "cien i un"),
        (105, "cien i cinco"),
        (256, "duzentos i cincoenta i seis"),
        (999, "nuobecientos i nobenta i nuobe"),
        (2025, "dous mil i binte i cinco"),
    ])
    def test_compound(self, parser, n, expected):
        assert parser.cardinal(n) == expected

    def test_million(self, parser):
        assert parser.cardinal(1_000_000) == "un milhou"


class TestEdgeCases:
    def test_zero(self, parser):
        assert parser.cardinal(0) == "zero"

    def test_teens_are_synthetic(self, parser):
        # 11-15 are single words, not *diêç i un* etc.
        for n in range(11, 16):
            assert " " not in parser.cardinal(n)

    def test_negative(self, parser):
        assert parser.pronounce_token("-4") == "menos quatro"


class TestOrdinals:
    @pytest.mark.parametrize("n,expected", [
        (1, "purmeiro"), (2, "segundo"), (3, "terceiro"), (4, "quarto"),
        (5, "quinto"), (7, "sétimo"), (8, "óutabo"), (9, "nono"),
    ])
    def test_ordinal_masc(self, parser, n, expected):
        assert parser.ordinal(n) == expected

    def test_ordinal_feminine_agreement(self, parser):
        assert parser.ordinal(1, "feminine") == "purmeira"
        assert parser.ordinal(4, "feminine") == "quarta"

    def test_ordinal_out_of_range(self, parser):
        with pytest.raises(ValueError):
            parser.ordinal(11)


class TestDecimal:
    def test_decimal_reads_digitwise(self, parser):
        # Iberian decimal comma; *bírgula* then digit-by-digit.
        assert parser.pronounce_token("3,5") == "trés bírgula cinco"
        assert parser.pronounce_token("3.5") == "trés bírgula cinco"


class TestSendinesVariants:
    """Sendinês forms — Vasconcelos §189 p.350, Obs. 4."""

    @pytest.fixture(scope="class")
    def sp(self):
        return MirandeseNumberParser("mwl-x-sendim")

    @pytest.mark.parametrize("n,expected", [
        (2, "dus"), (7, "site"), (8, "uito"), (9, "nube"), (10, "deç"),
        (200, "duzintos"), (300, "trezintos"),
    ])
    def test_sendim(self, sp, n, expected):
        assert sp.cardinal(n) == expected


class TestNormalizeNumbers:
    def test_cardinal_in_context(self):
        assert normalize_numbers("tengo 2 gatos") == "tengo dous gatos"

    def test_compound_in_context(self):
        assert normalize_numbers("21 anhos") == "binte i un anhos"

    def test_ordinal_marker_masc(self):
        assert normalize_numbers("l 1º die") == "l purmeiro die"

    def test_ordinal_marker_fem(self):
        assert normalize_numbers("la casa 5ª") == "la casa quinta"

    def test_punctuation_preserved(self):
        assert normalize_numbers("(3) gatos, 2!") == "(trés) gatos, dous!"

    def test_non_numeric_untouched(self):
        # regression: text with no digits is returned byte-for-byte
        text = "la lhéngua mirandesa ye falada an Miranda de l Douro"
        assert normalize_numbers(text) == text

    def test_ordinal_out_of_range_left_alone(self):
        # only 1-10 have ordinals; 99º is not verbalized
        assert normalize_numbers("99º") == "99º"

    def test_unknown_dialect_falls_back(self):
        assert normalize_numbers("2", dialect="zz") == "dous"


class TestAttestationSets:
    def test_sets_disjoint(self):
        assert ATTESTED.isdisjoint(DERIVED)

    def test_dialects(self):
        assert "mwl" in DIALECTS


class TestPhonemizerIntegration:
    @pytest.fixture(scope="class")
    def pho(self):
        return MirandesePhonemizer("mwl")

    def test_numbers_expanded_by_default(self, pho):
        # "2" becomes *dous* and is transcribed by the lattice
        assert pho.phonemize("2") == pho.phonemize("dous")

    def test_expand_numbers_off_keeps_digit(self, pho):
        assert "2" in pho.phonemize("tengo 2 gatos", expand_numbers=False)

    def test_no_digit_text_matches_bare_lattice(self, pho):
        # regression: number stage is a no-op on digit-free text
        assert pho.phonemize("lhéngua") == pho.phonemize("lhéngua",
                                                         expand_numbers=False)
