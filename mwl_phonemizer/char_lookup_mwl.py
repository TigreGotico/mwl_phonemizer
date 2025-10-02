from mwl_phonemizer.base import MirandesePhonemizer


class LookupTableMWL(MirandesePhonemizer):
    TILDE = "̃"  # ◌̃

    LETTERS = {
        "a": ["a", "ɐ"],
        "b": ["b", "β"],
        "c": ["k", "s"],
        "ç": ["s", "z"],
        "d": ["d", "ð"],
        "e": ["ɨ"],
        "é": ["ɛ"],
        "f": ["f"],
        "g": ["ɣ"],
        "h": [""],  # silent
        "i": ["i", "j"],
        "j": ["ʒ"],
        "l": ["l", "ɫ"],
        "m": ["m", TILDE, ],
        "n": ["n", "ŋ", TILDE],
        "o": ["u", "o", "ʊ"],
        "ó": ["ɔ"],
        "p": ["p"],
        "q": ["k"],
        "r": ["ɾ"],
        "s": ["s̺", "z̺"],
        "t": ["t"],
        "u": ["u", "w", "ũ"],
        "x": ["ʃ"],
        "y": ["j"],
        "z": ["z"],

        "A": ["ɐ̃ŋ"],
        "E": ["ẽŋ", "ɨ̃"],
        "I": ["ĩŋ"],
        "O": ["õŋ"],
        "R": ["r"],
        "S": ["s̺"],
        "U": ["ũŋ", "ʊ̃ŋ"],
        "Q": ["k"],
        "G": ["g"],
        "Ç": ["sɛ", "sɨ"],
        "C": ["s̻i"],
        "W": ["wo"],
        "Z": ["sk"],
        # "I": ["ɨ̃j̃"],  # SENDINESE
    }

    @staticmethod
    def normalize(sentence: str):
        # normalize short/long pauses to " " and "."
        sentence = (sentence.lower()
                    .replace("\t", " ")
                    .replace("-", " ")
                    .replace(",", " ")
                    .replace(";", " ")
                    .replace(".", ".")
                    .replace("!", ".")
                    .replace("?", "."))

        # temp representation of digraphs as individual letters
        DIMAP = {
            "an": "A",
            "en": "E",
            "in": "I",
            "on": "O",
            "un": "U",
            "rr": "R",
            "ss": "S",
            "lh": "ʎ",
            "nh": "ɲ",
            "qu": "Q",
            "gu": "G",
            "gue": "G",
            "Ge": "G",
            "ce": "Ç",
            "ci": "C",
            "uo": "W",
            "çc": "Z",
            "ge": "ʒɨ",
        }

        # normalize digraphs
        for di, n in DIMAP.items():
            sentence = sentence.replace(di, n)
        return sentence

    # -------------------------
    # Phonemizer interface
    # -------------------------
    def phonemize(self, word: str, lookup_word: bool = True) -> str:
        """Phonemize a single Mirandese word via espeak + correction rules."""
        if lookup_word and word.lower() in self.GOLD:
            return self.GOLD[word.lower()]
        word = self.normalize(word)
        phonemes = ""
        for idx, char in enumerate(word):
            if char in self.LETTERS:
                pho = self.LETTERS[char][0]
                phonemes += pho
            else:
                phonemes += char
        return phonemes


if __name__ == "__main__":

    pho = LookupTableMWL()

    stats = pho.evaluate_on_gold(limit=None, detailed=False, show_changes=False)

    # --- Compute PER (Phoneme Error Rate) ---  # TODO - move this to evaluate_on_gold
    total_ref_len_stress = sum(len(v) for v in pho.GOLD.values())
    total_ref_len_no_stress = sum(len(pho.strip_stress(v)) for v in pho.GOLD.values())

    per = stats['avg_edit_distance'] * stats['counts'] / total_ref_len_stress

    per_no_stress = stats['avg_edit_distance_no_stress'] * stats['counts'] / total_ref_len_no_stress

    # --- Print Summary Metrics ---
    print("\n" + "=" * 50)
    print("      Mirandese Phonemizer Rule Evaluation")
    print("=" * 50)
    print(f"Total Words Evaluated: {stats['counts']}\n")

    print("## Phoneme Error Rate (PER, Full IPA Match, includes stress)")
    print(f"PER:    {per:.2%}")

    print("\n## Phoneme Error Rate (PER, Stress-Agnostic)")
    print(f"PER:    {per_no_stress:.2%}")

    # --- Print only 'wrong' words (ED > 0) ---
    print("\n--- Incorrectly Phonemized Words (Full IPA Match ED > 0) ---")
    wrong_words = stats.get("details", [])

    if wrong_words:
        print(f"Total Incorrect: {len(wrong_words)} words\n")

        # Print a header for the detailed list
        print(f"{'Word':<20} | {'Gold':<15} | {'Phonemized':<15} | {'ED After':<8}")
        print("-" * 75)

        # Print the detailed list
        for d in wrong_words:
            print(
                f"{d['word']:<20} | {d['gold']:<15} | {d['phonemes']:<15} | {d['ed']:<8}")
    else:
        print("All words achieved an exact match (100% Accuracy)!")

    sample_texts = [
        "Muitas lhénguas ténen proua de ls sous pergaminos antigos, de la lhiteratura screbida hai cientos d'anhos i de scritores hai muito afamados, hoije bandeiras dessas lhénguas. Mas outras hai que nun puoden tener proua de nada desso, cumo ye l causo de la lhéngua mirandesa.",
        "Todos ls seres houmanos nácen lhibres i eiguales an honra i an dreitos. Dotados de rezon i de cuncéncia, dében de se dar bien uns culs outros i cumo armano",
        "Hai más fuogo alhá, i ye deimingo!"
    ]
    for t in sample_texts:
        print(pho.phonemize_sentence(t))
