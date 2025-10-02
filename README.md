# **Mirandese Phonemizer**

This repository contains a Python-based Mirandese phonemizer, designed to convert Mirandese text into its International Phonetic Alphabet (IPA) representation. It supports different Mirandese dialects and incorporates various phonological rules based on linguistic information from Wikipedia.

## **Features**

* **Grapheme-to-Phoneme Conversion:** Converts Mirandese graphemes (letters and digraphs) to their corresponding IPA phonemes.
* **Contextual Rules:** Applies phonological rules based on surrounding characters (e.g., lenition of voiced stops, sibilant variations, vowel glides).
* **Dialectal Support:**
  * Handles the specific lh to l pronunciation change in the Sendinese dialect.
  * Includes word-level lookup dictionaries for Central, Raiano, and Sendinese dialects to handle irregular pronunciations.
* **Latin Cluster Evolution:** Converts Latin initial consonant clusters (pl, kl, fl) to /tʃ/.
* **Proto-Romance Medial Clusters:** Converts Proto-Romance medial clusters (-ly-, -cl-) to /ʎ/.
* **Double Consonant Palatalization:** Handles palatalization of double ll to /ʎ/ and nn to /ɲ/.
* **Proto-Romance -mn-:** Converts -mn- to /m/.
* **Output Customization:** Options to keep or remove optional phonemes (in parentheses) and stress marks/syllable dots.

---

## **Usage**

```python
from mwl_phonemizer.crf_espeak_mwl import CRFEspeakCorrector


sample_texts = [
    "Muitas lhénguas ténen proua de ls sous pergaminos antigos, de la lhiteratura screbida hai cientos d'anhos i de scritores hai muito afamados, hoije bandeiras dessas lhénguas. Mas outras hai que nun puoden tener proua de nada desso, cumo ye l causo de la lhéngua mirandesa.",
    "Todos ls seres houmanos nácen lhibres i eiguales an honra i an dreitos. Dotados de rezon i de cuncéncia, dében de se dar bien uns culs outros i cumo armano",
]

phonemizer = CRFEspeakCorrector()
for text in sample_texts:
    print(f"Original: {text}")
    print(f"Phonemized: {phonemizer.phonemize_sentence(text)}\n")
    
# Original: Muitas lhénguas ténen proua de ls sous pergaminos antigos, de la lhiteratura screbida hai cientos d'anhos i de scritores hai muito afamados, hoije bandeiras dessas lhénguas. Mas outras hai que nun puoden tener proua de nada desso, cumo ye l causo de la lhéngua mirandesa.
# Phonemized: mujtɐs̺ ʎenɡɐs̺ tenɛ̃ pɾowuɐ dɛ ls̺ sowus̺ pɛɾɡɐminos̺ ɐntiɡos̺, dɛ ʎɐ ʎitɛɾɐtuɾɐ s̺kɾβdɐ aj s̻iɛntos̻ d'ɐnos̺ i dɛ s̺kɾitoɾɛs̺ aj mujtu ɐfɐmðs̺, owiʒɛ bɐndɛjɾɐs̺ dɛʃsɐs̺ ʎenɡɐs̺. mɐs̺ owutrɐs̺ aj kʷɛ nũ puð̃ tɨˈneɾ pɾowuɐ dɛ nð dɛʃsu, kumu ˈje l̩ kawzu dɛ ʎɐ ˈʎɛ̃ɡwɐ miɾɐndɛzɐ.

# Original: Todos ls seres houmanos nácen lhibres i eiguales an honra i an dreitos. Dotados de rezon i de cuncéncia, dében de se dar bien uns culs outros i cumo armano
# Phonemized: tðs̺ ls̺ sɛɾɛs̺ owumɐnos̺ nazɛ̃ ʎibrɛs̺ i ɛjɡɐlɛs̺ ɐ̃ onrɐ i ɐ̃ dɾɛjtos̺. dotðs̺ dɛ rɛzõ i dɛ kuns̻ens̻iɐ, dβ̃ dɛ sɛ dɐɾ biɛ̃ uns̺ kuls̺ owutros̺ i kumu ɐɾmɐnu
```

### **Helper Functions**

The base class provides static methods for cleaning up IPA output:

- **`strip_markers(ipa: str)`**: Removes syllable dots (`.`) and optional phoneme parentheses (`()`).
- **`strip_stress(ipa: str)`**: Removes primary (`ˈ`) and secondary (`ˌ`) stress markers.

```python
ipa_with_markers = "ˈe(j).ʒɛmˈplu"
clean_ipa = phonemizer.strip_markers(ipa_with_markers)
print(f"Clean IPA: {clean_ipa}")
# Output: Clean IPA: ˈejʒɛmˈplu

ipa_with_stress = "miɾɐ̃ˈdes̺"
stress_agnostic_ipa = phonemizer.strip_stress(ipa_with_stress)
print(f"Stress-Agnostic IPA: {stress_agnostic_ipa}")
# Output: Stress-Agnostic IPA: miɾɐ̃des̺
```

---

## **Phonemizer Comparison**

| Phonemizer            | PER (Full IPA, Stress) | PER (Stress-Agnostic) | Words Incorrect (ED>0) | Notes                                                     |
|-----------------------|------------------------|-----------------------|------------------------|-----------------------------------------------------------|
| **Espeak + CRF**      | 59.98% → 3.72%         | 39.51% → 4.26%        | 35                     | Espeak output corrected with a CRF model                  |
| **Epitran + CRF**     | 51.37% → 16.54%        | 44.89% → 18.97%       | 110                    | Epitran output corrected with a CRF model                 |
| **CRF**               | 15.36%                 | 17.06%                | 117                    | Character-level CRF trained on aligned word–phoneme pairs |
| **Orthography Rules** | 39.04%                 | 31.99%                | 136                    | Hand-crafted orthographic rules                           |
| **Epitran + Rules**   | 51.37% → 47.26%        | 44.89% → 40.07%       | 137                    | Epitran output corrected with hand-crafted rules          |
| **Espeak + Rules**    | 59.98% → 52.35%        | 39.51% → 30.30%       | 73                     | Espeak output corrected with hand-crafted rules           |
| **N-gram (n=4)**      | 43.93%                 | 30.98%                | 141                    | Statistical N-gram model for G2P conversion               |
| **Character lookup**  | 43.84%                 | 36.92%                | 142                    | Simple letter/digraph to phoneme lookup table             |

**Notes:**

- For **Epitran** and **Espeak**, the first value is the initial phonemization output; the second is after applying correction rules.
- **PER (Phoneme Error Rate)** measures the proportion of phonemes differing from the gold standard IPA transcription.
- **Stress-Agnostic PER** ignores stress marks.
- **lower PER does not necessarily mean a better phonemizer**

---

## **Future Work**

* **Stress Prediction:** Implement machine learning or rule-based stress placement.
* **Larger Dataset:** Expand training and evaluation beyond ~150 words.
* **Neural Approaches:** Explore Transformer or seq2seq models for improved G2P accuracy.
* **Dialectal Coverage:** Add more irregular forms and dialect-specific exceptions.

---

## **Contributing**

Feel free to open issues or submit pull requests for improvements, bug fixes, or new dialect support.
