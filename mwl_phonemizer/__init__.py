"""Mirandese (mwl) grapheme-to-phoneme conversion.

Architecture: the transcription is the ``orthography2ipa`` Mirandese
pronunciation lattice (``G2P("mwl")`` and its dialect specs), which owns the
Mirandese phonology — grapheme rules, allophony, cross-word sandhi and stress.
This library is a thin Mirandese-facing wrapper over that engine; it adds only
what o2i does not: dialect selection, an optional native-speaker lexicon
overlay returned verbatim, and punctuation-preserving text handling.

Default rationale: against the only human-authored Mirandese gold — the 219-word
``TigreGotico/mirandese_g2p`` dictionary — the pure lattice scores 18.01% PER
(folded) / 11.62% once the documented broad-vs-narrow notation gap is folded out.
An optional CRF corrector (:mod:`mwl_phonemizer.crf`) trained on that dictionary
edges the lattice on folded PER, but on the convention-neutral basis the gap is
~0.4pp: the CRF mostly matches the lexicon's narrow convention rather than fixing
real errors, and couples every output to it. So the convention-neutral, untrained
lattice is the default; the CRF and lexicon lookup are opt-in. (The o2i-shipped
20-sentence sets, which the lattice reproduces at ~0% PER, are engine-pinned —
a consistency check, not an accuracy measurement.) See the README accuracy table.

Quickstart::

    from mwl_phonemizer import MirandesePhonemizer

    pho = MirandesePhonemizer(dialect="mwl")
    pho.phonemize("lhéngua")            # single word
    pho.phonemize("Falo la lhéngua mirandesa.")  # full text, sandhi + stress

or the module-level convenience::

    from mwl_phonemizer import phonemize
    phonemize("lhéngua")
"""

import re
from functools import lru_cache
from typing import List, Optional

from orthography2ipa import G2P
from orthography2ipa import WordContext

from mwl_phonemizer.crf import CRFCorrector, strip_stress
from mwl_phonemizer.gold import GOLD, CENTRAL, SENDINESE, RAIANO
from mwl_phonemizer.number_utils import normalize_numbers, MirandeseNumberParser

#: orthography2ipa spec codes with a Mirandese language spec
DIALECTS = ("mwl", "mwl-x-sendim", "mwl-x-ifanes")

#: a run of letters with internal spaces/apostrophes — a phrase the o2i engine
#: can transcribe with cross-word sandhi; everything else (punctuation, digits)
#: is preserved verbatim.
_PHRASE = re.compile(r"[^\W\d_](?:[ '’]?[^\W\d_])*")


def strip_markers(ipa: str) -> str:
    """Drop syllable dots and optional-phoneme parentheses from *ipa*."""
    return ipa.replace(".", "").replace("(", "").replace(")", "")


