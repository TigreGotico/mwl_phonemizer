# Mirandese Phonemizer

Grapheme-to-phoneme (G2P) conversion for **Mirandese** (`mwl`), the
Asturleonese language of Terra de Miranda, Portugal. It takes text and
returns IPA, with cross-word sandhi, allophony, and stress.

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

`transcribe` / `transcribe_word` are aliases of `phonemize` / `phonemize_word`.
`language_codes` reports the BCP-47 codes the instance covers, the surface
that downstream engines call.

### Dialects

The `dialect` argument is an `orthography2ipa` Mirandese spec code:

| code | variety |
|------|---------|
| `mwl` | Central Mirandese (default) |
| `mwl-x-sendim` | Sendinese, depalatalizes `lh`/initial `l` to `[l]` |
| `mwl-x-ifanes` | Ifanês / Raiano (northern) |

```python
MirandesePhonemizer("mwl-x-sendim").phonemize("lhobo")   # 'ˈloβu', not 'ˈʎobu'
```

### Numbers

Digits carry no orthography the lattice can read, so numeric tokens are spelled
out into Mirandese words before transcription, in the normalizer stage. This is
on by default in `phonemize`. Pass `expand_numbers=False` to leave digits as-is.

```python
from mwl_phonemizer import MirandesePhonemizer
from mwl_phonemizer.number_utils import normalize_numbers, MirandeseNumberParser

pho = MirandesePhonemizer("mwl")
pho.phonemize("tengo 2 gatos")                 # 2 -> 'dous', then transcribed
pho.phonemize("tengo 2 gatos", expand_numbers=False)   # digit left untouched

# spell numbers to text without phonemizing
normalize_numbers("tengo 21 anhos")            # 'tengo binte i un anhos'
normalize_numbers("la casa 5ª")                # 'la casa quinta'  (º masc / ª fem)

# the verbaliser directly
p = MirandeseNumberParser("mwl")
p.cardinal(256)                # 'duzentos i cincoenta i seis'
p.cardinal(2, "feminine")      # 'dues'
p.ordinal(1, "feminine")       # 'purmeira'
p.pronounce_token("3,5")       # 'trés bírgula cinco'
MirandeseNumberParser("mwl-x-sendim").cardinal(7)   # 'site'  (central 'siête')
```

Numeral groups join with the copulative **i** ("and"). The number words come
from a source-cited table. Cardinals through 500 and the tens 50-90 are
attested in Leite de Vasconcelos, *Estudos de Philologia Mirandesa* vol. I
§189 (pp. 347-351). The hundreds 600-900 follow the periphrastic
`cardinal + -cientos` rule Vasconcelos states for that range (p. 349). The
decimal word *bírgula* and the 6th/10th ordinals come from the regular
`v→b` / final-vowel adaptation. `number_utils.ATTESTED` and
`number_utils.DERIVED` list which words fall in each group.

## How it works

The transcription is the `orthography2ipa` Mirandese pronunciation lattice.
That engine owns the phonology: grapheme rules, allophony, cross-word sandhi,
and stress, for all three lects. This library is a thin Mirandese-facing
wrapper that adds dialect selection, punctuation-preserving text handling, and
two opt-in layers:

