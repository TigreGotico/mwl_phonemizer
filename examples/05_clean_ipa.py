"""Normalise IPA output with the base-class marker and stress helpers.

Run::

    python examples/05_clean_ipa.py
"""
from mwl_phonemizer.base import MirandesePhonemizer


def main() -> None:
    samples = [
        "ˈe(j).ʒɛmˈplu",
        "miɾɐ̃ˈdes̺",
        "ʎɛ̃ˈɡwɐ",
    ]
    print(f"{'raw':<16}{'no markers':<16}{'no stress':<16}")
    for ipa in samples:
        no_markers = MirandesePhonemizer.strip_markers(ipa)
        no_stress = MirandesePhonemizer.strip_stress(ipa)
        print(f"{ipa:<16}{no_markers:<16}{no_stress:<16}")

    # The helpers compose — drop both syllable/optional markers and stress.
    fully_clean = MirandesePhonemizer.strip_stress(
        MirandesePhonemizer.strip_markers("ˈe(j).ʒɛmˈplu")
    )
    print("fully clean    :", fully_clean)


if __name__ == "__main__":
    main()
