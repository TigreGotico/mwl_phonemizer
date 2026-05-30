# Quickstart — Mirandese text to IPA

`mwl_phonemizer` turns Mirandese (mwl) text into its IPA phonetic transcription.
Every phonemizer is a small class with the same two methods — `phonemize(word)`
for one word and `phonemize_sentence(text)` for a whole sentence — so you can
swap one backend for another without touching your calling code.

## 1. Install

```bash
pip install -e .
```

Core dependencies (`python-Levenshtein`, `sklearn_crfsuite`, `editdistance`,
`joblib`) come from `requirements.txt`. The CRF backends train a tiny model on
import, so the very first construction takes a moment.

Two backends need extra software that is **not** declared as a dependency and is
imported lazily — install them only if you reach for those classes:

- `epitran` (`pip install epitran`) for `EpitranMWL` / `CRFEpitranCorrector`.
- the `espeak-ng` system binary for `EspeakMWL` / `CRFEspeakCorrector`.

## 2. The one idea

Every phonemizer subclasses `MirandesePhonemizer` and shares one interface:

```python
phonemizer.phonemize(word, lookup_word=True)        # -> IPA string for one word
phonemizer.phonemize_sentence(text, lookup_word=True)  # -> IPA string, punctuation kept
```

`lookup_word=True` (the default) returns the curated gold transcription if the
word is in the bundled dictionary, and only falls back to the model otherwise.
Pass `lookup_word=False` to force the model/rules path — that is what you want
when measuring how the engine actually performs.

## 3. First real call

`CRFOrthoCorrector` is the headline engine: hand-written orthographic rules whose
output is cleaned up by a character-level CRF. It needs no external binaries.

```python
from mwl_phonemizer import CRFOrthoCorrector

phonemizer = CRFOrthoCorrector()

text = ("Muitas lhénguas ténen proua de ls sous pergaminos antigos, "
        "cumo ye l causo de la lhéngua mirandesa.")
print(phonemizer.phonemize_sentence(text))
# mujtɐs̺ ʎɛ̃ɡwas̺ tɛnẽ pɾowɐ ...
```

A single word, forcing the engine path so the lookup table does not shadow it:

```python
print(phonemizer.phonemize("lhéngua", lookup_word=False))   # ʎɛ̃ɡwɐ
```

## 4. Pick a backend

All of these share the interface above; they differ in accuracy and in what they
require to run:

```python
from mwl_phonemizer import (
    LookupTableMWL,        # letter/digraph lookup table, no dependencies
    NgramMWLPhonemizer,    # statistical n-gram G2P, no dependencies
    OrthographyRulesMWL,   # hand-crafted orthographic rules, no dependencies
    CRFOrthoCorrector,     # rules + CRF correction (best PER), no external binaries
)

for cls in (LookupTableMWL, NgramMWLPhonemizer, OrthographyRulesMWL, CRFOrthoCorrector):
    print(cls.__name__, cls().phonemize("mirandesa", lookup_word=False))
```

See [api.md](api.md) for the full class list and signatures.

## 5. Clean up the output

The base class ships two static helpers for normalising IPA before comparison:

```python
from mwl_phonemizer.base import MirandesePhonemizer

MirandesePhonemizer.strip_markers("ˈe(j).ʒɛmˈplu")   # 'ˈejʒɛmˈplu'  — drop . ( )
MirandesePhonemizer.strip_stress("miɾɐ̃ˈdes̺")        # 'miɾɐ̃des̺'    — drop ˈ ˌ
```

## Where next

- [api.md](api.md) — every public class, signature, and return shape
- [advanced.md](advanced.md) — dialects, evaluation, model persistence, gotchas
