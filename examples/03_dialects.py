"""Phonemize the same words under each Mirandese dialect.

Run::

    python examples/03_dialects.py
"""
from mwl_phonemizer import NgramMWLPhonemizer
from mwl_phonemizer.base import Dialects


def main() -> None:
    words = ["lhéngua", "lhibres", "alhá"]

    for dialect in (Dialects.CENTRAL, Dialects.RAIANO, Dialects.SENDINESE):
        eng = NgramMWLPhonemizer(n=4, dialect=dialect)
        transcriptions = [eng.phonemize(w, lookup_word=False) for w in words]
        print(f"{dialect.value:10}", "  ".join(transcriptions))


if __name__ == "__main__":
    main()
