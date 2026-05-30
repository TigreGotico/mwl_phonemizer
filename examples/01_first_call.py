"""Phonemize a Mirandese sentence with the headline CRF+rules engine.

Run::

    python examples/01_first_call.py
"""
from mwl_phonemizer import CRFOrthoCorrector


def main() -> None:
    phonemizer = CRFOrthoCorrector()

    sentences = [
        "Muitas lhénguas ténen proua de ls sous pergaminos antigos.",
        "Todos ls seres houmanos nácen lhibres i eiguales an honra i an dreitos.",
        "Hai más fuogo alhá, i ye deimingo!",
    ]
    for text in sentences:
        print("Original :", text)
        print("IPA      :", phonemizer.phonemize_sentence(text))
        print()


if __name__ == "__main__":
    main()
