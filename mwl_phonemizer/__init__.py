import re
import string

MWL_ALPHABET_MAP = {
    "a": ["a", "ä", "ɐ"],
    "á": ["ɐ̃", "a",],
    "ai": ["aj"],
    "an": ["ɐ̃ŋ"],
    "b": ["b", "β"],  # - b = [β] between vowels and after voiced consonants
    "c": ["k", "s̻", "s", "z"],  # - c = [s̻] before e or i, [k] elsewhere
    "ç": ["z̻"],  # - ç = [z̻] before words starting with voiced consonants
    "ch": ["tʃ"],
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
    "l": ["l","ʎ", "ɫ"],  # - l = [ʎ] at the beginning of words, and [l] elsewhere
    "lh": ["ʎ"],
    "m": ["m", "~"],  # - m is silent before nasalized front vowels, e.g. amportante
    "n": ["n", "ŋ", "~"],
    # - n is silent before consonants and at the end of words before nasalized front vowels, e.g. lhéngua, sons, quien
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
    "z": ["z"]
}

_vowels = "aeiouáéíóúäɐɛɨɪɔʊ"  # Extended set of vowels for context checking
_voiced_consonants = "bdgjlmnrvz"  # Approximated list of voiced consonants


def _is_vowel(char):
    return char in _vowels


def _is_voiced_consonant(char):
    return char in _voiced_consonants


def phonemize_word(word):
    phonemes = []
    i = 0
    while i < len(word):
        matched = False

        # Try to match multi-character graphemes first
        for length in sorted([len(g) for g in MWL_ALPHABET_MAP.keys()], reverse=True):
            if i + length <= len(word):
                grapheme = word[i:i + length].lower()
                if grapheme in MWL_ALPHABET_MAP:
                    # Apply specific rules for graphemes
                    if grapheme == "b":
                        if (i > 0 and _is_vowel(word[i - 1])) and \
                                (i + 1 < len(word) and _is_vowel(word[i + 1])):
                            phonemes.append(MWL_ALPHABET_MAP["b"][1])  # [β] between vowels
                        elif i > 0 and _is_voiced_consonant(word[i - 1]):
                            phonemes.append(MWL_ALPHABET_MAP["b"][1])  # [β] after voiced consonants
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["b"][0])  # [b] otherwise
                    elif grapheme == "c":
                        if (i + 1 < len(word) and word[i + 1].lower() in "ei"):
                            phonemes.append(MWL_ALPHABET_MAP["c"][0])  # [s̻] before e or i
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["c"][1])  # [k] elsewhere
                    elif grapheme == "ç":
                        # This rule is tricky without full word context (e.g., "words starting with voiced consonants")
                        # For now, a simplified interpretation: if followed by a voiced consonant at word boundary
                        # This needs more sophisticated look-ahead if the rule means the *next word* starts with a voiced consonant
                        if i + 1 < len(word) and _is_voiced_consonant(word[i + 1]):
                            phonemes.append(
                                MWL_ALPHABET_MAP["ç"][0])  # [z̻] before words starting with voiced consonants
                        else:  # Fallback for now if not matching the specific rule
                            phonemes.append(MWL_ALPHABET_MAP["ç"][0])  # Default to [z̻]
                    elif grapheme == "d":
                        if (i > 0 and _is_vowel(word[i - 1])) and \
                                (i + 1 < len(word) and _is_vowel(word[i + 1])):
                            phonemes.append(MWL_ALPHABET_MAP["d"][1])  # [ð] between vowels
                        elif i > 0 and word[i - 1].lower() == 'r':
                            phonemes.append(MWL_ALPHABET_MAP["d"][1])  # [ð] after r
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["d"][0])  # [d] otherwise
                    elif grapheme == "e":
                        # Simplified for now: always take the first phoneme.
                        # "before stressed syllables" would require a syllabification and stress prediction model
                        phonemes.append(MWL_ALPHABET_MAP["e"][0])
                    elif grapheme == "g":
                        if (i > 0 and _is_vowel(word[i - 1])) and \
                                (i + 1 < len(word) and _is_vowel(word[i + 1])):
                            phonemes.append(MWL_ALPHABET_MAP["g"][1])  # [ɣ] between vowels
                        elif i > 0 and word[i - 1].lower() == 'r':
                            phonemes.append(MWL_ALPHABET_MAP["g"][1])  # [ɣ] after r
                        elif (i + 1 < len(word) and word[i + 1].lower() in "ei"):
                            phonemes.append(MWL_ALPHABET_MAP["g"][2])  # [ʒ] before e and i
                        # "g = [ɡu] in certain words" and "g = [gu̯] before a" are context-specific and harder to rule-base without a dictionary
                        # Falling back to default [g] for now if specific rules don't match
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["g"][0])
                    elif grapheme == "gu":
                        # Simplified for now, similar to 'g' for [ɣ]
                        if (i > 0 and _is_vowel(word[i - 1])) and \
                                (i + 2 < len(word) and _is_vowel(word[i + 2])):  # Check the character *after* 'u'
                            phonemes.append(MWL_ALPHABET_MAP["gu"][0])  # [ɣ] between vowels
                        elif i > 0 and word[i - 1].lower() == 'r':
                            phonemes.append(MWL_ALPHABET_MAP["gu"][0])  # [ɣ] after r
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["gu"][1])  # [g] otherwise
                    elif grapheme == "l":
                        if i == 0:  # At the beginning of words
                            phonemes.append(MWL_ALPHABET_MAP["l"][2])  # [ʎ]
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["l"][1])  # [l] elsewhere
                    elif grapheme == "m":
                        # "m is silent before nasalized front vowels, e.g. amportante" - requires nasal vowel detection
                        # For simplicity, assuming the first phoneme unless clear context for silence
                        # This rule is tricky without knowing which vowels are "nasalized front vowels"
                        # For now, a simplified assumption: if 'm' is followed by 'p' or 'b' or 'f'
                        # This rule might need further refinement for accuracy
                        if (i + 1 < len(word) and word[i + 1].lower() in "pb" and i > 0):  # Check for 'mp' or 'mb'
                            phonemes.append(MWL_ALPHABET_MAP["m"][1])  # Silent
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["m"][0])
                    elif grapheme == "n":
                        # "n is silent before consonants and at the end of words before nasalized front vowels"
                        if (i + 1 < len(word) and not _is_vowel(word[i + 1])) or (
                                i == len(word) - 1):  # Before consonants or at end
                            phonemes.append(MWL_ALPHABET_MAP["n"][2])  # Silent
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["n"][0])
                    elif grapheme == "o":
                        # "o = [u] when unstressed" - requires stress prediction
                        phonemes.append(MWL_ALPHABET_MAP["o"][0])  # Default to [ɔ] for now
                    elif grapheme == "qu":
                        if (i + 2 < len(word) and word[i + 2].lower() in "ei"):
                            phonemes.append(MWL_ALPHABET_MAP["qu"][0])  # [k] before e and i
                        elif (i + 2 < len(word) and word[i + 2].lower() in "aen"):  # Added 'en' as per rule
                            phonemes.append(MWL_ALPHABET_MAP["qu"][1])  # [kṷ] before a and en
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["qu"][0])  # default to [k]
                    elif grapheme == "r":
                        if i == 0 or (i > 0 and word[i - 1].lower() == 'n'):  # At beginning or after n
                            phonemes.append(MWL_ALPHABET_MAP["r"][2])  # [rr]
                        else:
                            phonemes.append(MWL_ALPHABET_MAP["r"][0])  # [ɾ] elsewhere
                    elif grapheme == "s":
                        if i == 0 or (i + 1 < len(word) and not _is_vowel(
                                word[i + 1])):  # Initial or before silent consonants (simplified to any non-vowel)
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
                        # "u = [ũ] for nasalized, needs context
                        phonemes.append(MWL_ALPHABET_MAP["u"][0])  # Default to [u]
                    elif grapheme == "v":
                        # "v is only used in loanwords from other languages" - defaulting to first phoneme
                        phonemes.append(MWL_ALPHABET_MAP["v"][0])
                    elif grapheme == "w":
                        # "w is only used in loanwords from other languages" - defaulting to first phoneme
                        phonemes.append(MWL_ALPHABET_MAP["w"][0])
                    else:
                        phonemes.append(MWL_ALPHABET_MAP[grapheme][0])  # Take the first phoneme in the list as default

                    i += length
                    matched = True
                    break

        # If no multi-character grapheme matched, try single character
        if not matched:
            if word[i].lower() in MWL_ALPHABET_MAP:
                phonemes.append(MWL_ALPHABET_MAP[word[i].lower()][0])
            elif word[i] in string.punctuation + string.whitespace:
                phonemes.append(word[i])  # Keep punctuation as is
            i += 1
    return "".join(phonemes)


