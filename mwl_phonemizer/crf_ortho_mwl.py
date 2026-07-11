from mwl_phonemizer.crf_mwl import CRFPhonemizer
from mwl_phonemizer.orthography_hand_rules import OrthographyRulesMWL


class CRFOrthoCorrector(CRFPhonemizer):
    # This backend feeds the CRF orthography-rules IPA output (not orthographic
    # Mirandese text), so the o2i grapheme feature export does not apply; it
    # keeps the character-window features + Levenshtein label alignment.
    feature_backend = "char"

    def __init__(self, *args, **kwargs):
        self.phonemizer = OrthographyRulesMWL()
        DATASET = [(self.phonemizer.phonemize(word, lookup_word=False), gold)
                   for word, gold in self.phonemizer.GOLD.items()]
        DATASET += [(gold, gold)  # so it learns not to touch correct phones
                   for word, gold in self.phonemizer.GOLD.items()]
        super().__init__(*args, ignore_stress=True, train_data=DATASET, **kwargs)

    def grapheme_transforms(self, word: str) -> str:
        return self.phonemizer.phonemize(word, lookup_word=False)


if __name__ == "__main__":
    phonemizer = CRFOrthoCorrector()

    # Evaluate on the same data (overfitting expected due to small dataset)
    stats = phonemizer.evaluate_on_gold(limit=None, detailed=False, show_changes=False)

    # PER is computed inside evaluate_on_gold (see base.MirandesePhonemizer).
    per = stats['per']
    per_no_stress = stats['per_no_stress']

    # --- Print Summary Metrics ---
    print("\n" + "=" * 50)
    print("      Mirandese Phonemizer Espeak+CRF Evaluation")
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