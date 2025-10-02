import abc
import json
import re
import os
from collections import Counter
import editdistance
from enum import Enum

class Dialects(str, Enum):
    CENTRAL = "central"
    RAIANO = "raiano"
    SENDINESE = "sendinese"


class MirandesePhonemizer:
    def __init__(self,
                 gold_dict: str | None = None,
                 raiano_dict: str | None = None,   # dialect exceptions
                 sendinese_dict: str | None = None, # dialect exceptions
                 dialect: Dialects = Dialects.CENTRAL):

        self.dialect = dialect

        gold_dict = gold_dict or f"{os.path.dirname(__file__)}/central.json"
        raiano_dict = raiano_dict or f"{os.path.dirname(__file__)}/raiano.json"
        sendinese_dict = sendinese_dict or f"{os.path.dirname(__file__)}/sendinese.json"

        with open(gold_dict, "r", encoding="utf-8") as f:
            self.GOLD = {k: self.strip_markers(v) for k, v in json.load(f).items()}
        with open(raiano_dict, "r", encoding="utf-8") as f:
            self.RAIANO_GOLD = {k: self.strip_markers(v) for k, v in json.load(f).items()}
        with open(sendinese_dict, "r", encoding="utf-8") as f:
            self.SENDINESE_GOLD = {k: self.strip_markers(v) for k, v in json.load(f).items()}

    def phonemize(self, word: str, lookup_word: bool = True) -> str:
        if lookup_word and word.lower() in self.GOLD:
            return self.GOLD[word.lower()]
        raise ValueError(f"unknown word: '{word}'")

    def phonemize_sentence(self,
                           text: str, lookup_word: bool = True):
        text = text.replace("-", " ")
        words = re.findall(r"\b\w+\b|[\W_]+", text)  # Split by words and keep punctuation/spaces
        phonemized_parts = []
        for word_or_punc in words:
            if word_or_punc.isalpha():
                phonemized_parts.append(self.phonemize(word_or_punc, lookup_word=lookup_word))
            else:
                phonemized_parts.append(word_or_punc)  # Keep punctuation and spaces as is
        return "".join(phonemized_parts)

    @staticmethod
    def strip_markers(ipa: str) -> str:
        return ipa.replace(".", "").replace("(", "").replace(")", "")  # drop syllable/optional markers

    @staticmethod
    def strip_stress(ipa: str) -> str:
        """Removes the primary stress marker 'ˈ' for stress-agnostic comparison."""
        return ipa.replace("ˈ", "").replace("ˌ", "")

    @staticmethod
    def word_edit_distance(a: str, b: str) -> int:
        return editdistance.eval(a, b)

    def evaluate_on_gold(self, limit=None, detailed=False, show_changes=False):
        pairs = list(self.GOLD.items())
        if limit:
            pairs = pairs[:limit]

        total_ed_after = 0
        cnt = 0
        improvements = Counter()
        details = []

        # Stress-agnostic metrics
        total_ed_no_stress_after = 0

        for ortho, gold_ipa in pairs:
            phonemes = self.phonemize(ortho, lookup_word=False)

            # Standard metrics (includes stress)
            ed_after = self.word_edit_distance(phonemes, gold_ipa)
            total_ed_after += ed_after
            cnt += 1

            # Stress-agnostic metrics (ignores stress)
            corrected_no_stress = self.strip_stress(phonemes)
            gold_ipa_no_stress = self.strip_stress(gold_ipa)

            ed_after_no_stress = self.word_edit_distance(corrected_no_stress, gold_ipa_no_stress)

            total_ed_no_stress_after += ed_after_no_stress

            # Only append to details if the final corrected IPA does not match the gold (ED > 0)
            if ed_after > 0:
                details.append({
                    "word": ortho,
                    "phonemes": phonemes,
                    "gold": gold_ipa,
                    "ed": ed_after,
                })

        result = {
            # Standard Metrics
            "avg_edit_distance": total_ed_after / cnt if cnt else 0,

            # Stress-Agnostic Metrics
            "avg_edit_distance_no_stress": total_ed_no_stress_after / cnt if cnt else 0,

            "counts": cnt,
            "improvements": improvements,
            "details": details
        }
        return result