- **Lexicon overlay** (`lookup=True`) is a bundled native-speaker word
  dictionary (`mwl_phonemizer.gold`, from the
  [`TigreGotico/mirandese_g2p`](https://huggingface.co/datasets/TigreGotico/mirandese_g2p)
  dataset). Words present in it are returned verbatim. Its transcription
  convention is finer-grained (marking, for example, vowel centralization) and
  differs from the sentence gold below, so it is off by default.

  ```python
  pho.phonemize("lhéngua")               # 'ˈʎɛŋɡwa'   (lattice)
  pho.phonemize("lhéngua", lookup=True)  # 'ˈʎɛ̃ɡwɐ'   (dictionary)
  ```

- **CRF correction** (`use_crf=True`) is a linear-chain CRF over the engine's
  per-grapheme feature export, trained on that same word dictionary. It is
  tuned to the dictionary's convention and moves output away from the sentence
  gold, so it too is off by default. It is kept for callers whose target
  matches that convention.

  ```python
  MirandesePhonemizer("mwl", use_crf=True).phonemize_word("amportante")
  ```

## Accuracy

Phoneme Error Rate (PER = character edit distance / gold length), gold lookup
disabled so the numbers reflect the model.

### Human gold: the only accuracy measurement (primary)

The **only** human-authored Mirandese gold is the 219-word native-speaker
dictionary [`TigreGotico/mirandese_g2p`](https://huggingface.co/datasets/TigreGotico/mirandese_g2p)
(central 206, sendinese 11, raiano 2, rows routed to `mwl` / `mwl-x-sendim` /
`mwl-x-ifanes` by their dialect tag). Everything below is scored against it,
full dataset, no caps. Three normalizations are reported:

- **strict**: only structural markers (syllable dots, optional-phoneme
  parentheses) are removed. Stress and every diacritic count.
- **folded**: also folds three documented notation conventions:
  stress marks (`ˈ ˌ`), length (`ː`), and tie-bars (`t͡ʃ`→`tʃ`).
- **broad**: also folds the documented broad-vs-narrow gap. The
  human gold is a **narrow** transcription, and this engine is
  **broad-phonemic**. This folds centralized `ʉ ʊ`→`u`, spirant `ð`→`d`, dark
  `ɫ`→`l`, lowered `e̞`→`e`, and the apical/laminal sibilant diacritics
  (`s̺ s̻`→`s`). What remains is the residual true phonemic error, not
  convention distance.

| system | strict | folded | broad |
|--------|-------:|-------:|------:|
| **pure lattice** (deployed default) | 20.68% | 18.01% | **11.62%** |
| + CRF, 5-fold cross-validated (honest OOD) | 21.18% | 18.16% | 12.73% |
| + CRF, fit to dictionary (circular upper bound) | 8.79% | 3.83% | 2.59% |
| lexicon lookup (`lookup=True`, memorisation) | 0.25% | 0.28% | 0.30% |

Reading the table honestly:

- **Lexicon lookup ≈ 0%** is pure memorization: the lexicon *is* this gold, so
  every word is returned verbatim. It is not an accuracy signal, and it mixes
  the narrow lexicon convention into otherwise-broad sentences, which is why it
  is off by default.
- **CRF fit-to-dictionary (3.83% folded)** is trained and scored on the same
  words, a circular upper bound, not accuracy.
- **CRF 5-fold CV (18.16% folded)** is the honest out-of-dictionary estimate.
  It edges the lattice by about 1.3pp folded.

On the convention-neutral **broad** basis, the gap collapses to 0.37pp
(12.73% vs 11.62%). Almost all of the CRF's apparent gain comes from matching
the lexicon's narrow convention, not from fixing real errors, and it couples
every output to that convention. The **pure lattice remains the default**: it
is convention-neutral, deterministic, untrained, and statistically tied with
the CRF on true phonemic error.

Reproduce with:

```bash
python -m mwl_phonemizer.evaluate                # dialect mwl
python -m mwl_phonemizer.evaluate mwl-x-sendim
```

### Engine sentence set: a consistency check, NOT an accuracy claim

`orthography2ipa` also ships 20-sentence sets per lect
(`mwl`/`mwl-x-sendim`/`mwl-x-ifanes`). The lattice reproduces them at about 0%
PER. Those sentences were **authored to match this engine's own output**
(they are engine-pinned), so that 0% is an internal consistency check, and
**not** a measure of accuracy against human ground truth. Earlier versions of
this README, and two downstream dataset cards, presented that 0% as the
primary accuracy figure. That was circular. The human-gold table above is the
real measurement.

## Related projects

- [`TigreGotico/orthography2ipa`](https://github.com/TigreGotico/orthography2ipa)
  is the pronunciation lattice engine this library wraps.
- [`TigreGotico/mirandese_g2p`](https://huggingface.co/datasets/TigreGotico/mirandese_g2p)
  is the native-speaker gold dataset used for the lexicon overlay, the CRF,
  and the accuracy table above.

## License

Apache-2.0
