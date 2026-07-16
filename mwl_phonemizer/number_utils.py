"""Mirandese number verbalization — the orthography2ipa normalizer stage.

Numbers written as digits carry no orthography a grapheme-to-phoneme lattice can
read, so they are spelled out into Mirandese words *before* the pronunciation
lattice runs. This mirrors the architecture tugaphone uses for Portuguese
(``tugaphone.number_utils`` wired as the orthography2ipa ``normalizer``): a
:class:`MirandeseNumberParser` turns one numeric token into words, and
:func:`normalize_numbers` rewrites every numeric token in running text, leaving
non-numeric tokens untouched. :class:`~mwl_phonemizer.MirandesePhonemizer` calls
it before splitting text into transcribable letter runs, so the spelled-out
words then flow through the lattice's sandhi and stress like any other word.

Unlike tugaphone this module does **not** delegate to ``unicode_rbnf`` — that
library ships no Mirandese ruleset. The number words are a native, source-cited
table plus a small recursive composer.

Attestation
-----------
Every base word is tagged in :data:`ATTESTED` or :data:`DERIVED`:

* **Attested** forms are spelled verbatim in Leite de Vasconcelos, *Estudos de
  Philologia Mirandesa* vol. I, §189 (cardinals, pp. 347–351) and §190
  (ordinals, pp. 351–352), cross-checked against the native numeral headwords
  of ``TigreGotico/mirandese-ipa-dict-synthetic``. Vasconcelos gives the full
  cardinal set through 500 and the tens 50–90 explicitly.
* **Derived** forms are not spelled out in the source and are built by the rule
  Vasconcelos himself states for the gap: *"De quatrocientos para cima, até mil,
  os cardinaes formaram-se … periphrasticamente"* (p. 349) — i.e. the hundreds
  600–900 follow the attested ``cardinal + -cientos`` pattern (400
  *quatrocientos*, 500 *cincocientos*), and the scale words above *milhou*, the
  ordinals 6th/10th and the decimal word are reconstructed by the regular
  ``v→b`` / final-vowel adaptation. They are the engine's best reconstruction,
  not a citation, and are marked so a reviewer can tell the two apart.

Conjunction: Mirandese joins numeral groups with the copulative **i** ("and") —
Vasconcelos fixes this in his orthographic convention (*"Com i represento a
conjunção correspondente á portuguesa e"*, vol. I). The specific compound
spellings (*binte i un*, *cien i cinco*) are composed here from attested atoms;
the pattern is attested, the exact strings are not written in the source.
"""
from typing import Dict, List, Optional, Tuple

#: Mirandese spec codes this module knows how to verbalize for.
DIALECTS = ("mwl", "mwl-x-sendim", "mwl-x-ifanes")

#: Copulative conjunction ("and") joining numeral groups (Convénio).
_AND = "i"

#: Decimal separator word. Portuguese reads the point as *vírgula*; the
#: Mirandese reflex applies the regular ``v→b`` correspondence. DERIVED.
_DECIMAL_WORD = "bírgula"

#: Word for the sign of a negative number. DERIVED (Mirandese *menos*).
_MINUS_WORD = "menos"

# ---------------------------------------------------------------------------
# Base numeral tables. Central (mwl) is the default; per-dialect overrides
# layer on top. Feminine forms are given only where the numeral inflects for
# gender (1 and 2 in Ibero-Romance).
# ---------------------------------------------------------------------------

#: units 0-9, masculine. ATTESTED except 0.
_UNITS_M: Dict[int, str] = {
    0: "zero",      # DERIVED (Mirandese has no distinct native zero word)
    1: "un",        # ATTESTED
    2: "dous",      # ATTESTED
    3: "trés",      # ATTESTED
    4: "quatro",    # ATTESTED
    5: "cinco",     # ATTESTED
    6: "seis",      # ATTESTED
    7: "siête",     # ATTESTED (central)
    8: "oito",      # ATTESTED
    9: "nuobe",     # ATTESTED (central)
}

#: feminine overrides for the gendered units. ATTESTED.
_UNITS_F: Dict[int, str] = {
    1: "ũa",        # ATTESTED
    2: "dues",      # ATTESTED
}