def mirandese_phonemizer(text):
    words = re.findall(r"\b\w+\b|[\W_]+", text)  # Split by words and keep punctuation/spaces
    phonemized_parts = []
    for word_or_punc in words:
        if word_or_punc.isalpha():
            phonemized_parts.append(phonemize_word(word_or_punc))
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
    #     biβiɛ, kumɔ ʎ tʃauɣaɾz̻ɔ dɛ ʎa s̺jera,
    #     wa ʎɛ~ga dɛ s̺õŋs̺ tɐ̃ŋ baɾjaðɔs̺?
    #
    #     mɔs̺tɾɛ-s̺ɛ i falɛ-s̺' ɛs̺a ʎɛ~ga fiʎa
    #     d'ũŋ pɔβɔ kɛ tẽŋ nejʎa ʎ tʃɔɾɔ i ʎ kɐ̃ŋtɔ!
    #     naða pɔɾ s̻jeɾtɔ mɔs̺ kautiβa tɐ̃ŋtɔ
    #     kumɔ ʎa fɔɾm' ɐ̃ŋ kɛ ʎ'ejðeja bɾiʎa.
    #
    #     zgɾaz̻jaðɔ d'akɛl, k'aβɐ̃ŋdõŋɐ̃ŋdɔ
    #     ʎa patɾi' ɐ̃ŋ kɛ nas̻iw, ʎa kaz̺a i ʎ uɾtɔ.
    #     tamiẽŋ s̺ɛ s̺kɛz̻ɛ dɛ ʎa fala! kṷɐ̃ŋdɔ
    #     ʎ fuɾðɛs̺ bɛɾ, talβɛz̻ kɛ s̺tɛja muɾtɔ!