from mwl_phonemizer.base import Dialects
from mwl_phonemizer.crf_mwl import CRFPhonemizer
from mwl_phonemizer.espeak_mwl import _EspeakPhonemizer


class CRFEspeakCorrector(CRFPhonemizer):
    def __init__(self, *args, **kwargs):
        self.espeak = _EspeakPhonemizer()
        super().__init__(*args, ignore_stress=False, **kwargs)

    def grapheme_transforms(self, word: str) -> str:
        word = word.replace("ch", "tch")
        return self.espeak.phonemize_string(word)


if __name__ == "__main__":
    phonemizer = CRFEspeakCorrector(dialect=Dialects.CENTRAL)

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
