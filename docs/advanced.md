# Advanced usage

Recipes, configuration, and the sharp edges. Skim [api.md](api.md) first for the
signatures referenced here.

## Selecting a dialect

The dialect flows through the base constructor and changes which exception
dictionary is consulted. It matters most for `NgramMWLPhonemizer`, which merges
the dialect's exceptions into its training data:

```python
from mwl_phonemizer import NgramMWLPhonemizer
from mwl_phonemizer.base import Dialects

central   = NgramMWLPhonemizer(n=4, dialect=Dialects.CENTRAL)
sendinese = NgramMWLPhonemizer(n=4, dialect=Dialects.SENDINESE)

print(central.phonemize("lhéngua", lookup_word=False))
print(sendinese.phonemize("lhéngua", lookup_word=False))
```

The Sendinese dialect notably realises `lh` as `l`; its exceptions live in
`sendinese.json`, Raiano in `raiano.json`, and the Central gold in `central.json`.

## Comparing engines on one word

Because every engine shares the interface, comparison is a loop. Force
`lookup_word=False` so the gold dictionary does not short-circuit the engine:

```python
from mwl_phonemizer import (
    LookupTableMWL, NgramMWLPhonemizer, OrthographyRulesMWL, CRFOrthoCorrector,
)

engines = [LookupTableMWL(), NgramMWLPhonemizer(n=4),
           OrthographyRulesMWL(), CRFOrthoCorrector()]

for eng in engines:
    print(f"{type(eng).__name__:22} {eng.phonemize('mirandesa', lookup_word=False)}")
```

## Scoring against the gold dictionary

`evaluate_on_gold` returns mean edit distances plus a `details` list of every
word the engine got wrong. Phoneme Error Rate (PER) is that total edit distance
divided by the total reference length:

```python
from mwl_phonemizer import OrthographyRulesMWL

eng = OrthographyRulesMWL()
stats = eng.evaluate_on_gold()

ref_len = sum(len(v) for v in eng.GOLD.values())
per = stats["avg_edit_distance"] * stats["counts"] / ref_len
print(f"PER (stress): {per:.2%}  over {stats['counts']} words")

ref_len_ns = sum(len(eng.strip_stress(v)) for v in eng.GOLD.values())
per_ns = stats["avg_edit_distance_no_stress"] * stats["counts"] / ref_len_ns
print(f"PER (stress-agnostic): {per_ns:.2%}")

for d in stats["details"][:5]:
    print(f"  {d['word']:<14} gold={d['gold']:<14} got={d['phonemes']:<14} ed={d['ed']}")
```

A lower PER does not by itself mean a better phonemizer — the gold set is roughly
150 words, so the CRF engines are overfitted to it. Treat the numbers as a
relative sanity check, not an absolute quality score.

## Training a CRF on your own data

`CRFPhonemizer` retrains on every construction. Pass `train_data` — a list of
`(orthography, gold IPA)` pairs — to train on your own aligned set instead of the
bundled gold dictionary:

```python
from mwl_phonemizer import CRFPhonemizer

pairs = [("lhéngua", "ʎɛ̃ɡwɐ"), ("mirandesa", "miɾɐ̃dezɐ"), ("fuogo", "fwoɡu")]
eng = CRFPhonemizer(train_data=pairs, ignore_stress=True)
print(eng.phonemize("fuogo", lookup_word=False))
```

Once trained, `eng.save_model(path)` writes the model with `joblib` and
`eng.load_model(path)` reads it back into an existing instance.

`strategy=AlignmentStrategy.LEV` aligns input and gold with Levenshtein editops;
`AlignmentStrategy.PAD` pads the shorter sequence with `.`. The `apply_manual_fixes`
flag turns on heuristic word-final phone patching for words ending in a vowel or a
consonant the alignment tends to drop.

## Optional backends

`EspeakMWL` / `CRFEspeakCorrector` shell out to the `espeak-ng` binary;
`EpitranMWL` / `CRFEpitranCorrector` use `epitran.Epitran("por-Latn")`. Neither
backend is a declared dependency, so guard their use:

```python
try:
    from mwl_phonemizer import CRFEspeakCorrector
    eng = CRFEspeakCorrector()
    print(eng.phonemize_sentence("Hai más fuogo alhá, i ye deimingo!"))
except Exception as exc:
    print("espeak-ng backend unavailable:", exc)
```

## Gotchas

- `phonemize()` on the bare base `MirandesePhonemizer` raises `ValueError` for an
  unknown word when `lookup_word=False`. Use a concrete subclass to generate.
- With `lookup_word=True` (the default), gold words are returned verbatim, so
  evaluation always forces `lookup_word=False`.
- CRF engines train on import; the first construction is the slow one.
- `OrthographyRulesMWL` defaults to `keep_stress_marks=False` — set it `True` if
  you need stress in the output.

## Where next

- [quickstart.md](quickstart.md) — install and first call
- [api.md](api.md) — full signatures and return shapes
