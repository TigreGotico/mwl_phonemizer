# Roadmap — mwl_phonemizer

Grapheme-to-phoneme for Mirandese (mwl), converting text to IPA. The package
bundles several interchangeable backends — character lookup, n-gram, hand-crafted
orthography rules, a character-level CRF, and espeak/epitran outputs corrected by
rules or CRF — with dialect lookups for Central, Raiano, and Sendinese. The best
configuration (orthography rules + CRF) reaches a low stress-agnostic PER on the
in-repo benchmark.

## Phase 0 — Hardening

- Realign the three existing workflows to `OpenVoiceOS/gh-automations@dev` and
  remove their inline `publish_pypi` / `sync_dev` steps in favour of the reusable
  workflows; add `build-tests`, `coverage`, and `license_check`.
- Migrate packaging to `pyproject.toml`, declare `epitran`/`espeak` backends as
  optional extras (they are imported lazily today), add `LICENSE`, fill
  `description`, and add a `.gitignore` so `mwl_phonemizer.egg-info/` stays out.
- Add a `tests/` suite covering the rule and lookup backends and the IPA cleanup
  helpers (`strip_markers`, `strip_stress`); promote the in-repo benchmark to a
  regression test that fails on PER regressions.

## Phase 1 — Correctness & coverage

- Add stress prediction (rule-based first, following Mirandese phonology; ML as a
  follow-up) so output is not stress-agnostic by default.
- Expand dialect exception lookups (Central / Raiano / Sendinese) and verify the
  Latin/Proto-Romance cluster rules (`pl`/`kl`/`fl` → `tʃ`, `-ly-`/`-cl-` → `ʎ`,
  `ll`→`ʎ`, `nn`→`ɲ`, `-mn-`→`m`) against more gold data.
- Grow the evaluation corpus beyond ~150 words to make the CRF/PER numbers
  meaningful and reduce overfitting.

## Phase 2 — Integration

- Expose the recommended backend as a `phoonnx` phonemizer: the `PhonemeType` /
  per-language `mwl` slots already exist in phoonnx's config and
  `phoonnx/phonemizers/mwl.py`, so wire `CRFOrthoCorrector` (or the chosen default)
  through `BasePhonemizer`, emitting `Alphabet.IPA`.
- Align the IPA inventory with `orthography2ipa`: contribute / reconcile a Mirandese
  `LanguageSpec` (grapheme→IPA + allophone maps, ancestry to pt/ast) so output
  validates against its tokenizer and can be compared via the distance metrics.

## Phase 3 — Datasets & publishing

- Publish the aligned word→IPA gold set as a versioned dataset so backends can be
  scored reproducibly.
- Explore a small seq2seq/transformer G2P once the corpus is large enough to beat
  the rules+CRF baseline; ship it as an additional backend, not a replacement.
- Release to PyPI through the standard publish workflow after Phase 0.
