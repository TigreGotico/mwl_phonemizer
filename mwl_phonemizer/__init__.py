"""Mirandese (mwl) grapheme-to-phoneme conversion.

Architecture: the base transcription comes from the ``orthography2ipa``
Mirandese pronunciation lattice (``G2P("mwl")`` and dialect specs), and a
linear-chain CRF trained on native-speaker gold pronunciations corrects the
lattice output. Words present in the gold dictionary are returned verbatim.

Quickstart::

    from mwl_phonemizer import MirandesePhonemizer

    pho = MirandesePhonemizer(dialect="mwl")
    pho.phonemize("lhéngua")            # single word
    pho.phonemize("Falo la lhéngua mirandesa.")  # full text

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

#: orthography2ipa spec codes with a Mirandese language spec
DIALECTS = ("mwl", "mwl-x-sendim", "mwl-x-ifanes")


def strip_markers(ipa: str) -> str:
    """Drop syllable dots and optional-phoneme parentheses from *ipa*."""
    return ipa.replace(".", "").replace("(", "").replace(")", "")


class MirandesePhonemizer:
    """Mirandese G2P: gold-dictionary lookup, o2i lattice base, CRF correction.

    :param dialect: ``orthography2ipa`` spec code — one of :data:`DIALECTS`.
    :param use_crf: apply the CRF correction layer to out-of-dictionary
        words. When ``False``, out-of-dictionary words get the raw
        ``orthography2ipa`` transcription.
    :param crf_model_path: path to a saved CRF model. When given and the file
        exists it is loaded; otherwise the CRF is trained on the gold
        dictionary at construction time (fast — a few seconds) and, if a path
        was given, saved there.
    """

    def __init__(self, dialect: str = "mwl",
                 use_crf: bool = True,
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

    def phonemize(self, text: str, lookup: bool = True) -> str:
        """IPA for *text* — a single word or a full sentence.

        Words (and multi-word expressions) found in the gold dictionary are
        returned verbatim when *lookup* is true; everything else goes through
        the o2i lattice plus, when enabled, the CRF corrector. Punctuation
        and whitespace are preserved.
        """
        text = text.strip()
        if lookup and text.lower() in self.gold:
            return self.gold[text.lower()]
        parts = re.findall(r"[^\W\d_]+|[\W\d_]+", text.replace("-", " "))
        out = []
        for part in parts:
            if part.isalpha():
                out.append(self.phonemize_word(part, lookup=lookup))
            else:
                out.append(part)
        return "".join(out)

    def phonemize_word(self, word: str, lookup: bool = True) -> str:
        """IPA for a single *word*."""
        word = word.lower().strip()
        if lookup and word in self.gold:
            return self.gold[word]
        if self.crf is not None:
            return self.crf.predict(word)
        return self.g2p.transcribe_word(word)

    # ------------------------------------------------------------------
    # The surface downstream code relies on. mwl_phonemizer is an engine built
    # ON orthography2ipa, not a plugin to it — nothing there discovers or calls it.
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