#: 10-19. All ATTESTED (Vasconcelos §189 p.348: dezaseis, dezasiete, dezuito,
#: dezanobe — note the reduced *-nobe* stem in compounds, not *nuobe*).
_TEENS: Dict[int, str] = {
    10: "diêç",         # ATTESTED (central)
    11: "ounze",        # ATTESTED
    12: "doze",         # ATTESTED
    13: "treze",        # ATTESTED
    14: "quatorze",     # ATTESTED
    15: "quinze",       # ATTESTED
    16: "dezaseis",     # ATTESTED (var. dezasseis)
    17: "dezasiete",    # ATTESTED (var. dezassiete)
    18: "dezuito",      # ATTESTED
    19: "dezanobe",     # ATTESTED
}

#: tens 20-90. All ATTESTED (Vasconcelos §189 p.348: cincoenta, sessenta,
#: setenta, uitenta, nobenta).
_TENS: Dict[int, str] = {
    20: "binte",        # ATTESTED
    30: "trinta",       # ATTESTED
    40: "quarenta",     # ATTESTED
    50: "cincoenta",    # ATTESTED
    60: "sessenta",     # ATTESTED
    70: "setenta",      # ATTESTED
    80: "uitenta",      # ATTESTED
    90: "nobenta",      # ATTESTED
}

#: hundreds. 100 is *cien* (Vasconcelos p.348), used both standalone and before
#: a remainder (*cien i cinco*). 200-500 ATTESTED (duzentos, trezentos,
#: quatrocientos, cincocientos); 600-900 DERIVED on the attested *cardinal +
#: -cientos* pattern (the periphrastic rule Vasconcelos states, p.349).
_HUNDRED_ONE = "cien"        # ATTESTED (100, standalone and compound head)
_HUNDREDS: Dict[int, str] = {
    200: "duzentos",        # ATTESTED (sendinês duzintos)
    300: "trezentos",       # ATTESTED (sendinês trezintos)
    400: "quatrocientos",   # ATTESTED
    500: "cincocientos",    # ATTESTED
    600: "seiscientos",     # DERIVED
    700: "siêtecientos",    # DERIVED
    800: "oitocientos",     # DERIVED
    900: "nuobecientos",    # DERIVED
}

#: scale words. *mil* and *milhou* ATTESTED (Vasconcelos p.348); the plural
#: *milhones* and *bilhou/bilhones* DERIVED (regular ``-ou/-ones`` reflex).
_THOUSAND = "mil"                       # ATTESTED
_MILLION = ("milhou", "milhones")       # milhou ATTESTED, milhones DERIVED
_BILLION = ("bilhou", "bilhones")       # DERIVED

#: ordinals 1-10, masculine. Vasconcelos §190 p.351: 1st-5th, 7th-9th spelled
#: out (nono flagged literary); 6th only as *sésta-feira*, 10th only *décima* —
#: their standalone masculines are DERIVED. Vasconcelos: *"O povo faz pouco uso
#: dos ordinaes"* — beyond ~5th these are learned.
_ORDINALS_M: Dict[int, str] = {
    1: "purmeiro",     # ATTESTED
    2: "segundo",      # ATTESTED
    3: "terceiro",     # ATTESTED
    4: "quarto",       # ATTESTED
    5: "quinto",       # ATTESTED
    6: "sesto",        # DERIVED (only sésta-feira attested)
    7: "sétimo",       # ATTESTED (var. sétemo)
    8: "óutabo",       # ATTESTED (var. uitabo)
    9: "nono",         # ATTESTED (literary)
    10: "décimo",      # DERIVED (only décima attested)
}

#: base entries attested verbatim in Vasconcelos §189-190 / the native dict.
ATTESTED = {
    "un", "ũa", "dous", "dues", "trés", "quatro", "cinco", "seis", "siête",
    "oito", "nuobe", "diêç", "ounze", "doze", "treze", "quatorze", "quinze",
    "dezaseis", "dezasiete", "dezuito", "dezanobe",
    "binte", "trinta", "quarenta", "cincoenta", "sessenta", "setenta",
    "uitenta", "nobenta",
    "cien", "duzentos", "trezentos", "quatrocientos", "cincocientos",
    "mil", "milhou",
    "purmeiro", "purmeira", "segundo", "terceiro", "quarto", "quinto",
    "sétimo", "óutabo", "nono",
    # sendinês attested variants (Vasconcelos p.350 Obs.4)
    "dus", "site", "nube", "uito", "deç", "duzintos", "trezintos",
}
DERIVED = {
    "zero",
    "seiscientos", "siêtecientos", "oitocientos", "nuobecientos",
    "milhones", "bilhou", "bilhones",
    "sesto", "décimo",
    "bírgula", "menos",
}

