# API reference

Everything here is re-exported from the top-level `mwl_phonemizer` package or
lives on the `mwl_phonemizer.base` module. All phonemizers subclass
`MirandesePhonemizer` and share its `phonemize` / `phonemize_sentence` interface.

## The shared interface — `MirandesePhonemizer`

`from mwl_phonemizer.base import MirandesePhonemizer, Dialects`

```python
MirandesePhonemizer(
    gold_dict: str | None = None,       # path to gold {ortho: ipa} JSON
    raiano_dict: str | None = None,     # Raiano dialect exceptions
    sendinese_dict: str | None = None,  # Sendinese dialect exceptions
    dialect: Dialects = Dialects.CENTRAL,
)
```

The constructor loads three bundled JSON dictionaries (`central.json`,
`raiano.json`, `sendinese.json`) and runs every value through `strip_markers`.
The loaded dictionaries are available as `self.GOLD`, `self.RAIANO_GOLD`, and
`self.SENDINESE_GOLD`.

### Methods

```python
phonemize(word: str, lookup_word: bool = True) -> str
```
Returns the IPA transcription of one word. With `lookup_word=True`, a word found
in `self.GOLD` is returned verbatim. The base class raises `ValueError` for an
unknown word when `lookup_word=False`; every concrete subclass overrides this to
generate a transcription instead.

```python
phonemize_sentence(text: str, lookup_word: bool = True) -> str
```
Splits `text` into words and punctuation, phonemizes each alphabetic token, and
re-joins everything — punctuation and spacing are preserved, and `-` is treated
as a word separator.

```python
evaluate_on_gold(limit=None, detailed=False, show_changes=False) -> dict
```
Scores the phonemizer against `self.GOLD` (always with `lookup_word=False`).
Returns a dict shaped like:

```python
{
    "avg_edit_distance": float,            # mean edit distance, stress included
    "avg_edit_distance_no_stress": float,  # mean edit distance, stress ignored
    "counts": int,                          # words evaluated
    "improvements": Counter(),              # per-rule deltas (engine-specific)
    "details": [                            # only words with edit distance > 0
        {"word": str, "phonemes": str, "gold": str, "ed": int},
        ...
    ],
}
```

### Static helpers

```python
strip_markers(ipa: str) -> str   # removes '.', '(' and ')'
strip_stress(ipa: str) -> str    # removes primary 'ˈ' and secondary 'ˌ' stress
word_edit_distance(a: str, b: str) -> int   # editdistance.eval(a, b)
```

### `Dialects`

A `str` enum: `Dialects.CENTRAL` (`"central"`), `Dialects.RAIANO` (`"raiano"`),
`Dialects.SENDINESE` (`"sendinese"`).

## Dependency-free phonemizers

### `LookupTableMWL`

`from mwl_phonemizer import LookupTableMWL`

Single letter/digraph to phoneme table. `LookupTableMWL.normalize(sentence)` is a
static method that lowercases, collapses pauses, and rewrites digraphs (`lh`,
`nh`, `an`, `qu`, …) into internal placeholders before lookup.

```python
LookupTableMWL().phonemize("lhéngua", lookup_word=False)   # 'ʎɛnga'
```

### `NgramMWLPhonemizer`

`from mwl_phonemizer import NgramMWLPhonemizer`

```python
NgramMWLPhonemizer(n: int = 4, *args, **kwargs)
```
Statistical n-gram G2P trained on `self.GOLD` at construction time. For
`Dialects.RAIANO` or `Dialects.SENDINESE` the matching exception dictionary is
merged into the training data. `n` is the n-gram order (n=4 conditions on three
preceding graphemes).

```python
NgramMWLPhonemizer(n=4).phonemize("mirandesa", lookup_word=False)
```

### `OrthographyRulesMWL`

`from mwl_phonemizer import OrthographyRulesMWL`

```python
OrthographyRulesMWL(*args, keep_optional_phones=True, keep_stress_marks=False, **kwargs)
```
Hand-crafted orthographic and phonological rules (lenition, sibilant variation,
Latin cluster evolution, palatalization). `keep_optional_phones` keeps phones the
rules mark as optional (in parentheses); `keep_stress_marks` keeps `ˈ`/`ˌ`.

Grapheme segmentation is delegated to the shared
`orthography2ipa.phonetok.PhonetokTokenizer` (a maximal-munch trie over the
Mirandese grapheme set) and the realisation rules run as an
`orthography2ipa.rescorer.LatticeRescorer` over the resulting per-grapheme
lattice — there is no private tokenizer or hand-rolled index arithmetic.

```python
OrthographyRulesMWL().phonemize("lhéngua", lookup_word=False)   # 'ʎɛŋɡwa'
```

## CRF phonemizers

### `CRFPhonemizer`

`from mwl_phonemizer import CRFPhonemizer` (also `mwl_phonemizer.crf_mwl`)

```python
CRFPhonemizer(
    crf_model_path: str | None = None,
    strategy=AlignmentStrategy.LEV,    # LEV (Levenshtein editops) or PAD
    algorithm="lbfgs",
    c1=0.1, c2=0.1,
    max_iterations=100,
    all_possible_transitions=False,
    apply_manual_fixes=False,          # heuristic word-final phone patching
    ignore_stress=True,
    train_data: list[tuple[str, str]] | None = None,
    *args, **kwargs,
)
```

Character-level CRF over aligned `(input, gold)` pairs. On construction it loads
`crf_model_path` if the file exists, else trains on `train_data` if given, else
trains on `self.GOLD`. Useful methods:

```python
train_crf(train_data: list[tuple[str, str]]) -> None
save_model(path: str) -> None
load_model(path: str) -> None
grapheme_transforms(str_input: str) -> str   # override hook; identity by default
```

`AlignmentStrategy` is a `str` enum with `PAD` and `LEV`. Module-level helpers
`align_with_lev(a, b)` and `align_pad(a, b)` return two equal-length lists with
gaps marked `.`.

### `CRFOrthoCorrector`

`from mwl_phonemizer import CRFOrthoCorrector`

Runs `OrthographyRulesMWL` first and lets the CRF correct the result — the
lowest-PER engine, with no external binaries. Takes no required arguments.

```python
CRFOrthoCorrector().phonemize("lhéngua", lookup_word=False)   # 'ʎɛ̃ɡwɐ'
```

## Backends needing extra software

These are imported lazily; constructing them without the backend installed raises
at import/run time.

### `EspeakMWL` / `CRFEspeakCorrector`

`from mwl_phonemizer import EspeakMWL, CRFEspeakCorrector`

Use the `espeak-ng` system binary to phonemize via Portuguese, then (for the CRF
variant) correct it. `CRFEspeakCorrector` keeps stress (`ignore_stress=False`).

### `EpitranMWL` / `CRFEpitranCorrector`

`from mwl_phonemizer import EpitranMWL, CRFEpitranCorrector`

Use `epitran.Epitran("por-Latn")` as the first-pass transcriber, optionally
corrected by the CRF. Requires `pip install epitran`.

## Where next

- [quickstart.md](quickstart.md) — install and first call
- [advanced.md](advanced.md) — dialects, evaluation, persistence, gotchas
