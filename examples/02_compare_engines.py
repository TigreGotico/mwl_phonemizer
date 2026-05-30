"""Compare every dependency-free engine on the same Mirandese words.

Run::

    python examples/02_compare_engines.py
"""
from mwl_phonemizer import (
    LookupTableMWL,
    NgramMWLPhonemizer,
    OrthographyRulesMWL,
    CRFOrthoCorrector,
)


def main() -> None:
    engines = [
        LookupTableMWL(),
        NgramMWLPhonemizer(n=4),
        OrthographyRulesMWL(),
        CRFOrthoCorrector(),
    ]
    words = ["lhéngua", "mirandesa", "houmanos", "fuogo"]

    header = "engine".ljust(22) + "  ".join(w.ljust(12) for w in words)
    print(header)
    print("-" * len(header))
    for eng in engines:
        # lookup_word=False forces the engine path so the gold dict does not shadow it
        cells = [eng.phonemize(w, lookup_word=False).ljust(12) for w in words]
        print(type(eng).__name__.ljust(22) + "  ".join(cells))


if __name__ == "__main__":
    main()
