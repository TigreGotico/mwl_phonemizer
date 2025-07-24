import re
import string
"""
reference phonetic info from wikipedia:

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

Portuguese spelling still distinguishes all seven and is identical to Mirandese spelling in this respect, but in pronunciation, Portuguese has reduced them to four /s, z, ʃ, ʒ/ except in northern hinterland European Portuguese dialects, including those of the area that Mirandese is spoken. Northern/central Peninsular Spanish has also reduced them to four but in quite a different way: /t͡ʃ, θ, s̺, x/. Western Andalusian Spanish and Latin American Spanish have further reduced them to three: /t͡ʃ, s̻, x/.

- Retention of the initial /f/ from Latin, like nearly all dialects of Western Romance (the major maverick being Spanish, where /f/> /h/ > ∅).
- As in Leonese and Galician-Portuguese, the Latin initial consonant clusters /pl/, /kl/, /fl/ evolve into /t͡ʃ/.
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

- the laminal dental sibilants correspond to Portuguese /s, z/. These are spelled c/ç and z. The corresponding alveolar sibilants are apical and are spelled s(s) and s. Furthermore, there is an additional palatal affricate /t͡ʃ/ ch that is distinct from the fricative /ʃ/, spelled x. The voiced /ʒ/ is spelled j or g, as in Portuguese. Standard Portuguese has reduced all those sounds to just four fricatives: /s, z, ʃ, ʒ/.
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


# Mapping to convert graphemes to phonemes
MWL_ALPHABET_MAP = {
    "a": ["a", "ä", "ɐ"],
    "á": ["ɐ̃", "a", ],
    "ai": ["aj"],
    "an": ["ɐ̃ŋ"],
    "b": ["b", "β"],  # - b = [β] between vowels and after voiced consonants
    "c": ["k", "s̻", "s", "z"],  # - c = [s̻] before e or i, [k] elsewhere
    "ç": ["z̻"],  # - ç = [z̻] before words starting with voiced consonants
    "ch": ["t͡ʃ"],
    "d": ["d", "ð"],  # - d = [ð] between vowels and after r
    "e": ["e", "ɛ", "ɨ", "ɨ̃"],  # - e = [ɨ/ɨ̃] before stressed syllables
    "en": ["ẽŋ", "ɨ̃"],
    "é": ["ɛ"],
    "ei": ["ej"],
    "eu": ["ew"],
    "éu": ["ɛw"],
    "f": ["f"],
    "g": ["g", "ɣ", "ʒ", "ɡu", "gu̯"],
    # - g = [ɣ] between vowels and after r. Before e and i, g = [ʒ]. g = [ɡu] in certain words, such as guira, guiron and guirica. g = [gu̯] before a
    "gu": ["g", "gu", "ɣ"],  # - gu = [ɣ] between vowels and after r
    "h": [""],  # silent
    "i": ["i", "j"],
    "in": ["ĩŋ", "ɨ̃j̃"],  # ɨ̃j̃ (Sendinese dialect)
    "í": ["i"],
    "ia": ["ja"],
    "iê": ["je", "jê"],
    "iu": ["iw"],
    "j": ["ʒ"],
    "k": ["k"],  # - k is only used in loanwords from other languages
    "l": ["l", "ʎ", "ɫ"],  # - l = [ʎ] at the beginning of words, and [l] elsewhere
    "lh": ["ʎ"],
    "m": ["m"],  # - m is silent before nasalized front vowels, e.g. amportante
    "n": ["n", "ŋ"], # - n is silent before consonants and at the end of words before nasalized front vowels, e.g. lhéngua, sons, quien
    "nh": ["ɲ"],
    "o": ["ɔ", "o", "u", "ʊ"],  # - o = [u] when unstressed
    "on": ["õŋ"],
    "ó": ["ɔ"],
    "oi": ["oj"],
    "ói": ["ɔj"],
    "ou": ["ow"],
    "p": ["p"],
    "q": ["k"],
    "qu": ["k", "kṷ"],  # - qu = [k] before e and i, and [kṷ] before a and en
    "r": ["ɾ", "r", "rr"],  # - r = [rr] at the beginning of words and after n
    "rr": ["r"],
    "s": ["s̺", "z̺"],
    # - s = [s̺] when in initial position and before silent consonants. Between vowels and before voiced consonants, s = [z̺]
    "ss": ["s̺"],
    "t": ["t"],
    "u": ["u", "w", "ũ"],
    "un": ["ũŋ", "ʊ̃ŋ"],
    "ú": ["u"],
    "ũ": ["ũ"],
    "ua": ["wa"],
    "ui": ["uj"],
    "uo": ["wo", "u"],
    "v": ["b", "v"],  # - v is only used in loanwords from other languages
    "w": ["w", "b", "β"],  # - w is only used in loanwords from other languages
    "x": ["ʃ"],
    "y": ["j"],
    "z": ["z"],
    # --- Added for improvements ---
    "mn": ["m"],  # Proto-Romance -mn- becomes /m/
    "pl": ["t͡ʃ"], # Latin initial consonant cluster
    "kl": ["t͡ʃ"], # Latin initial consonant cluster
    "fl": ["t͡ʃ"], # Latin initial consonant cluster
    "ly": ["ʎ"], # Proto-Romance medial cluster -ly- (handled as a special grapheme)
    "cl": ["ʎ"], # Proto-Romance medial cluster -cl- (handled as a special grapheme)
    "ll": ["ʎ"], # Palatalization of double l
    "nn": ["ɲ"], # Palatalization of double n
}

# direct word look ups
# https://en.wiktionary.org/wiki/Category:Mirandese_terms_with_IPA_pronunciation
CENTRAL_DICT = {
    "hai": "aj",
    "más": "mas̺",
    "mais": "majs̺",
    "alhá": "ɐˈʎa",
    "deimingo": "dejˈmĩ.gʊ",
    "abandono": "a.bɐ̃ˈdo.nu",
    "adbertido": "ɐ.dbɨɾˈti.du",
    "adulto": "ɐˈdul.tu",
    "afamado": "ɐ.fɐˈma.du",
    "afeito": "ɐˈfej.tʊ",
    "afelhado": "ɐ.fɨˈʎa.du",
    "alternatibo": "al.tɨɾ.nɐˈti.bu",
    "amarielho": "ɐ.mɐˈɾjɛ.ʎu",
    "ambesible": "ɐ̃.bɨˈs̺i.blɨ",
    "amouchado": "amowˈt͡ʃaðu",
    "amportante": "ɐ̃.puɾˈtɐ̃.tɨ",
    "ampossible": "ɐ̃.puˈsi.blɨ",
    "ampressionante": "ɐ̃.pɾɨ.sjuˈnɐ̃.tɨ",
    "anchir": "ɐ̃.ˈt͡ʃiɾ",
    "antender": "ɐ̃.tɨ̃.ˈdeɾ",
    "arena": "ɐˈɾenɐ",
    "açpuis": "ɐsˈpujs̺",
    "berde": "ˈveɾ.dɨ",
    "besible": "bɨˈz̺i.blɨ",
    "bexanar": "bɨ.ʃɐ.ˈnaɾ",
    "bibal": "bi.ˈβaɫ",
    "bielho": "bjɛʎu",
    "biolento": "bjuˈlẽ.tu",
    "biúba": "biˈuβɐ",
    "brabo": "bɾa.bu",
    "branco": "bɾɐ̃.ku",
    "buono": "bwo.nu",
    "burmeilho": "buɾˈmɐj.ʎu",
    "bíblico": "bi.bli.ku",
    "cabresto": "kɐˈbɾeʃ.tu",
    "canhona": "kɐˈɲo.nɐ",
    "cheno": "ˈt͡ʃe.nu",
    "chober": "t͡ʃuˈβeɾ",
    "ciguonha": "s̻i.ˈɣwo.ɲɐ",
    "cul": "kul",
    "dafeito": "ðɐˈfej.tʊ",
    "defrente": "dɨˈfɾẽ.tɨ",
    "defícel": "dɨˈfi.sɛl",
    "drento": "ˈdɾẽtu",
    "eigual": "ɐjˈɡwal",
    "era": "ˈɛ.ɾɐ",
    "eras": "ˈɛ.ɾɐs̺",
    "feliç": "fɨˈlis̻",
    "fierro": "ˈfjɛ.ru",
    "francesa": "fɾɐ̃ˈsɛ.zɐ",
    "francesas": "fɾɐ̃ˈsɛ.zɐs̺",
    "franceses": "fɾɐ̃ˈsɛ.zɨs̺",
    "francés": "fɾɐ̃ˈsɛs̺",
    "fui": "fuj",
    "fumos": "ˈfu.mus̺",
    "fuogo": "fwo.ɣʊ",
    "fuonte": "ˈfwõ.tɨ",
    "fuorte": "ˈfwɔɾ.tɨ",
    "fuortemente": "fwɔɾ.tɨˈmẽ.tɨ",
    "fuorça": "ˈfwɔɾ.s̻ɐ",
    "fuste": "ˈfus̺.tɨ",
    "fácele": "ˈfa.sɨ.lɨ",
    "guapo": "ˈɡwa.pu",
    "haber": "ɐˈβeɾ",
    "houmano": "o(w)ˈmɐ.nu",
    "i": "i",
    "l": "l̩",
    "lhabrar": "ʎɐˈbɾaɾ(i)",
    "lhimpo": "ˈʎĩ.pʊ",
    "lhobo": "ˈʎo.bʊ",
    "lhuç": "ˈʎus̻",
    "lhéngua": "ˈʎɛ̃ɡwɐ",
    "luç": "ˈʎus̻",
    "macado": "mɐˈka.du",
    "maias": "ˈmajɐs̺",
    "mirandés": "mi.ɾɐ̃ˈdes̺",
    "molineiro": "mʊ.li.ˈnei̯.rʊ",
    "molino": "muˈlinu",
    "muola": "ˈmu̯olɐ",
    "ne l": "nɨl",
    "neçairo": "nɨˈsaj.ɾu",
    "nuobo": "ˈnwo.βʊ",
    "nó": "ˈnɔ",
    "onte": "ˈõ.tɨ",
    "oucidental": "ow.s̻i.dẽˈtal",
    "oufecialmente": "o(w).fɨˌsjalˈmẽ.tɨ",
    "ourdenhar": "ou̯ɾdɨˈɲaɾ",
    "oureginal": "ow.ɾɨ.ʒiˈnal",
    "ourganizaçon": "ou̯r.ɡɐ.ni.zɐ.ˈsõ",
    "ouropeu": "ow.ɾuˈpew",
    "ourriêta": "ˈowrjetɐ",
    "paxarina": "pɐʃɐˈɾinɐ",
    "pequeinho": "pɨˈkɐi.ɲu",
    "piranha": "piˈra.ɲɐ",
    "puis": "ˈpujs̺",
    "pul": "ˈpul",
    "puorta": "ˈpwoɾtɐ",
    "purmeiro": "puɾˈmɐj.ɾu",
    "quaije": "ˈkwaj.ʒɨ",
    "quando": "ˈkwɐ̃.du",
    "quelobrinas": "kɨluˈbrinas̺",
    "quemun": "kɨˈmun",
    "rabielho": "rɐ.ˈβje.ʎu",
    "rico": "ˈri.ku",
    "salir": "s̺ɐˈliɾ",
    "screbir": "s̺krɨˈβiɾ",
    "segar": "s̺ɨˈɣaɾ",
    "sendo": "ˈsẽ.du",
    "ser": "ˈseɾ",
    "sida": "ˈsi.dɐ",
    "sidas": "ˈsi.dɐs̺",
    "sido": "ˈsi.du",
    "sidos": "ˈsi.dus̺",
    "simple": "ˈs̺ĩ.plɨ",
    "sobrino": "s̺uˈbɾinu",
    "sodes": "ˈso.dɨs̺",
    "somos": "ˈso.mus̺",
    "son": "ˈsõ",
    "sou": "ˈso(w)",
    "spanha": "ˈs̺pɐ.ɲɐ",
    "squierdo": "ˈs̺kjeɾ.du",
    "sós": "ˈs̺ɔs̺",
    "talbeç": "talˈbes",
    "tamien": "tɐˈmjẽ",
    "tascar": "tɐs̺.ˈkaɾ",
    "tener": "tɨˈneɾ",
    "trasdonte": "ˈtɾɐz̺dõtɨ",
    "trasdontonte": "ˈtɾɐz̺dõtõtɨ",
    "ye": "ˈje",
    "you": "jow",
    "yê": "ˈje",
    "zastre": "ˈzas̺tɾɨ",
    "zeigual": "zɐjˈɡwal",
    "zenhar": "zɨˈɲaɾ",
    "áfrica": "ˈafɾikɐ",
    "çcansar": "skɐ̃ˈs̺aɾ",
    "çcrebir": "skɾɨˈβiɾ",
    "çcriçon": "skɾiˈsõ",
    "çtinto": "ˈstĩ.tu",
    "érades": "ˈɛ.ɾɐ.dɨs̺",
    "éramos": "ˈɛ.ɾɐ.mus̺",
    "éran": "ˈɛ.ɾɐn",
    "ũ": "ˈũ",
    "ũa": "ˈũ.ŋɐ",
    "ua": "ˈũ.ŋɐ"
}
RAIANO_DICT = {
    "fuogo": "fwo.ʊ",
    "l": "ɐl",
}
SENDINESE_DICT = {
    "fuogo": "fu.ɣʊ",
    "alhá": "ɐˈla",
    "ye": "(ˈj)i",
    "deimingo": "dɨˈmʊ̃j̃.gʊ",
    "demingo": "dɨˈmʊ̃j̃.gʊ",
    "l": "lʊ",
    "lhobo": "ˈlo.bʊ",
    "lhuç": "ˈlus̻",
    "luç": "ˈlus̻",
    "puorta": "ˈpuɾtɐ",
    "yê": "ˈji",
}

_vowels = "aeiouáéíóúäɐɛɨɪɔʊ"  # Extended set of vowels for context checking
_voiced_consonants = "bdgjlmnrvz"  # Approximated list of voiced consonants


def _is_vowel(char):
    """Checks if a character is a vowel."""
    return char.lower() in _vowels


def _is_voiced_consonant(char):
    """Checks if a character is a voiced consonant."""
    return char.lower() in _voiced_consonants


def _post_process(phonemized: str,
                   keep_optional_phones=True,
                   keep_stress_marks=False) -> str:
    if not keep_stress_marks:
        phonemized = (phonemized.
                      replace("ˈ", "").
                      replace(".", ""))
    if keep_optional_phones:
        # just drop parentheses
        phonemized = (phonemized.
                      replace("(", "").
                      replace(")", ""))
    else:
        # Remove optional phonemes inside parentheses
        # This regex finds any content within parentheses and replaces the whole match with an empty string
        phonemized = re.sub(r'\([^)]*\)', '', phonemized)
    return phonemized

def phonemize_word(word, dialect="central",
                   word_lookup=True,
                   keep_optional_phones=True,
                   keep_stress_marks=False):
    """
    Phonemizes a single Mirandese word based on the provided mapping and rules,
    with support for dialectal variations.

    Args:
        word (str): The word to phonemize.
        dialect (str): The dialect to use for phonemization (e.g., "central", "sendinese").
    """
    word = word.lower()
    if word_lookup:
        if dialect == "sendinese":
            if word in SENDINESE_DICT:
                phonemized = SENDINESE_DICT[word]
                return _post_process(phonemized, keep_optional_phones, keep_stress_marks)
        elif dialect == "raiano":
            if word in RAIANO_DICT:
                phonemized = RAIANO_DICT[word]
                return _post_process(phonemized, keep_optional_phones, keep_stress_marks)

        if word in CENTRAL_DICT:
            phonemized = CENTRAL_DICT[word]
            return _post_process(phonemized, keep_optional_phones, keep_stress_marks)

    phonemes = []
    i = 0
    while i < len(word):
        matched = False

        # Try to match multi-character graphemes first (longest first)
        # This ensures 'ch' is matched before 'c', 'lh' before 'l', etc.
        # Also handles new clusters like 'pl', 'kl', 'fl', 'mn', 'ly', 'cl', 'll', 'nn'
        for length in sorted([len(g) for g in MWL_ALPHABET_MAP.keys()], reverse=True):
            if i + length <= len(word):
                grapheme = word[i:i + length].lower()

                # Handle dialectal variations for 'l' and 'lh'
                if dialect == "sendinese":
                    if grapheme == "lh":
                        phonemes.append(MWL_ALPHABET_MAP["l"][0])  # 'lh' becomes [l] in Sendinese
                        i += length
                        matched = True
                        break
                    elif grapheme == "l" and i == 0:  # Initial 'l' in Sendinese remains [l]
                        phonemes.append(MWL_ALPHABET_MAP["l"][0])
                        i += length
                        matched = True
                        break

                if grapheme in MWL_ALPHABET_MAP:
                    # Apply specific rules for graphemes based on context
                    if grapheme == "b":
                        # Rule: b = [β] between vowels and after voiced consonants
                        if (i > 0 and _is_vowel(word[i - 1])) and \
                                (i + 1 < len(word) and _is_vowel(word[i + 1])):
                            phonemes.append(MWL_ALPHABET_MAP["b"][1])  # [β] between vowels
                        elif i > 0 and _is_voiced_consonant(word[i - 1]):
                            phonemes.append(MWL_ALPHABET_MAP["b"][1])  # [β] after voiced consonants
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["b"][0])  # [b] otherwise
                    elif grapheme == "c":
                        # Rule: c = [s̻] before e or i, [k] elsewhere
                        if (i + 1 < len(word) and word[i + 1].lower() in "ei"):
                            phonemes.append(MWL_ALPHABET_MAP["c"][1])  # [s̻] before e or i (second element in map)
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["c"][0])  # [k] elsewhere (first element in map)
                    elif grapheme == "ç":
                        # Rule: ç = [z̻] before words starting with voiced consonants
                        # This rule is tricky without full word context (e.g., "words starting with voiced consonants")
                        # For now, a simplified interpretation: if followed by a voiced consonant within the word.
                        # A more accurate implementation would require sentence-level context.
                        if i + 1 < len(word) and _is_voiced_consonant(word[i + 1]):
                            phonemes.append(MWL_ALPHABET_MAP["ç"][0])  # [z̻]
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["ç"][0])  # Default to [z̻]
                    elif grapheme == "d":
                        # Rule: d = [ð] between vowels and after r
                        if (i > 0 and _is_vowel(word[i - 1])) and \
                                (i + 1 < len(word) and _is_vowel(word[i + 1])):
                            phonemes.append(MWL_ALPHABET_MAP["d"][1])  # [ð] between vowels
                        elif i > 0 and word[i - 1].lower() == 'r':
                            phonemes.append(MWL_ALPHABET_MAP["d"][1])  # [ð] after r
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["d"][0])  # [d] otherwise
                    elif grapheme == "e":
                        # Rule: e = [ɨ/ɨ̃] before stressed syllables
                        # This rule requires stress prediction, which is beyond this rule-based phonemizer.
                        # Defaulting to the first phoneme [e].
                        phonemes.append(MWL_ALPHABET_MAP["e"][0])
                    elif grapheme == "g":
                        # Rule: g = [ɣ] between vowels and after r. Before e and i, g = [ʒ].
                        # g = [ɡu] in certain words, such as guira, guiron and guirica. g = [gu̯] before a
                        if (i > 0 and _is_vowel(word[i - 1])) and \
                                (i + 1 < len(word) and _is_vowel(word[i + 1])):
                            phonemes.append(MWL_ALPHABET_MAP["g"][1])  # [ɣ] between vowels
                        elif i > 0 and word[i - 1].lower() == 'r':
                            phonemes.append(MWL_ALPHABET_MAP["g"][1])  # [ɣ] after r
                        elif (i + 1 < len(word) and word[i + 1].lower() in "ei"):
                            phonemes.append(MWL_ALPHABET_MAP["g"][2])  # [ʒ] before e and i
                        # The [ɡu] and [gu̯] rules are word-specific and complex for a simple rule-based system.
                        # Defaulting to [g] for other cases.
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["g"][0])
                    elif grapheme == "gu":
                        # Rule: gu = [ɣ] between vowels and after r
                        # Simplified: checking context around 'gu'
                        if (i > 0 and _is_vowel(word[i - 1])) and \
                                (i + 2 < len(word) and _is_vowel(word[i + 2])):  # Check the character *after* 'u'
                            phonemes.append(MWL_ALPHABET_MAP["gu"][2])  # [ɣ] between vowels (third element in map)
                        elif i > 0 and word[i - 1].lower() == 'r':
                            phonemes.append(MWL_ALPHABET_MAP["gu"][2])  # [ɣ] after r
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["gu"][0])  # [g] otherwise (first element in map)
                    elif grapheme == "i":
                        # Rule: i can become glide [j] when preceding or following other vowels.
                        is_glide = False
                        # Check if 'i' is followed by a vowel
                        if i + 1 < len(word) and _is_vowel(word[i + 1]):
                            is_glide = True
                        # Check if 'i' is preceded by a vowel
                        elif i > 0 and _is_vowel(word[i - 1]):
                            is_glide = True

                        if is_glide:
                            phonemes.append(MWL_ALPHABET_MAP["i"][1])  # [j]
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["i"][0])  # [i]
                    elif grapheme == "l":
                        # This rule is now handled by the dialect-specific check above for 'sendinese'
                        if dialect != "sendinese" and i == 0:
                            phonemes.append(MWL_ALPHABET_MAP["l"][1])  # [ʎ] at the beginning of words (non-Sendinese)
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["l"][0])  # [l] elsewhere
                    elif grapheme == "lh":
                        # This rule is now handled by the dialect-specific check above for 'sendinese'
                        if dialect != "sendinese":
                            phonemes.append(MWL_ALPHABET_MAP["lh"][0])  # [ʎ] for 'lh' (non-Sendinese)
                        # else: handled by the 'sendinese' block above
                    elif grapheme == "m":
                        # Rule: m is silent before nasalized front vowels, e.g. amportante
                        # Default to [m]. Nasalization of preceding vowels is handled by AN, EN, IN, ON, UN.
                        phonemes.append(MWL_ALPHABET_MAP["m"][0])  # [m]
                    elif grapheme == "n":
                        # Rule: n = [ŋ] before k, g, q (velar consonants), otherwise [n].
                        # Nasalization of preceding vowels is handled by AN, EN, IN, ON, UN.
                        if i + 1 < len(word) and word[i + 1].lower() in "kgq":
                            phonemes.append(MWL_ALPHABET_MAP["n"][1]) # [ŋ]
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["n"][0])  # [n]
                    elif grapheme == "o":
                        # Rule: o = [u] when unstressed. Also, final -o becomes /u/.
                        if i == len(word) - 1:  # If 'o' is the last character in the word
                            phonemes.append(MWL_ALPHABET_MAP["o"][2])  # [u] (third element in map)
                        # This rule requires stress prediction, which is beyond this rule-based phonemizer.
                        # Defaulting to the first phoneme [ɔ] for non-final 'o'.
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["o"][0])
                    elif grapheme == "qu":
                        # Rule: qu = [k] before e and i, and [kṷ] before a and en
                        if (i + 2 < len(word) and word[i + 2].lower() in "ei"):
                            phonemes.append(MWL_ALPHABET_MAP["qu"][0])  # [k] before e and i
                        elif (i + 2 < len(word) and word[i + 2].lower() == "a") or \
                                (i + 2 < len(word) - 1 and word[i + 2:i + 4].lower() == "en"):
                            phonemes.append(MWL_ALPHABET_MAP["qu"][1])  # [kṷ] before a or en
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["qu"][0])  # default to [k]
                    elif grapheme == "r":
                        # Rule: r = [rr] at the beginning of words and after n
                        # The "hard" or "long" R is an alveolar trill /r/. The "soft" or "short" R is an alveolar tap [ɾ].
                        # The map has ["ɾ", "r", "rr"]. So "r" is the trill, "ɾ" is the tap.
                        if i == 0 or (i > 0 and word[i - 1].lower() == 'n'):  # At beginning or after n
                            phonemes.append(MWL_ALPHABET_MAP["r"][1])  # [r] (second element in map, the trill)
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["r"][0])  # [ɾ] elsewhere (first element in map, the tap)
                    elif grapheme == "s":
                        # Rule: s = [s̺] when in initial position and before silent consonants.
                        # Between vowels and before voiced consonants, s = [z̺]
                        if i == 0 or (i + 1 < len(word) and not _is_vowel(
                                word[i + 1])):  # Initial or before non-vowel (simplified 'silent consonant')
                            phonemes.append(MWL_ALPHABET_MAP["s"][0])  # [s̺]
                        elif (i > 0 and _is_vowel(word[i - 1])) and \
                                (i + 1 < len(word) and _is_voiced_consonant(word[i + 1])):
                            phonemes.append(
                                MWL_ALPHABET_MAP["s"][1])  # [z̺] between vowels and before voiced consonants
                        elif (i > 0 and _is_vowel(word[i - 1])) and \
                                (i + 1 < len(word) and _is_vowel(word[i + 1])):
                            phonemes.append(MWL_ALPHABET_MAP["s"][1])  # [z̺] between vowels
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["s"][0])  # Default [s̺]
                    elif grapheme == "u":
                        # Rule: u can become glide [w] when preceding or following other vowels.
                        is_glide = False
                        # Check if 'u' is followed by a vowel
                        if i + 1 < len(word) and _is_vowel(word[i + 1]):
                            is_glide = True
                        # Check if 'u' is preceded by a vowel
                        elif i > 0 and _is_vowel(word[i - 1]):
                            is_glide = True

                        if is_glide:
                            phonemes.append(MWL_ALPHABET_MAP["u"][1])  # [w]
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["u"][0])  # [u]
                    # For v and w, the map has multiple options, but Wikipedia implies primarily for loanwords.
                    # Sticking to the first phoneme in the map as default for simplicity.
                    elif grapheme == "v":
                        phonemes.append(MWL_ALPHABET_MAP["v"][0])
                    elif grapheme == "w":
                        phonemes.append(MWL_ALPHABET_MAP["w"][0])
                    # --- cluster rules ---
                    elif grapheme in ["pl", "kl", "fl", "mn", "ly", "cl", "ll", "nn"]:
                        phonemes.append(MWL_ALPHABET_MAP[grapheme][0])
                    else:
                        # For other graphemes, take the first phoneme in the list as default
                        phonemes.append(MWL_ALPHABET_MAP[grapheme][0])

                    i += length
                    matched = True
                    break  # Break from the inner loop (grapheme lengths) once a match is found

        # If no multi-character grapheme matched, try single character
        if not matched:
            if word[i].lower() in MWL_ALPHABET_MAP:
                phonemes.append(MWL_ALPHABET_MAP[word[i].lower()][0])
            elif word[i] in string.punctuation + string.whitespace:
                phonemes.append(word[i])  # Keep punctuation as is
            else:
                phonemes.append(word[i])  # Fallback for any unmapped character
            i += 1
    phonemized = "".join(phonemes)
    return _post_process(phonemized, keep_optional_phones, keep_stress_marks)


def mirandese_phonemizer(text, dialect="central", word_lookup=True, keep_optional_phones=True, keep_stress_marks=False):
    """
    Phonemizes a Mirandese text, separating words with '|' and preserving punctuation.
    Supports different dialects.

    Args:
        text (str): The input Mirandese text.
        dialect (str): The dialect to use for phonemization (e.g., "central", "sendinese").
        word_lookup (bool): Whether to use the direct word lookup dictionaries.
        keep_optional_phones (bool): If True, keeps optional phonemes in parentheses. If False, removes them.
        keep_stress_marks (bool): If True, keeps stress marks and syllable dots. If False, removes them.
    """
    text = text.replace("-", " ")
    words = re.findall(r"\b\w+\b|[\W_]+", text)  # Split by words and keep punctuation/spaces
    phonemized_parts = []
    for word_or_punc in words:
        if word_or_punc.isalpha():
            phonemized_parts.append(phonemize_word(word_or_punc, dialect, word_lookup, keep_optional_phones, keep_stress_marks))
        else:
            phonemized_parts.append(word_or_punc)  # Keep punctuation and spaces as is
    return "".join(phonemized_parts)


if __name__ == "__main__":
    sample_texts = [
        "Muitas lhénguas ténen proua de ls sous pergaminos antigos, de la lhiteratura screbida hai cientos d'anhos i de scritores hai muito afamados, hoije bandeiras dessas lhénguas. Mas outras hai que nun puoden tener proua de nada desso, cumo ye l causo de la lhéngua mirandesa.",
        "Todos ls seres houmanos nácen lhibres i eiguales an honra i an dreitos. Dotados de rezon i de cuncéncia, dében de se dar bien uns culs outros i cumo armano",
        """Quien dirie qu'antre ls matos eiriçados
    Las ourriêtas i ls rius d'esta tiêrra,
    Bibie, cumo l chaugarço de la siêrra,
    Ua lhéngua de sons tan bariados?

    Mostre-se i fale-s' essa lhéngua filha
    D'un pobo que ten neilha l choro i l canto!
    Nada por ciêrto mos cautiba tanto
    Cumo la form' an que l'eideia brilha.

    Zgraçiado d'aquel, qu'abandonando
    La patri' an que naciu, la casa i l huôrto.
    Tamien se squeçe de la fala! Quando
    L furdes ber, talbéç que stéia muôrto!"""
    ]

    for text in sample_texts:
        print(f"Original: {text}")
        print(f"Phonemized: {mirandese_phonemizer(text)}\n")

    # Original: Muitas lhénguas ténen proua de ls sous pergaminos antigos, de la lhiteratura screbida hai cientos d'anhos i de scritores hai muito afamados, hoije bandeiras dessas lhénguas. Mas outras hai que nun puoden tener proua de nada desso, cumo ye l causo de la lhéngua mirandesa.
    # Phonemized: mujtas̺ ʎɛ~gas̺ tɛnẽŋ pɾowa dɛ ʎs̺ s̺ows̺ pɛɾɣamĩŋɔs̺ ɐ̃ŋtiɣɔs̺, dɛ ʎa ʎitɛɾatuɾa s̺kɾɛβiða aj s̻iẽŋtɔs̺ d'ɐ̃ŋɔs̺ i dɛ s̺kɾitɔɾɛs̺ aj mujtɔ afamaðɔs̺, ojʒɛ bɐ̃ŋdejɾas̺ dɛs̺as̺ ʎɛ~gas̺. mas̺ owtɾas̺ aj kɛ nũŋ pwoðẽŋ tẽŋɛɾ pɾowa dɛ naða dɛs̺ɔ, kumɔ jɛ ʎ kauz̺ɔ dɛ ʎa ʎɛ~ga miɾɐ̃ŋdɛz̺a.
    #
    # Original: Todos ls seres houmanos nácen lhibres i eiguales an honra i an dreitos. Dotados de rezon i de cuncéncia, dében de se dar bien uns culs outros i cumo armano
    # Phonemized: tɔðɔs̺ ʎs̺ s̺ɛɾɛs̺ owmɐ̃ŋɔs̺ nas̻ẽŋ ʎibɾɛs̺ i ejɣalɛs̺ ɐ̃ŋ õŋrra i ɐ̃ŋ dɾejtɔs̺. dɔtaðɔs̺ dɛ rrɛzõŋ i dɛ kũŋkɛ~s̻ja, dɛβẽŋ dɛ s̺ɛ daɾ biẽŋ ũŋs̺ kuls̺ owtɾɔs̺ i kumɔ aɾmɐ̃ŋɔ
    #
    # Original: Quien dirie qu'antre ls matos eiriçados
    #     Las ourriêtas i ls rius d'esta tiêrra,
    #     Bibie, cumo l chaugarço de la siêrra,
    #     Ua lhéngua de sons tan bariados?
    #
    #     Mostre-se i fale-s' essa lhéngua filha
    #     D'un pobo que ten neilha l choro i l canto!
    #     Nada por ciêrto mos cautiba tanto
    #     Cumo la form' an que l'eideia brilha.
    #
    #     Zgraçiado d'aquel, qu'abandonando
    #     La patri' an que naciu, la casa i l huôrto.
    #     Tamien se squeçe de la fala! Quando
    #     L furdes ber, talbéç que stéia muôrto!
    # Phonemized: kiẽŋ diɾiɛ k'ɐ̃ŋtɾɛ ʎs̺ matɔs̺ ejɾiz̻aðɔs̺
    #     ʎas̺ owrjetas̺ i ʎs̺ rriws̺ d'ɛs̺ta tjera,
    #     biβiɛ, kumɔ ʎ t͡ʃauɣaɾz̻ɔ dɛ ʎa s̺jera,
    #     wa ʎɛ~ga dɛ s̺õŋs̺ tɐ̃ŋ baɾjaðɔs̺?
    #
    #     mɔs̺tɾɛ-s̺ɛ i falɛ-s̺' ɛs̺a ʎɛ~ga fiʎa
    #     d'ũŋ pɔβɔ kɛ tẽŋ nejʎa ʎ t͡ʃɔɾɔ i ʎ kɐ̃ŋtɔ!
    #     naða pɔɾ s̻jeɾtɔ mɔs̺ kautiβa tɐ̃ŋtɔ
    #     kumɔ ʎa fɔɾm' ɐ̃ŋ kɛ ʎ'ejðeja bɾiʎa.
    #
    #     zgɾaz̻jaðɔ d'akɛl, k'aβɐ̃ŋdõŋɐ̃ŋdɔ
    #     ʎa patɾi' ɐ̃ŋ kɛ nas̻iw, ʎa kaz̺a i ʎ uɾtɔ.
    #     tamiẽŋ s̺ɛ s̺kɛz̻ɛ dɛ ʎa fala! kṷɐ̃ŋdɔ
    #     ʎ fuɾðɛs̺ bɛɾ, talβɛz̻ kɛ s̺tɛja muɾtɔ!


    print("\n--- Dialect-Specific Examples from Wikipedia Table ---")

    test_sentence = "Hai más fuogo alhá, i ye deimingo!"
    print(f"Original: {test_sentence}")

    # Raiano Dialect
    print("\n--- Raiano ---")
    print(f"Expected IPA: ˈaj ˈmas̺ ˈfwo.ɣʊ/u/ˈfwo.ʊ/u ɐˈʎa, ˈi ˈje dejˈmĩ.gʲʊ/u\n")
    print(f"Phonemized (Raiano, with optional, using dict): {mirandese_phonemizer(test_sentence, dialect='raiano', word_lookup=True,  keep_optional_phones=True)}")
    print(f"Phonemized (Raiano, no optional, using dict): {mirandese_phonemizer(test_sentence, dialect='raiano', word_lookup=True,keep_optional_phones=False)}")
    print(f"Phonemized (Raiano, no dict): {mirandese_phonemizer(test_sentence, dialect='raiano', word_lookup=False)}\n")

    # Central Dialect
    print("\n--- Central ---")
    print(f"Expected IPA: ˈaj ˈmas̺/ˈmajs̺ ˈfwo.ɣʊ/u ɐˈʎa, i je dejˈmĩ.gʊ/u\n")
    print(f"Phonemized (Central, with optional, using dict): {mirandese_phonemizer(test_sentence, dialect='central', word_lookup=True,  keep_optional_phones=True)}")
    print(f"Phonemized (Central, no optional, using dict): {mirandese_phonemizer(test_sentence, dialect='central', word_lookup=True,  keep_optional_phones=False)}")
    print(f"Phonemized (Central, no dict): {mirandese_phonemizer(test_sentence, dialect='central', word_lookup=False)}\n")

    # Sendinese Dialect
    print("\n--- Sendinese ---")
    print(f"Expected IPA: ˈaj ˈmas̺ ˈfu.ɣʊ/u ɐˈla, ˈi ˈ(j)i dɨˈmʊ̃j̃.gʲʊ/u\n")
    print(f"Phonemized (Sendinese, with optional, using dict): {mirandese_phonemizer(test_sentence, dialect='sendinese', word_lookup=True, keep_optional_phones=True)}")
    print(f"Phonemized (Sendinese, no optional, using dict): {mirandese_phonemizer(test_sentence, dialect='sendinese', word_lookup=True, keep_optional_phones=False)}")
    print(f"Phonemized (Sendinese, no dict): {mirandese_phonemizer(test_sentence, dialect='sendinese', word_lookup=False)}\n")

    # Example demonstrating 'lh' to 'l' in Sendinese
    print(f"Original: alhá")
    print(f"Phonemized (Central): {mirandese_phonemizer('alhá', dialect='central')}")  # Should be aʎa
    print(f"Phonemized (Sendinese): {mirandese_phonemizer('alhá', dialect='sendinese')}\n")  # Should be ala

    print(f"Original: Lhado")
    print(f"Phonemized (Central): {mirandese_phonemizer('Lhado', dialect='central')}")  # Should be ʎado
    print(f"Phonemized (Sendinese): {mirandese_phonemizer('Lhado', dialect='sendinese')}\n")  # Should be lado
