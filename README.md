# Mirandese Phonemizer

Grapheme-to-phoneme (G2P) conversion for **Mirandese** (`mwl`), the
Asturleonese language of Terra de Miranda, Portugal — text in, IPA out, with
cross-word sandhi, allophony and stress.

```python
from mwl_phonemizer import phonemize

phonemize("Falo la lhéngua mirandesa.")   # 'ˈfalu lɐ ˈʎɛŋɡwa miɾɐˈndez̺ɐ.'
```

## Install

```bash
pip install mwl_phonemizer
```

This pulls in [`orthography2ipa`](https://github.com/TigreGotico/orthography2ipa),
which carries the Mirandese language specs and gold data.

## Usage

### One-shot

```python
from mwl_phonemizer import phonemize

phonemize("lhéngua")                          # 'ˈʎɛŋɡwa'
phonemize("fuogo", dialect="mwl-x-sendim")    # Sendinese variety
```

`phonemize` caches one phonemizer per dialect, so repeated calls are cheap.

### Reusable instance

```python
from mwl_phonemizer import MirandesePhonemizer

pho = MirandesePhonemizer(dialect="mwl")
pho.phonemize("Buonos dies, cumo stás?")   # full text, punctuation preserved
pho.phonemize_word("amportante")           # a single word -> 'ɐ̃puˈɾtɐ̃tɨ'
```

`transcribe` / `transcribe_word` are aliases of `phonemize` / `phonemize_word`,
and `language_codes` reports the BCP-47 codes the instance covers — the surface
downstream engines call.

### Dialects

The `dialect` argument is an `orthography2ipa` Mirandese spec code:

| code | variety |
|------|---------|
| `mwl` | Central Mirandese (default) |
| `mwl-x-sendim` | Sendinese — depalatalises `lh`/initial `l` to `[l]` |
| `mwl-x-ifanes` | Ifanês / Raiano (northern) |

```python
MirandesePhonemizer("mwl-x-sendim").phonemize("lhobo")   # 'ˈloβu', not 'ˈʎobu'
```

## How it works

The transcription is the `orthography2ipa` Mirandese pronunciation lattice.
That engine owns the phonology — grapheme rules, allophony, cross-word sandhi
and stress — for all three lects. This library is a thin Mirandese-facing
wrapper that adds dialect selection, punctuation-preserving text handling, and
two opt-in layers:

- **Lexicon overlay** (`lookup=True`) — a bundled native-speaker word
  dictionary (`mwl_phonemizer.gold`, from the
  [`TigreGotico/mirandese_g2p`](https://huggingface.co/datasets/TigreGotico/mirandese_g2p)
  dataset). Words present in it are returned verbatim. Its transcription
  convention is finer-grained (marking, for example, vowel centralisation) and
  differs from the sentence gold below, so it is off by default.

  ```python
  pho.phonemize("lhéngua")               # 'ˈʎɛŋɡwa'   (lattice)
  pho.phonemize("lhéngua", lookup=True)  # 'ˈʎɛ̃ɡwɐ'   (dictionary)
  ```

- **CRF correction** (`use_crf=True`) — a linear-chain CRF over the engine's
  per-grapheme feature export, trained on that same word dictionary. It is
  tuned to the dictionary's convention and moves output away from the sentence
  gold, so it too is off by default; it is kept for callers whose target
  matches that convention.

  ```python
  MirandesePhonemizer("mwl", use_crf=True).phonemize_word("amportante")
  ```

## Accuracy

Phoneme Error Rate (PER = character edit distance / gold length), gold lookup
disabled so the numbers reflect the model.

### Sentence gold (primary)

The research-grounded, blind-judge-verified 20-sentence sets `orthography2ipa`
ships for each lect. These are held out from everything the library trains on.
The deployed default reproduces them segment-for-segment:

| lect | sentences | PER | PER (stress-agnostic) |
|------|-----------|-----|-----------------------|
| `mwl` | 20 | **0.00%** | **0.00%** |
| `mwl-x-sendim` | 20 | **0.00%** | **0.00%** |
| `mwl-x-ifanes` | 20 | **0.00%** | **0.00%** |

### Word dictionary (secondary)

The ~205-word native-speaker dictionary, in its own finer convention. Because
that convention differs from the sentence gold, PER against it is a measure of
convention distance, not of engine error:

| system | PER | PER (stress-agnostic) |
|--------|-----|-----------------------|
| lattice | 22.33% | 19.60% |
| + CRF, fit to dictionary | 6.99% | 1.92% |
| + CRF, 5-fold cross-validated | 21.49% | 18.79% |

The CRF fit-to-dictionary figure is an upper bound (trained and scored on the
same words); cross-validation estimates unseen-word performance. Reproduce
either table with:

```bash
python -m mwl_phonemizer.evaluate                # dialect mwl
python -m mwl_phonemizer.evaluate mwl-x-sendim
```

## License

Apache-2.0