#: per-dialect overrides applied on top of the central tables. Sendinês forms
#: are ATTESTED (Vasconcelos §189 p.350, Obs. 4).
_DIALECT_OVERRIDES: Dict[str, Dict[str, Dict[int, str]]] = {
    "mwl-x-sendim": {
        "units": {2: "dus", 7: "site", 8: "uito", 9: "nube"},
        "teens": {10: "deç"},
        "hundreds": {200: "duzintos", 300: "trezintos"},
    },
}


def _tables(dialect: str) -> Dict[str, Dict]:
    """Return the numeral tables for *dialect* (central base + overrides)."""
    units_m = dict(_UNITS_M)
    teens = dict(_TEENS)
    hundreds = dict(_HUNDREDS)
    ov = _DIALECT_OVERRIDES.get(dialect, {})
    units_m.update(ov.get("units", {}))
    teens.update(ov.get("teens", {}))
    hundreds.update(ov.get("hundreds", {}))
    return {"units_m": units_m, "teens": teens, "hundreds": hundreds}


class MirandeseNumberParser:
    """Spell an integer or a numeric token into Mirandese words.

    The composer is recursive over scale groups (units < 100, hundreds,
    thousands, millions), joined by the copulative :data:`_AND`. Gender applies
    only to the gendered units 1 and 2 and to hundreds' units where a following
    noun would agree; this class exposes the gendered forms and lets the caller
    pick, defaulting to masculine (the Ibero-Romance citation gender).
    """

    def __init__(self, dialect: str = "mwl"):
        if dialect not in DIALECTS:
            raise ValueError(
                f"unknown dialect {dialect!r}; expected one of {DIALECTS}")
        self.dialect = dialect
        t = _tables(dialect)
        self.units_m = t["units_m"]
        self.teens = t["teens"]
        self.hundreds = t["hundreds"]

    # -- helpers ---------------------------------------------------------
    def _unit(self, n: int, gender: str) -> str:
        if gender == "feminine" and n in _UNITS_F:
            return _UNITS_F[n]
        return self.units_m[n]

    def _under_100(self, n: int, gender: str) -> str:
        if n < 10:
            return self._unit(n, gender)
        if n < 20:
            return self.teens[n]
        tens, unit = divmod(n, 10)
        base = _TENS[tens * 10]
        if unit == 0:
            return base
        return f"{base} {_AND} {self._unit(unit, gender)}"

    def _under_1000(self, n: int, gender: str) -> str:
        if n < 100:
            return self._under_100(n, gender)
        hundreds, rem = divmod(n, 100)
        if hundreds == 1:
            head = _HUNDRED_ONE
        else:
            head = self.hundreds[hundreds * 100]
        if rem == 0:
            return head
        return f"{head} {_AND} {self._under_100(rem, gender)}"

    def _scale(self, n: int, gender: str) -> str:
        """Compose an arbitrary non-negative integer."""
        if n < 1000:
            return self._under_1000(n, gender)
        if n < 1_000_000:
            thousands, rem = divmod(n, 1000)
            # 1000 is bare *mil*, not *un mil*
            head = _THOUSAND if thousands == 1 \
                else f"{self._under_1000(thousands, 'masculine')} {_THOUSAND}"
            return head if rem == 0 else f"{head} {self._join_rem(rem, gender)}"
        return self._big(n, gender)

    def _big(self, n: int, gender: str) -> str:
        for divisor, (sing, plur) in ((1_000_000_000, _BILLION),
                                      (1_000_000, _MILLION)):
            if n >= divisor:
                count, rem = divmod(n, divisor)
                word = sing if count == 1 else plur
                head = f"{self._under_1000(count, 'masculine')} {word}"
                return head if rem == 0 \
                    else f"{head} {self._join_rem(rem, gender)}"
        return self._under_1000(n, gender)

    def _join_rem(self, rem: int, gender: str) -> str:
        # a remainder under 100 is joined with the copulative *i*; larger
        # remainders simply follow (cf. *mil i dous* vs *mil dozientos*).
        tail = self._scale(rem, gender)
        return f"{_AND} {tail}" if rem < 100 else tail

    # -- public API ------------------------------------------------------
    def cardinal(self, n: int, gender: str = "masculine") -> str:
        """Spell integer *n* as a cardinal (``gender`` = masculine/feminine)."""
        if n < 0:
            return f"{_MINUS_WORD} {self.cardinal(-n, gender)}"
        if n == 0:
            return _UNITS_M[0]
        return self._scale(n, gender)

    def ordinal(self, n: int, gender: str = "masculine") -> str:
        """Spell integer *n* (1-10) as an ordinal.

        Only 1-10 are provided; the ordinal stems above ten are analytic in
        the sources and are left to the caller. Feminine swaps the final
        ``-o`` for ``-a`` (the regular Ibero-Romance ordinal agreement).
        """
        if n not in _ORDINALS_M:
            raise ValueError(f"ordinal out of supported range 1-10: {n}")
        word = _ORDINALS_M[n]
        if gender == "feminine" and word.endswith("o"):
            return word[:-1] + "a"
        return word

    def decimal(self, whole: int, frac: str, gender: str = "masculine") -> str:
        """Spell a decimal: whole part, *bírgula*, then digit-by-digit frac."""
        digits = " ".join(self._unit(int(d), gender) for d in frac)
        return f"{self.cardinal(whole, gender)} {_DECIMAL_WORD} {digits}"

    def year(self, n: int) -> str:
        """Spell a year as a plain cardinal (Mirandese reads years in full)."""
        return self.cardinal(n, "masculine")

    # -- token handling --------------------------------------------------
    def pronounce_token(self, token: str, gender: str = "masculine",
                        as_ordinal: bool = False) -> Optional[str]:
        """Spell one numeric *token* ("12", "3,5", "-4"), or ``None``."""
        t = token.strip()
        neg = t.startswith("-")
        if neg:
            t = t[1:]
        # decimal (comma is the Mirandese/Iberian decimal mark; also accept .)
        for sep in (",", "."):
            if sep in t:
                whole_s, _, frac_s = t.partition(sep)
                if whole_s.isdigit() and frac_s.isdigit():
                    out = self.decimal(int(whole_s), frac_s, gender)
                    return f"{_MINUS_WORD} {out}" if neg else out
        if not t.isdigit():
            return None
        n = int(t)
        val = self.ordinal(n, gender) if as_ordinal else self.cardinal(n, gender)
        return f"{_MINUS_WORD} {val}" if neg else val


