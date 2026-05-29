"""Train a character-level CRF on inline word/IPA pairs and predict with it.

Run::

    python examples/06_train_custom_crf.py
"""
from mwl_phonemizer import CRFPhonemizer
from mwl_phonemizer.crf_mwl import AlignmentStrategy, align_with_lev


def main() -> None:
    # Tiny inline aligned dataset (orthography, gold IPA).
    pairs = [
        ("lhéngua", "ʎɛ̃ɡwɐ"),
        ("mirandesa", "miɾɐ̃dezɐ"),
        ("fuogo", "fwoɡu"),
        ("alhá", "ɐʎa"),
    ]

    # Passing train_data trains immediately on those pairs instead of the gold dict.
    eng = CRFPhonemizer(train_data=pairs, ignore_stress=True,
                        strategy=AlignmentStrategy.LEV)
    print("model trained:", eng.model is not None)

    for word, gold in pairs:
        got = eng.phonemize(word, lookup_word=False)
        print(f"  {word:<12} gold={gold:<12} got={got}")

    # The Levenshtein aligner the CRF trains on, shown directly.
    inp, ref = align_with_lev("fuogo", "fwoɡu")
    print("aligned input:", inp)
    print("aligned gold :", ref)


if __name__ == "__main__":
    main()
