# Mirandese Phonemizer

Grapheme-to-phoneme (G2P) conversion for **Mirandese** (`mwl`), the
Asturleonese language of Terra de Miranda, Portugal.

The pipeline has three layers, each falling back to the next:

1. **Native-speaker gold dictionary** — pronunciations from the
   [TigreGotico/mirandese_g2p](https://huggingface.co/datasets/TigreGotico/mirandese_g2p)
   dataset, bundled as a word list and returned verbatim.
2. **`orthography2ipa` lattice** — the language-agnostic
   [orthography2ipa](https://github.com/TigreGotico/orthography2ipa) engine
   with its Mirandese language specs provides the base transcription for any
   word.
3. **CRF correction** — a linear-chain CRF trained on the gold dictionary
   corrects the lattice output for out-of-dictionary words. Its features are
   `orthography2ipa`'s per-grapheme feature export (phonological-class
   predicates, grapheme context, candidate-lattice top-1/cost, per-word
   confidence). Stress placement is delegated to the spec's own stress rules,
   so the CRF only learns segment corrections.

## Quickstart

```python
from mwl_phonemizer import MirandesePhonemizer

pho = MirandesePhonemizer(dialect="mwl")
pho.phonemize("lhéngua")                      # 'ˈʎɛ̃ɡwɐ'
pho.phonemize("Falo la lhéngua mirandesa.")   # full text, punctuation kept
pho.phonemize_word("amportante")              # single word
```

Or the module-level convenience (caches one phonemizer per dialect):

```python
from mwl_phonemizer import phonemize

phonemize("lhéngua")
phonemize("fuogo", dialect="mwl-x-sendim")
```

`MirandesePhonemizer` also implements the `orthography2ipa` `G2PPlugin`
interface (`transcribe`, `transcribe_word`, `language_codes`).

## Dialects

The `dialect` argument takes an `orthography2ipa` Mirandese spec code:

| code | variety |
|------|---------|
| `mwl` | Central Mirandese (default) |
| `mwl-x-sendim` | Sendinese (Sendim) |
| `mwl-x-ifanes` | Ifanes |

Sendinese gold overrides (e.g. `lh` → /l/ words) are layered on top of the
base gold dictionary. A small Raiano word list is bundled in
`mwl_phonemizer.gold.RAIANO`; it is not wired to a dialect because no
`mwl-x-raiano` spec exists in `orthography2ipa`.

## Accuracy

Phoneme Error Rate (PER = character edit distance / gold length) on the full
205-word native-speaker gold dictionary, dialect `mwl`, gold lookup disabled
so the numbers reflect the models rather than the dictionary:

| system | PER | PER (stress-agnostic) |
|--------|-----|-----------------------|
| `orthography2ipa` base | 22.33% | 19.60% |
| + CRF, fit to gold | **6.99%** | **1.92%** |
| + CRF, 5-fold cross-validated | 21.49% | 18.79% |

Methodology, stated honestly:

- **fit to gold** — the CRF is trained on the full gold dictionary and scored
  on that same dictionary. This is an upper bound (the deployed default
  trains exactly this way), not a generalization estimate.
- **5-fold cross-validated** — every gold word is scored by a CRF trained
  without it. This estimates performance on out-of-dictionary words: the CRF
  helps on both metrics even for words it has never seen, and words that are
  in the dictionary bypass the model entirely via gold lookup.
- Most residual stressed-PER error is stress-mark placement, which comes from
  the spec's rule-based stress detector, not from the CRF.

Reproduce with:

```bash
python -m mwl_phonemizer.evaluate            # dialect mwl
python -m mwl_phonemizer.evaluate mwl-x-sendim
```

## Retraining the CRF

The CRF trains at construction time in a few seconds; there is nothing to
ship. To persist and reuse a model:

```python
pho = MirandesePhonemizer(dialect="mwl", crf_model_path="mwl.crf")
```

The model is loaded from the path when the file exists and trained-then-saved
otherwise. To train on custom data:

```python
from orthography2ipa import G2P
from mwl_phonemizer.crf import CRFCorrector

crf = CRFCorrector(G2P("mwl")).train([("lhéngua", "ˈʎɛ̃gwɐ")])
crf.predict("lhéngua")
crf.save("custom.crf")
```

## Install

```bash
pip install mwl_phonemizer
```

## License

Apache-2.0
