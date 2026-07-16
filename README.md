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

### Human gold — the only accuracy measurement (primary)

The **only** human-authored Mirandese gold is the 219-word native-speaker
dictionary [`TigreGotico/mirandese_g2p`](https://huggingface.co/datasets/TigreGotico/mirandese_g2p)
(central 206, sendinese 11, raiano 2; rows routed to `mwl` / `mwl-x-sendim` /
`mwl-x-ifanes` by their dialect tag). Everything below is scored against it,
full dataset, no caps. Three normalisations are reported:

- **strict** — only structural markers (syllable dots, optional-phoneme
  parentheses) removed; stress and every diacritic count.
- **folded** — additionally folds three documented notation conventions:
  stress marks (`ˈ ˌ`), length (`ː`), and tie-bars (`t͡ʃ`→`tʃ`).
- **broad** — additionally folds the documented *broad-vs-narrow* gap: the
  human gold is a **narrow** transcription, this engine is **broad-phonemic**.
  Folds centralised `ʉ ʊ`→`u`, spirant `ð`→`d`, dark `ɫ`→`l`, lowered `e̞`→`e`,
  and the apical/laminal sibilant diacritics (`s̺ s̻`→`s`). What remains is the
  residual *true* phonemic error, not convention distance.

| system | strict | folded | broad |
|--------|-------:|-------:|------:|
| **pure lattice** (deployed default) | 22.23% | 19.50% | **13.10%** |
| + CRF, 5-fold cross-validated (honest OOD) | 21.18% | 18.16% | 12.73% |
| + CRF, fit to dictionary (circular upper bound) | 8.79% | 3.83% | 2.59% |
| lexicon lookup (`lookup=True`, memorisation) | 0.25% | 0.28% | 0.30% |

Reading the table honestly:

- **Lexicon lookup ≈ 0%** is pure memorisation — the lexicon *is* this gold, so
  every word is returned verbatim. It is not an accuracy signal, and it mixes
  the narrow lexicon convention into otherwise-broad sentences, which is why it
  is off by default.
- **CRF fit-to-dictionary (3.83% folded)** is trained and scored on the same
  words — a circular upper bound, not accuracy.
- **CRF 5-fold CV (18.16% folded)** is the honest out-of-dictionary estimate.
  It edges the lattice by ~1.3pp folded, but on the convention-neutral **broad**
  basis the gap collapses to 0.37pp (12.73% vs 13.10%): almost all of the CRF's
  apparent gain is matching the lexicon's narrow convention, not fixing real
  errors — and it couples every output to that convention. Hence the **pure
  lattice remains the default**: convention-neutral, deterministic, untrained,
  and statistically tied with the CRF on true phonemic error.

Reproduce with:

```bash
python -m mwl_phonemizer.evaluate                # dialect mwl
python -m mwl_phonemizer.evaluate mwl-x-sendim
```

### Engine sentence set — a consistency check, NOT an accuracy claim

`orthography2ipa` also ships 20-sentence sets per lect
(`mwl`/`mwl-x-sendim`/`mwl-x-ifanes`). The lattice reproduces them at ~0% PER —
but those sentences were **authored to match this engine's own output** (they
are engine-pinned), so that 0% is an internal consistency check, **not** a
measure of accuracy against human ground truth. Earlier versions of this README
(and two downstream dataset cards) presented that 0% as the primary accuracy
figure; that was circular. The human-gold table above is the real measurement.

## License

Apache-2.0
