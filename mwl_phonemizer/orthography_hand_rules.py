"""Rule-based Mirandese G2P built on the shared orthography2ipa lattice.

Grapheme segmentation is delegated to the language-agnostic
:class:`orthography2ipa.phonetok.PhonetokTokenizer` (a maximal-munch trie
over the Mirandese grapheme set declared in ``g2p.json``) and every
context-sensitive realisation rule runs as a
:class:`orthography2ipa.rescorer.LatticeRescorer` re-costing the shared
per-grapheme :class:`~orthography2ipa.phonetok.SegmentSlot` lattice. There
is no private tokenizer and no hand-rolled index arithmetic: the bespoke
``while i < len(word)`` scanner has been replaced by the shared trie plus a
single rescorer that resolves each grapheme to its Mirandese realisation.

Reference phonetic info (Wikipedia, "Mirandese language", drawing on Leite
de Vasconcelos and the Convénçon Ortográfica da Lhéngua Mirandesa):

# Ortography

Mirandese is written using the Latin alphabet, with a Portuguese basis for orthography due to its political situation:

| [Letters](https://en.wikipedia.org/wiki/Letter_(alphabet) "Letter (alphabet)") and [Dipgraphs](https://en.wikipedia.org/wiki/Digraph_(orthography) "Digraph (orthography)") | Names[[10]](https://en.wikipedia.org/wiki/Mirandese_language#cite_note-CDM-11) | [IPA](https://en.wikipedia.org/wiki/International_Phonetic_Alphabet "International Phonetic Alphabet") |
| --- | --- | --- |
| Uppercase | Lowercase |
| A | a | á | /a/, /ɐ/ |
| AN | an | - | /ɐ̃(ŋ)/ |
| B | b | bé | /b/, /β/ |
| C | c | cé, qué | /k/, /s/ |
| Ç | ç | cé de cedilha | /s/, /z/ |
| D | d | dé | /d/, /ð/ |
| E | e | é | /ɛ/, /e/, /ɨ/ |
| EN | en | - | /ẽ(ŋ)//ɨ̃/ |
| F | f | fé | /f/ |
| G | g | gué | /g/, /ɣ/, /ʒ/ |
| H| h | hagá | — |
| I | i | i | /i/, /j/ |
| IN | in | - | /ĩ(ŋ)/, /ɨ̃j̃/ (Sendinese) |
| J | j | jé | /ʒ/ |
| L | l | lé | /l/, /ɫ/ |
| LH | lh | - | /ʎ/ |
| M | m | mé | /m/, /~/ |
| N | n | né | /n/, /~/, /ŋ/ |
| NH | nh | - | /ɲ/ |
| O | o | ó | /ɔ/, /o/, /u/, /ʊ/ |
| ON | on | - | /õ(ŋ)/ |
| P | p | pé | /p/ |
| Q | q | qué | /k/ |
| R | r | ré | /ɾ/, /r/ |
| RR | rr | - | /r/ |
| S | s | sé | /s̺/, /z̺/ |
| SS | s | - | /s̺/ |
| T | t | té | /t/ |
| U | u | u | /u/, /w/, /ũ/ |
| UN | un | - | /ũ(ŋ)/, /ʊ̃(ŋ)/ |
| X | x | xiç | /ʃ/ |
| Y | y | i griego | /j/ |
| Z | z | zé | /z/ |

Three variants of the Mirandese language exist: Border Mirandese (_Mirandés Raiano_), Central Mirandese (_Mirandés Central_) and Sendinese (_Sendinés_). Most speakers of Mirandese also speak Portuguese.

Despite there being a singular writing system for mirandese, there is one aspect that is written differently in different dialects. In the Sendinese dialect, many words that in other dialects are said with /ʎ/ ⟨lh⟩, are said with /l/ ⟨l⟩ (_alá_ for _alhá_ 'over there', _lado_ for _lhado_ 'side', _luç_ for _lhuç_ 'light', amongst others)


# Phonology

/s̺/ and /z̺/ indicate apico-alveolar sibilants (as in modern Catalan, northern/central peninsular Spanish and coastal northern European Portuguese), while /s̻/ and /z̻/ are dentalized laminal alveolar sibilants (as in most modern Portuguese, French and English). The unrelated Basque language also maintains a distinction between /s̺/ and /s̻/ (Basque has no voiced sibilants), which suggests that the distinction originally was an areal feature across Iberia.

Portuguese spelling still distinguishes all seven and is identical to Mirandese spelling in this respect, but in pronunciation, Portuguese has reduced them to four /s, z, ʃ, ʒ/ except in northern hinterland European Portuguese dialects, including those of the area that Mirandese is spoken. Northern/central Peninsular Spanish has also reduced them to four but in quite a different way: /tʃ, θ, s̺, x/. Western Andalusian Spanish and Latin American Spanish have further reduced them to three: /tʃ, s̻, x/.

- Retention of the initial /f/ from Latin, like nearly all dialects of Western Romance (the major maverick being Spanish, where /f/> /h/ > ∅).
- As in Leonese and Galician-Portuguese, the Latin initial consonant clusters /pl/, /kl/, /fl/ evolve into /tʃ/.
- Proto-Romance medial clusters -ly- and -cl- became medial /ʎ/.
- The cluster /-mb-/ is kept.
- Proto-Romance -mn- becomes /m/: lūm'nem > lume.
- Falling diphthongs /ei/, /ou/ preserved.
- Final -o becomes /u/.
- Voiced sibilants are still maintained.
- Retention of intervocalic /l/, /n/.
- Western Romance /ɛ/, /ɔ/ can diphthongize to /jɛ/, /wo/ (as in Italian). That happens not only before palatals, as in Aragonese, but also before nasals.
- /l/ is palatalized word-initially (as in other Astur-Leonese languages and in Catalan).

# Consonants

- the laminal dental sibilants correspond to Portuguese /s, z/. These are spelled c/ç and z. The corresponding alveolar sibilants are apical and are spelled s(s) and s. Furthermore, there is an additional palatal affricate /tʃ/ ch that is distinct from the fricative /ʃ/, spelled x. The voiced /ʒ/ is spelled j or g, as in Portuguese. Standard Portuguese has reduced all those sounds to just four fricatives: /s, z, ʃ, ʒ/.
- The "hard" or "long" R is an alveolar trill /r/, as in other varieties of Astur-Leonese and Spanish. The Portuguese uvular fricative [ʁ] is not found in Mirandese. The "soft" or "short" R is an ordinary alveolar tap [ɾ] commonly found in the Iberian Peninsula. As in other languages spoken in the region, the two contrast only in the word-internal position.
- Voiced stops /b, d, ɡ/ can be lenited as fricatives [β, ð, ɣ].

# Vowels

All oral and nasal vowel sounds and allophones are the same from Portuguese, with different allophones:

- /a/ has allophones of [ä, ɐ], /e/ with [ɛ, e, ɨ], and /o/ with [ɔ, o, u] and [ʊ]. And with the addition of nasal vowel sounds [ɨ̃] and [ɛ̃] for /ẽ/.
- Vowels /i, u/ can become glides [j, w] when preceding or following other vowels.

# Morphology

As in Portuguese, Mirandese still uses the following synthetic tenses:

. Synthetic pluperfect in -ra.
. Future subjunctive in -r(e).
. Personal infinitive in -r(e), which has the same endings as the future subjunctive but often differs as the personal infinitive always uses the infinitive stem, whereas the future subjunctive uses the past.

"""

