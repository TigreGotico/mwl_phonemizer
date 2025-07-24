# **Mirandese Phonemizer**

This repository contains a Python-based Mirandese phonemizer, designed to convert Mirandese text into its International Phonetic Alphabet (IPA) representation. It supports different Mirandese dialects and incorporates various phonological rules based on linguistic information from Wikipedia.

## **Features**

* **Grapheme-to-Phoneme Conversion:** Converts Mirandese graphemes (letters and digraphs) to their corresponding IPA phonemes.  
* **Contextual Rules:** Applies phonological rules based on the surrounding characters (e.g., lenition of voiced stops, sibilant variations, vowel glides).  
* **Dialectal Support:**  
  * Handles the specific lh to l pronunciation change in the Sendinese dialect.  
  * Includes word-level lookup dictionaries for Central, Raiano, and Sendinese dialects to handle irregular pronunciations.  
* **Latin Cluster Evolution:** Converts Latin initial consonant clusters (pl, kl, fl) to /tʃ/.  
* **Proto-Romance Medial Clusters:** Converts Proto-Romance medial clusters (-ly-, -cl-) to /ʎ/.  
* **Double Consonant Palatalization:** Handles palatalization of double ll to /ʎ/ and nn to /ɲ/.  
* **Proto-Romance -mn-:** Converts -mn- to /m/.  
* **Output Customization:** Options to keep or remove optional phonemes (in parentheses) and stress marks/syllable dots.


### **Basic Usage**

```python
from mwl_phonemizer import mirandese_phonemizer

text = "Hai más fuogo alhá, i ye deimingo!"  
ipa_representation = mirandese_phonemizer(text)  
print(ipa_representation)  
# Example Output (Central dialect, no optional phones/stress marks): aj mas fwoɣu aʎa i je dejmiŋgu
```

### **Dialect Selection**

Specify the dialect parameter for dialect-specific rules and word lookups.  

# Sendinese dialect  

```python
from mwl_phonemizer import mirandese_phonemizer

text = "Hai más fuogo alhá, i ye deimingo!"  
ipa_sendinese = mirandese_phonemizer(text, dialect='sendinese')  
print(ipa_sendinese)  
# Example Output (Sendinese dialect, no optional phones/stress marks): aj mas fuɣu ala i ji dɨmʊ̃j̃gu
```

# Raiano dialect  

```python
from mwl_phonemizer import mirandese_phonemizer

text = "Hai más fuogo alhá, i ye deimingo!"  
ipa_raiano = mirandese_phonemizer(text, dialect='raiano')  
print(ipa_raiano)  
# Example Output (Raiano dialect, no optional phones/stress marks): aj mas fwoʊ aʎa i je dejmĩgʲu
```

### **Controlling Output Details**

* word_lookup (default: True): Set to False to disable dictionary lookups and rely solely on rule-based phonemization.  
* keep_optional_phones (default: True): Set to False to remove phonemes enclosed in parentheses (e.g., (j)i becomes ji if True, i if False).  
* keep_stress_marks (default: False): Set to True to retain IPA stress marks (ˈ) and syllable dots (.).

```
text = "Hai más fuogo alhá, i ye deimingo!"

# No optional phones, no stress marks (default for most examples)  
print(mirandese_phonemizer(text, keep_optional_phones=False, keep_stress_marks=False))

# Keep optional phones and stress marks  
print(mirandese_phonemizer(text, keep_optional_phones=True, keep_stress_marks=True))
```

## **Phonological Rules Implemented**

The phonemizer attempts to follow the Mirandese phonology described on Wikipedia, including:

* **Sibilants:** Distinction and contextual voicing for /s̺/, /z̺/, /s̻/, /z̻/.  
* **Initial Consonants:** Retention of initial /f/.  
* **Latin Clusters:** Evolution of pl-, kl-, fl- to /tʃ/.  
* **Medial Clusters:** Evolution of -ly-, -cl- to /ʎ/.  
* **Double Consonants:** Palatalization of ll to /ʎ/ and nn to /ɲ/.  
* **Nasal Consonants:** Handling of m and n, including n velarization to ŋ before velar consonants.  
* **Vowel Glides:** i becoming j and u becoming w when adjacent to other vowels.  
* **Diphthongs:** Preservation of ei and ou.  
* **Final Vowels:** Final -o becoming /u/.  
* **Intervocalic Consonants:** Retention of intervocalic l and n.

## **Limitations**

* **Stress Prediction:** The current rule-based system does not perform stress prediction. Rules dependent on stress (e.g., specific vowel allophones, diphthongization of short e in stressed positions) are simplified or not fully implemented.  
* **Complex Allophony:** While allophones are listed in the map, their precise contextual application (beyond simple adjacency) is not exhaustively covered.  
* **Sentence-Level Context:** Rules that depend on broader sentence context (e.g., ç before words starting with voiced consonants) are approximated at the word level.  
* **Specific Dialectal Nuances:** Some very specific allophonic variations noted in the Wikipedia examples (e.g., gʲʊ for gu in deimingo in Raiano/Sendinese) are not yet explicitly captured by general rules and would require further refinement or more extensive dialect-specific dictionaries.

## **Contributing**

Feel free to open issues or submit pull requests if you find any inaccuracies or have suggestions for improvements.