class MirandesePhonemizer:
    """Mirandese G2P over the ``orthography2ipa`` lattice.

    The lattice engine does the phonology; this class layers dialect selection,
    an optional native-speaker lexicon overlay (exact words returned verbatim)
    and optional CRF correction on top, and preserves punctuation in text.

    :param dialect: ``orthography2ipa`` spec code — one of :data:`DIALECTS`.
    :param use_crf: when true, correct out-of-lexicon words with a CRF trained
        on the bundled word dictionary. Off by default: on the research gold the
        raw lattice is exact and the CRF, tuned to the word dictionary's
        convention, only diverges from it. Kept for reproducibility and for
        callers whose target matches that convention.
    :param crf_model_path: path to a saved CRF model, used only when
        ``use_crf`` is true. When the file exists it is loaded; otherwise the
        CRF is trained on the lexicon at construction (a few seconds) and, if a
        path was given, saved there.
    """

    def __init__(self, dialect: str = "mwl",
                 use_crf: bool = False,
                 crf_model_path: str | None = None):
        if dialect not in DIALECTS:
            raise ValueError(f"unknown dialect {dialect!r}; expected one of {DIALECTS}")
        self.dialect = dialect
        self.g2p = G2P(dialect)
        self.gold = {word: strip_markers(ipa)
                     for word, ipa in GOLD[dialect].items()}
        self.crf: CRFCorrector | None = None
        if use_crf:
            self.crf = CRFCorrector(self.g2p)
            if crf_model_path:
                import os
                if os.path.exists(crf_model_path):
                    self.crf.load(crf_model_path)
                else:
                    self.crf.train(list(self.gold.items()))
                    self.crf.save(crf_model_path)
            else:
                self.crf.train(list(self.gold.items()))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def phonemize(self, text: str, lookup: bool = False,
                  expand_numbers: bool = True) -> str:
        """IPA for *text* — a single word or a full sentence.

        Each letter run is transcribed by the ``orthography2ipa`` engine as a
        whole phrase, so its cross-word sandhi and stress apply; punctuation and
        whitespace are preserved between runs. When *lookup* is true, words and
        multi-word expressions present in the native-speaker lexicon overlay are
        returned verbatim instead, and any phrase containing such a word is done
        word-by-word so the overlay wins (this trades the engine's phrase-level
        sandhi for the overlay's per-word transcriptions).

        When *expand_numbers* is true (the default), numeric tokens are spelled
        out into Mirandese words by :func:`~mwl_phonemizer.number_utils.normalize_numbers`
        *before* the lattice runs — the normalizer stage — so the spelled-out
        words are transcribed with the engine's own sandhi and stress. Pass
        ``expand_numbers=False`` to leave digits untouched.
        """
        text = text.strip()
        if expand_numbers:
            text = normalize_numbers(text, self.dialect)
        if lookup and text.lower() in self.gold:
            return self.gold[text.lower()]
        out = []
        pos = 0
        for m in _PHRASE.finditer(text):
            out.append(text[pos:m.start()])
            out.append(self._phonemize_phrase(m.group(), lookup=lookup))
            pos = m.end()
        out.append(text[pos:])
        return "".join(out)

    def _phonemize_phrase(self, phrase: str, lookup: bool) -> str:
        """Transcribe one letter run, honouring the lexicon overlay."""
        if lookup and phrase.lower() in self.gold:
            return self.gold[phrase.lower()]
        words = phrase.split()
        # A lexicon hit or the CRF needs the per-word path; otherwise let the
        # engine transcribe the whole phrase so sandhi crosses word gaps.
        if self.crf is None and not (
                lookup and any(w.lower() in self.gold for w in words)):
            return self.g2p.transcribe(phrase)
        return " ".join(self.phonemize_word(w, lookup=lookup) for w in words)

    def phonemize_word(self, word: str, lookup: bool = False) -> str:
        """IPA for a single *word*.

        The raw ``orthography2ipa`` lattice transcription, unless *lookup* is
        true and the word is in the native-speaker lexicon overlay, or the CRF
        corrector is enabled.
        """
        word = word.lower().strip()
        if lookup and word in self.gold:
            return self.gold[word]
        if self.crf is not None:
            return self.crf.predict(word)
        return self.g2p.transcribe_word(word)

    # ------------------------------------------------------------------
    # Engine surface the downstream code relies on. mwl_phonemizer is an engine
    # built ON orthography2ipa, not a plugin to it — nothing there discovers or
    # calls it.
    # ------------------------------------------------------------------

    @property
    def language_codes(self) -> List[str]:
        codes = ["mwl"]
        if self.dialect != "mwl":
            codes.append(self.dialect)
        return codes

    def transcribe(self, text: str) -> str:
        return self.phonemize(text)

    def transcribe_word(self, word: str, context: Optional[WordContext] = None) -> str:
        return self.phonemize_word(word)


@lru_cache(maxsize=None)
def _default_phonemizer(dialect: str) -> MirandesePhonemizer:
    return MirandesePhonemizer(dialect=dialect)


def phonemize(text: str, dialect: str = "mwl") -> str:
    """IPA for *text* using a cached default :class:`MirandesePhonemizer`."""
    return _default_phonemizer(dialect).phonemize(text)