def normalize_numbers(text: str, dialect: str = "mwl",
                      strict: bool = False) -> str:
    """Replace numeric tokens in *text* with their Mirandese written forms.

    This is the orthography2ipa normalizer stage: it runs on raw orthographic
    text before the pronunciation lattice, so spelled-out numbers are then
    transcribed like any other word. Non-numeric tokens are returned untouched.

    :param dialect: a Mirandese spec code (see :data:`DIALECTS`).
    :param strict: when true, re-raise a token that fails to verbalize;
        otherwise leave it in place.
    """
    if dialect not in DIALECTS:
        dialect = "mwl"
    parser = MirandeseNumberParser(dialect)
    words = text.split()
    out: List[str] = []
    for word in words:
        prefix, core, suffix = _split_affixes(word)
        # a trailing ordinal marker (º masc / ª fem) makes it an ordinal and
        # fixes its gender, and is consumed (not carried into the output).
        as_ord = suffix[:1] in _ORDINAL_MARKERS
        gender = "feminine" if suffix[:1] == _ORD_FEM else "masculine"
        emit_suffix = suffix[1:] if as_ord else suffix
        try:
            spelled = parser.pronounce_token(
                core, gender=gender, as_ordinal=as_ord) if core else None
        except Exception:
            if strict:
                raise
            spelled = None
        out.append(f"{prefix}{spelled}{emit_suffix}"
                   if spelled is not None else word)
    return " ".join(out)


_ORD_MASC = "º"
_ORD_FEM = "ª"
_ORDINAL_MARKERS = (_ORD_MASC, _ORD_FEM)


def _split_affixes(word: str) -> Tuple[str, str, str]:
    """Split leading/trailing punctuation off a token's numeric core."""
    start, end = 0, len(word)
    while start < end and not (word[start].isdigit() or word[start] == "-"):
        start += 1
    while end > start and not word[end - 1].isdigit():
        end -= 1
    return word[:start], word[start:end], word[end:]