import json
import os.path
import re
from dataclasses import replace
from functools import lru_cache

from orthography2ipa import get
from orthography2ipa.phonetok import (
    PhonetokTokenizer, SegmentSlot, Candidate, TokenKind, flat_contexts,
)
from orthography2ipa.rescorer import LatticeRescorer, RescoreContext, apply_rescorers

from mwl_phonemizer.base import MirandesePhonemizer, Dialects


@lru_cache(maxsize=None)
def _tokenizer(grapheme_key: tuple) -> PhonetokTokenizer:
    """Shared maximal-munch tokenizer over the Mirandese grapheme set.

    Built from the published ``mwl`` spec, but with the grapheme table
    replaced by the local ``g2p.json`` inventory (passed in as a hashable
    tuple of ``(grapheme, first-candidate)`` pairs) so segmentation stays
    identical to the historical hand-rolled scanner while the trie itself
    is the shared o2i one. Positional/allophone/weight branches are cleared
    — this engine resolves realisation entirely through its own rescorer.
    """
    spec = get("mwl")
    graphemes = {g: [ipa] for g, ipa in grapheme_key}
    narrowed = replace(
        spec,
        graphemes=graphemes,
        positional_graphemes=None,
        allophones={},
        grapheme_weights=None,
        allophone_rules=None,
        sandhi_rules=None,
        word_exceptions=None,
    )
    return PhonetokTokenizer(narrowed)


