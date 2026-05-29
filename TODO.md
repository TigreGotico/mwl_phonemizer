# TODO — mwl_phonemizer

A rule-based Mirandese phonemizer with several G2P backends (character lookup,
n-gram, hand-crafted orthography rules, CRF, and espeak/epitran correction) plus
dialect lookups for Central, Raiano, and Sendinese.

## Hardening (CI / packaging / hygiene)

- [ ] Align the existing workflows to `OpenVoiceOS/gh-automations@dev`: `release_workflow.yml`, `publish_stable.yml`, and `conventional-label.yaml` currently reference `TigreGotico/gh-automations@master`.
- [ ] Drop the inline `publish_pypi` / `sync_dev` steps from `release_workflow.yml` / `publish_stable.yml` and rely on the reusable workflows alone.
- [ ] Add the missing standard workflows: `build-tests`, `coverage`, `license_check`.
- [ ] Migrate packaging to `pyproject.toml`; keep the `version.py` block untouched by humans.
- [ ] Fill in package metadata: `license` and `description` are empty. Add a `LICENSE` file.
- [ ] Add a `.gitignore` (egg-info, `__pycache__`, build/dist) so the build artifact `mwl_phonemizer.egg-info/` is not committed.
- [ ] Declare the backend dependencies properly: `epitran` and `espeak`-based modules are imported lazily but not in `requirements.txt`, so those backends fail without them. Move them to optional extras keyed per backend.
- [ ] Add a `tests/` suite; modules only carry `__main__` demos today.

## Correctness gaps

- [ ] Stress prediction is not implemented (no rule-based or ML stress placement).
- [ ] CRF models are overfit on the ~150-word corpus; the reported PER numbers are not robust.
- [ ] Dialect coverage is partial — only irregular-form lookups for Central, Raiano, Sendinese; expand exceptions per dialect.

## Code TODOs

- [ ] Move the duplicated PER computation out of the per-module `__main__` blocks into a shared `evaluate_on_gold` in `mwl_phonemizer/base.py`:
  - `crf_espeak_mwl.py:22`
  - `char_lookup_mwl.py:114`
  - `crf_ortho_mwl.py:24`
  - `crf_mwl.py:246`
  - `epitran_mwl.py:197`
  - `crf_epitran_mwl.py:22`
  - `espeak_mwl.py:251`
  - `orthography_hand_rules.py:389`
  - `ngram_mwl.py:168`
