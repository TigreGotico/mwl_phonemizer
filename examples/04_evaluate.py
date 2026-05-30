"""Score an engine against the bundled gold dictionary and compute PER.

Run::

    python examples/04_evaluate.py
"""
from mwl_phonemizer import OrthographyRulesMWL


def main() -> None:
    eng = OrthographyRulesMWL()
    stats = eng.evaluate_on_gold()

    ref_len = sum(len(v) for v in eng.GOLD.values())
    ref_len_ns = sum(len(eng.strip_stress(v)) for v in eng.GOLD.values())

    per = stats["avg_edit_distance"] * stats["counts"] / ref_len
    per_ns = stats["avg_edit_distance_no_stress"] * stats["counts"] / ref_len_ns

    print(f"Words evaluated      : {stats['counts']}")
    print(f"PER (stress)         : {per:.2%}")
    print(f"PER (stress-agnostic): {per_ns:.2%}")
    print(f"Words with errors    : {len(stats['details'])}")
    print()
    print(f"{'word':<14}{'gold':<16}{'got':<16}ed")
    for d in stats["details"][:6]:
        print(f"{d['word']:<14}{d['gold']:<16}{d['phonemes']:<16}{d['ed']}")


if __name__ == "__main__":
    main()