class _MirandeseRescorer(LatticeRescorer):
    """Resolve each Mirandese grapheme to its realisation over the shared
    lattice.

    A thin adapter around :meth:`OrthographyRulesMWL._grapheme_ipa`: it reads
    the slot's grapheme and its character offset (``slot.span[0]``) and asks
    the owning phonemizer for the context-conditioned IPA. Keeping the rule
    body on the phonemizer lets every rule consult the full source word
    (``owner._word``) and the ``g2p.json`` candidate table, exactly as the
    historical scanner did — the migration changes *where* segmentation and
    rescoring happen (the shared trie + B4 seam), not the phonology.
    """

    def __init__(self, owner: "OrthographyRulesMWL"):
        self._owner = owner

    def rescore(self, slot: SegmentSlot, ctx: RescoreContext):
        ipa = self._owner._grapheme_ipa(slot.grapheme, slot.span[0])
        return (Candidate(ipa, 0.0),)


class OrthographyRulesMWL(MirandesePhonemizer):

    def __init__(self, *args, keep_optional_phones=True, keep_stress_marks=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.keep_optional_phones = keep_optional_phones
        self.keep_stress_marks = keep_stress_marks
        # Mapping to convert graphemes to phonemes
        self._vowels = "aeiouáéíóúäɐɛɨɪɔʊ"  # Extended set of vowels for context checking
        self._voiced_consonants = "bdgjlmnrvz"  # Approximated list of voiced consonants
        with open(os.path.join(os.path.dirname(__file__), "g2p.json")) as f:
            self.MWL_ALPHABET_MAP = json.load(f)
        # source word currently being phonemized (read by the rescorer's
        # char-level context rules; the shared lattice slots carry the
        # absolute char offsets that index back into it)
        self._word = ""
        self._rescorers = (_MirandeseRescorer(self),)

    @property
    def _tok(self) -> PhonetokTokenizer:
        key = tuple((g, cands[0]) for g, cands in self.MWL_ALPHABET_MAP.items())
        return _tokenizer(key)

    @staticmethod
    def _stressed_vowel_span(word: str) -> tuple:
        """Approximate the character span of the stressed vowel group.

        Convenção Ortográfica da Língua Mirandesa (1999) stress rules
        (shared with Portuguese): words ending in a vowel (optionally +s)
        are stressed on the penultimate syllable; words ending in any other
        consonant are stressed on the last syllable. Orthographic accents
        (á é í ó ú) mark irregular stress explicitly and are handled by
        their own graphemes, so this helper is only consulted for
        accent-less words. Returns a (start, end) char span of the stressed
        vowel group, or (-1, -1) if the word has no vowel.
        """
        if re.search(r"[áéíóú]", word):
            return (-1, -1)  # accent marks stress; not this helper's job
        groups = [(m.start(), m.end())
                  for m in re.finditer(r"[aeiouy]+", word)]
        if not groups:
            return (-1, -1)
        if re.search(r"[aeiou]s?$", word) and len(groups) > 1:
            return groups[-2]  # paroxytone: vowel(-s) final words
        return groups[-1]  # oxytone: consonant-final words

    def _is_vowel(self, char):
        """Checks if a character is a vowel."""
        return char.lower() in self._vowels

    def _is_voiced_consonant(self, char):
        """Checks if a character is a voiced consonant."""
        return char.lower() in self._voiced_consonants

    def _post_process(self, phonemized: str,
                      keep_optional_phones=True,
                      keep_stress_marks=False) -> str:
        if not self.keep_stress_marks:
            phonemized = (phonemized.
                          replace("ˈ", "").
                          replace(".", ""))
        if self.keep_optional_phones:
            # just drop parentheses
            phonemized = (phonemized.
                          replace("(", "").
                          replace(")", ""))
        else:
            # Remove optional phonemes inside parentheses
            # This regex finds any content within parentheses and replaces the whole match with an empty string
            phonemized = re.sub(r'\([^)]*\)', '', phonemized)
        return phonemized

    def _grapheme_ipa(self, grapheme: str, i: int) -> str:
        """Return the IPA realisation of *grapheme* starting at char offset *i*.

        Pure per-grapheme rule body invoked through the lattice rescorer. It
        reads the source word from ``self._word`` (so word-local context —
        ``word[i-1]`` / ``word[i+1]`` — is exactly what the historical
        scanner used) and selects among the ``g2p.json`` candidates.
        """
        word = self._word
        length = len(grapheme)

        # Dialectal variation for 'l' / 'lh' (Sendinese de-palatalisation):
        # Sendinese says [l] where other variants say [ʎ] ⟨lh⟩, and keeps a
        # word-initial ⟨l⟩ as [l] (Wikipedia: alá/alhá, lado/lhado, luç/lhuç).
        if self.dialect == Dialects.SENDINESE:
            if grapheme == "lh":
                return self.MWL_ALPHABET_MAP["l"][0]  # 'lh' becomes [l] in Sendinese
            elif grapheme == "l" and i == 0:  # Initial 'l' in Sendinese remains [l]
                return self.MWL_ALPHABET_MAP["l"][0]

        # Nasal vowel digraphs ⟨an/am/en/in/on/un⟩.
        #
        # 1. Before a vowel the ⟨n⟩ is a plain onset and the preceding vowel
        #    stays oral: Mirandese retains intervocalic /n/ (Wikipedia,
        #    "Mirandese language", Phonology: "Retention of intervocalic
        #    /l/, /n/"; also Quarteu & Frías Conde 2001, "L Mirandés: Ũa
        #    Lhéngua Minoritaira an Pertual", §2 on the conservation of
        #    Latin -N-). E.g. ⟨paxarina⟩ → [pɐʃɐɾinɐ], not *[pɐʃɐɾĩŋɐ].
        # 2. In coda position (before a consonant or word-finally) the vowel
        #    nasalises. The velar appendix is *optional* — the alphabet
        #    table gives /ɐ̃(ŋ)/, /ẽ(ŋ)/, /ĩ(ŋ)/, /õ(ŋ)/, /ũ(ŋ)/ (Wikipedia,
        #    "Mirandese language", Orthography table, after the Convenção
        #    Ortográfica da Língua Mirandesa 1999) — and is not realised
        #    word-internally: ⟨brincar⟩ → [bɾĩkaɾ]. Word-finally the gold
        #    transcriptions realise it after the high nasal vowels only
        #    (⟨botin⟩ → [bʉtĩŋ], ⟨-un⟩ → [ũŋ]).
        if grapheme in ("an", "am", "en", "in", "on", "un"):
            nxt = word[i + 2] if i + 2 < len(word) else ""
            if nxt and self._is_vowel(nxt):
                oral = {"an": "ɐ", "am": "ɐ", "en": "ɨ",
                        "in": "i", "on": "o", "un": "u"}[grapheme]
                return oral + ("m" if grapheme == "am" else "n")
            nasal = {"an": "ɐ̃", "am": "ɐ̃", "en": "ẽ",
                     "in": "ĩ", "on": "õ", "un": "ũ"}[grapheme]
            if i + 2 >= len(word) and grapheme in ("in", "un"):
                return nasal + "ŋ"  # word-final velar appendix, high vowels
            return nasal

        if grapheme == "a":
            # Rule: /a/ has allophones [ä(=a), ɐ] (Wikipedia, "Mirandese
            # language", Vowels) distributed by stress, as in Portuguese:
            # the open [a] in the stressed syllable, reduced [ɐ] in
            # unstressed syllables. Stress placement follows the Convenção
            # Ortográfica (1999) defaults (see _stressed_vowel_span).
            s, e = self._stressed_vowel_span(word)
            if s <= i < e:
                return self.MWL_ALPHABET_MAP["a"][1]  # stressed [a]
            return self.MWL_ALPHABET_MAP["a"][0]  # unstressed [ɐ]

        if grapheme == "b":
            # Rule: b = [β] between vowels and after voiced consonants
            if (i > 0 and self._is_vowel(word[i - 1])) and \
                    (i + 1 < len(word) and self._is_vowel(word[i + 1])):
                return self.MWL_ALPHABET_MAP["b"][1]  # [β] between vowels
            elif i > 0 and self._is_voiced_consonant(word[i - 1]):
                return self.MWL_ALPHABET_MAP["b"][1]  # [β] after voiced consonants
            else:
                return self.MWL_ALPHABET_MAP["b"][0]  # [b] otherwise
        elif grapheme == "c":
            # Rule: c = [s̻] before e or i, [k] elsewhere
            if (i + 1 < len(word) and word[i + 1].lower() in "ei"):
                return self.MWL_ALPHABET_MAP["c"][1]  # [s̻] before e or i (second element in map)
            else:
                return self.MWL_ALPHABET_MAP["c"][0]  # [k] elsewhere (first element in map)
        elif grapheme == "ç":
            # Rule: ⟨ç⟩ is the *voiceless* laminal dental sibilant [s̻]: "the
            # laminal dental sibilants correspond to Portuguese /s, z/. These
            # are spelled c/ç and z" (Wikipedia, "Mirandese language",
            # Consonants) — i.e. the voiceless member is ⟨c/ç⟩ and the voiced
            # one is ⟨z⟩. The Convenção Ortográfica (1999) likewise uses ⟨ç⟩
            # for /s/ before ⟨a, o, u⟩ and word-finally (⟨lhuç⟩ → [ʎus̻],
            # ⟨fuorça⟩ → [fwɔɾs̻ɐ]). Voicing to [z̻] happens only in external
            # sandhi (before a voiced-initial word), which is sentence-level
            # context this word-scoped rule does not see.
            return self.MWL_ALPHABET_MAP["ç"][0]  # [s̻]
        elif grapheme == "d":
            # Rule: ⟨d⟩ is the stop [d] by default; "Voiced stops /b, d, ɡ/
            # can be lenited as fricatives [β, ð, ɣ]" (Wikipedia, "Mirandese
            # language", Consonants) in weak position — between vowels and
            # after ⟨r⟩ — mirroring the ⟨b⟩/⟨g⟩ rules above/below. The
            # alphabet table gives D = /d/, /ð/ in that order (g2p.json now
            # matches; the map previously listed [ð] first, which inverted
            # the rule: word-initial ⟨d⟩ came out *[ð] and intervocalic ⟨d⟩
            # came out *[d]).
            # d = [ð] between vowels and after r
            if (i > 0 and self._is_vowel(word[i - 1])) and \
                    (i + 1 < len(word) and self._is_vowel(word[i + 1])):
                return self.MWL_ALPHABET_MAP["d"][1]  # [ð] between vowels
            elif i > 0 and word[i - 1].lower() == 'r':
                return self.MWL_ALPHABET_MAP["d"][1]  # [ð] after r
            else:
                return self.MWL_ALPHABET_MAP["d"][0]  # [d] otherwise
        elif grapheme == "e":
            # Rule: words ending in ⟨-r⟩ are stressed on the last syllable
            # (Convenção Ortográfica da Língua Mirandesa 1999, acentuação:
            # oxytone stress for consonant-final words, as in Portuguese),
            # and stressed /e/ is realised [e] while the reduced [ɨ]
            # allophone belongs to unstressed syllables (Wikipedia,
            # "Mirandese language", Vowels: /e/ has allophones [ɛ, e, ɨ]).
            # So ⟨e⟩ in a word-final ⟨-er⟩ (infinitives ⟨chober⟩, ⟨haber⟩)
            # is the stressed close-mid [e].
            if i + 2 == len(word) and word[i + 1].lower() == "r":
                return self.MWL_ALPHABET_MAP["e"][1]  # stressed [e]
            # Elsewhere stress prediction is beyond this rule-based
            # phonemizer; default to the reduced first candidate [ɨ].
            return self.MWL_ALPHABET_MAP["e"][0]
        elif grapheme == "g":
            # Rule: g = [ɣ] between vowels and after r. Before e and i, g = [ʒ].
            # g = [ɡu] in certain words, such as guira, guiron and guirica. g = [gu̯] before a
            if (i > 0 and self._is_vowel(word[i - 1])) and \
                    (i + 1 < len(word) and self._is_vowel(word[i + 1])):
                return self.MWL_ALPHABET_MAP["g"][1]  # [ɣ] between vowels
            elif i > 0 and word[i - 1].lower() == 'r':
                return self.MWL_ALPHABET_MAP["g"][1]  # [ɣ] after r
            elif (i + 1 < len(word) and word[i + 1].lower() in "ei"):
                return self.MWL_ALPHABET_MAP["g"][2]  # [ʒ] before e and i
            # The [ɡu] and [gu̯] rules are word-specific and complex for a simple rule-based system.
            # Defaulting to [g] for other cases.
            else:
                return self.MWL_ALPHABET_MAP["g"][0]
        elif grapheme == "gu":
            # Rule: gu = [ɣ] between vowels and after r
            # Simplified: checking context around 'gu'
            if (i > 0 and self._is_vowel(word[i - 1])) and \
                    (i + 2 < len(word) and self._is_vowel(word[i + 2])):  # Check the character *after* 'u'
                return self.MWL_ALPHABET_MAP["gu"][2]  # [ɣ] between vowels (third element in map)
            elif i > 0 and word[i - 1].lower() == 'r':
                return self.MWL_ALPHABET_MAP["gu"][2]  # [ɣ] after r
            else:
                return self.MWL_ALPHABET_MAP["gu"][0]  # [g] otherwise (first element in map)
        elif grapheme == "i":
            # Rule: i can become glide [j] when preceding or following other vowels.
            is_glide = False
            # Check if 'i' is followed by a vowel
            if i + 1 < len(word) and self._is_vowel(word[i + 1]):
                is_glide = True
            # Check if 'i' is preceded by a vowel
            elif i > 0 and self._is_vowel(word[i - 1]):
                is_glide = True

            if is_glide:
                return self.MWL_ALPHABET_MAP["i"][1]  # [j]
            else:
                return self.MWL_ALPHABET_MAP["i"][0]  # [i]
        elif grapheme == "l":
            # This rule is now handled by the dialect-specific check above for 'sendinese'
            if self.dialect != Dialects.SENDINESE and i == 0:
                return self.MWL_ALPHABET_MAP["l"][1]  # [ʎ] at the beginning of words (non-Sendinese)
            else:
                return self.MWL_ALPHABET_MAP["l"][0]  # [l] elsewhere
        elif grapheme == "lh":
            # This rule is now handled by the dialect-specific check above for 'sendinese'
            # (non-Sendinese only reaches here)
            return self.MWL_ALPHABET_MAP["lh"][0]  # [ʎ] for 'lh' (non-Sendinese)
        elif grapheme == "m":
            # Rule: m is silent before nasalized front vowels, e.g. amportante
            # Default to [m]. Nasalization of preceding vowels is handled by AN, EN, IN, ON, UN.
            return self.MWL_ALPHABET_MAP["m"][0]  # [m]
        elif grapheme == "n":
            # Rule: n = [ŋ] before k, g, q (velar consonants), otherwise [n].
            # Nasalization of preceding vowels is handled by AN, EN, IN, ON, UN.
            if i + 1 < len(word) and word[i + 1].lower() in "kgq":
                return self.MWL_ALPHABET_MAP["n"][1]  # [ŋ]
            else:
                return self.MWL_ALPHABET_MAP["n"][0]  # [n]
        elif grapheme == "o":
            # Rule: o = [u] when unstressed. Also, final -o becomes /u/.
            if i == len(word) - 1:  # If 'o' is the last character in the word
                return self.MWL_ALPHABET_MAP["o"][2]  # [u] (third element in map)
            # This rule requires stress prediction, which is beyond this rule-based phonemizer.
            # Defaulting to the first phoneme [ɔ] for non-final 'o'.
            else:
                return self.MWL_ALPHABET_MAP["o"][0]
        elif grapheme == "qu":
            # Rule: qu = [k] before e and i, and [kṷ] before a and en
            if (i + 2 < len(word) and word[i + 2].lower() in "ei"):
                return self.MWL_ALPHABET_MAP["qu"][0]  # [k] before e and i
            elif (i + 2 < len(word) and word[i + 2].lower() == "a") or \
                    (i + 2 < len(word) - 1 and word[i + 2:i + 4].lower() == "en"):
                return self.MWL_ALPHABET_MAP["qu"][1]  # [kṷ] before a or en
            else:
                return self.MWL_ALPHABET_MAP["qu"][0]  # default to [k]
        elif grapheme == "r":
            # Rule: r = [rr] at the beginning of words and after n
            # The "hard" or "long" R is an alveolar trill /r/. The "soft" or "short" R is an alveolar tap [ɾ].
            # The map has ["ɾ", "r", "rr"]. So "r" is the trill, "ɾ" is the tap.
            if i == 0 or (i > 0 and word[i - 1].lower() == 'n'):  # At beginning or after n
                return self.MWL_ALPHABET_MAP["r"][1]  # [r] (second element in map, the trill)
            else:
                return self.MWL_ALPHABET_MAP["r"][0]  # [ɾ] elsewhere (first element in map, the tap)
        elif grapheme == "s":
            # Rule: s = [s̺] when in initial position and before silent consonants.
            # Between vowels and before voiced consonants, s = [z̺]
            if i == 0 or (i + 1 < len(word) and not self._is_vowel(
                    word[i + 1])):  # Initial or before non-vowel (simplified 'silent consonant')
                return self.MWL_ALPHABET_MAP["s"][0]  # [s̺]
            elif (i > 0 and self._is_vowel(word[i - 1])) and \
                    (i + 1 < len(word) and self._is_voiced_consonant(word[i + 1])):
                return self.MWL_ALPHABET_MAP["s"][1]  # [z̺] between vowels and before voiced consonants
            elif (i > 0 and self._is_vowel(word[i - 1])) and \
                    (i + 1 < len(word) and self._is_vowel(word[i + 1])):
                return self.MWL_ALPHABET_MAP["s"][1]  # [z̺] between vowels
            else:
                return self.MWL_ALPHABET_MAP["s"][0]  # Default [s̺]
        elif grapheme == "u":
            # Rule: u can become glide [w] when preceding or following other vowels.
            is_glide = False
            # Check if 'u' is followed by a vowel
            if i + 1 < len(word) and self._is_vowel(word[i + 1]):
                is_glide = True
            # Check if 'u' is preceded by a vowel
            elif i > 0 and self._is_vowel(word[i - 1]):
                is_glide = True

            if is_glide:
                return self.MWL_ALPHABET_MAP["u"][1]  # [w]
            else:
                return self.MWL_ALPHABET_MAP["u"][0]  # [u]
        elif grapheme == "v":
            return self.MWL_ALPHABET_MAP["v"][0]
        elif grapheme == "w":
            return self.MWL_ALPHABET_MAP["w"][0]
        elif grapheme in ["pl", "kl", "fl", "mn", "ly", "cl", "ll", "nn"]:
            return self.MWL_ALPHABET_MAP[grapheme][0]
        elif grapheme in self.MWL_ALPHABET_MAP:
            # For other graphemes, take the first phoneme in the list as default
            return self.MWL_ALPHABET_MAP[grapheme][0]
        # Fallback for any unmapped character (kept as-is, e.g. bare 'ê')
        return grapheme

    def phonemize_word(self, word: str):
        """Phonemize a single Mirandese word over the shared o2i lattice.

        Segmentation is delegated to the shared
        :class:`~orthography2ipa.phonetok.PhonetokTokenizer`; the Mirandese
        realisation rules run as a :class:`~orthography2ipa.rescorer.LatticeRescorer`
        over the resulting per-grapheme slots. Characters the trie does not
        recognise (e.g. a bare ⟨ê⟩) are passed through unchanged, as before.
        """
        word = word.lower()
        if word == "l":
            return "l̩"

        self._word = word
        tokens = self._tok.tokenize(word)

        # grapheme slots -> rescore over the shared lattice
        g_tokens = [t for t in tokens if t.kind == TokenKind.GRAPHEME]
        contexts = flat_contexts(g_tokens)
        slots = [
            SegmentSlot(
                grapheme=t.grapheme,
                span=(t.position, t.position + t.length),
                candidates=(Candidate(self.MWL_ALPHABET_MAP.get(t.grapheme, [t.grapheme])[0], 0.0),),
            )
            for t in g_tokens
        ]
        rescored = apply_rescorers(
            slots, contexts, self._rescorers,
            syll_for_token=list(range(len(g_tokens))),
            stressed_syll_idx=None,
        )

        # stitch grapheme IPA back together in surface order, passing
        # non-grapheme (unrecognised) tokens through unchanged
        rescored_iter = iter(rescored)
        parts = []
        for t in tokens:
            if t.kind == TokenKind.GRAPHEME:
                s = next(rescored_iter)
                if s.candidates and s.top.ipa:
                    parts.append(s.top.ipa)
            else:
                parts.append(t.grapheme)
        phonemized = "".join(parts)
        return self._post_process(phonemized)

    def phonemize_sentence(self,  text: str):
        text = text.replace("-", " ")
        words = re.findall(r"\b\w+\b|[\W_]+", text)  # Split by words and keep punctuation/spaces
        phonemized_parts = []
        for word_or_punc in words:
            if word_or_punc.isalpha():
                phonemized_parts.append(
                    self.phonemize_word(word_or_punc))
            else:
                phonemized_parts.append(word_or_punc)  # Keep punctuation and spaces as is
        return "".join(phonemized_parts)

    # -------------------------
    # Phonemizer interface
    # -------------------------
    def phonemize(self, word: str, lookup_word: bool = True) -> str:
        """Phonemize a single Mirandese word via the lattice + correction rules."""
        if lookup_word and word.lower() in self.GOLD:
            return self.GOLD[word.lower()]
        return self.phonemize_word(word)


if __name__ == "__main__":

    pho = OrthographyRulesMWL()

    stats = pho.evaluate_on_gold(limit=None, detailed=False, show_changes=False)

    per = stats['per']
    per_no_stress = stats['per_no_stress']

    print("\n" + "=" * 50)
    print("      Mirandese Phonemizer Rule Evaluation")
    print("=" * 50)
    print(f"Total Words Evaluated: {stats['counts']}\n")

    print("## Phoneme Error Rate (PER, Full IPA Match, includes stress)")
    print(f"PER:    {per:.2%}")

    print("\n## Phoneme Error Rate (PER, Stress-Agnostic)")
    print(f"PER:    {per_no_stress:.2%}")

    print("\n--- Incorrectly Phonemized Words (Full IPA Match ED > 0) ---")
    wrong_words = stats.get("details", [])

    if wrong_words:
        print(f"Total Incorrect: {len(wrong_words)} words\n")
        print(f"{'Word':<20} | {'Gold':<15} | {'Phonemized':<15} | {'ED After':<8}")
        print("-" * 75)
        for d in wrong_words:
            print(
                f"{d['word']:<20} | {d['gold']:<15} | {d['phonemes']:<15} | {d['ed']:<8}")
    else:
        print("All words achieved an exact match (100% Accuracy)!")
