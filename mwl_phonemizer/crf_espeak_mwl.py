from mwl_phonemizer.base import MirandesePhonemizer, Dialects
from mwl_phonemizer.espeak_mwl import _EspeakPhonemizer
import os


class CRFEspeakCorrector(MirandesePhonemizer):
    def __init__(self, crf_model_path: str | None = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crf_model_path = crf_model_path
        self.model = None
        self.espeak = _EspeakPhonemizer()
        if crf_model_path and os.path.exists(crf_model_path):
            self.load_model(crf_model_path)
        else:
            # Prepare training data: (espeak_ipa, gold_ipa)
            train_data = [(self.espeak.phonemize_string(word), gold)
                          for word, gold in self.GOLD.items()]
            self.train_crf(train_data)

    def _ipa_to_features(self, ipa_seq: str):
        features = []
        for i, char in enumerate(ipa_seq):
            feats = {
                'char': char,
                'is_first': i == 0,
                'is_last': i == len(ipa_seq) - 1,
                'prev_char': '' if i == 0 else ipa_seq[i - 1],
                'next_char': '' if i == len(ipa_seq) - 1 else ipa_seq[i + 1],
                'prev_char2': '' if i < 2 else ipa_seq[i - 2],
                'next_char2': '' if i >= len(ipa_seq) - 2 else ipa_seq[i + 2]
            }
            features.append(feats)
        return features

    def train_crf(self, train_data):
        import sklearn_crfsuite
        X, y = [], []
        for espeak_ipa, gold_ipa in train_data:
            gold_ipa = self.strip_markers(gold_ipa)
            if len(espeak_ipa) != len(gold_ipa):
                gold_aligned = list(gold_ipa)
                while len(gold_aligned) < len(espeak_ipa):
                    gold_aligned.append(".")
                gold_aligned = gold_aligned[:len(espeak_ipa)]
            else:
                gold_aligned = list(gold_ipa)
            X.append(self._ipa_to_features(espeak_ipa))
            y.append(gold_aligned)

        self.model = sklearn_crfsuite.CRF(
            algorithm='lbfgs',
            c1=0.1,
            c2=0.1,
            max_iterations=1000,
            all_possible_transitions=True
        )
        self.model.fit(X, y)

        if self.crf_model_path:
            self.save_model(self.crf_model_path)

    def phonemize(self, word: str, lookup_word: bool = True) -> str:
        word = word.lower().strip()
        if lookup_word and word in self.GOLD:
            return self.GOLD[word]
        if not self.model:
            raise ValueError("CRF model is not trained or loaded.")
        espeak_ipa = self.espeak.phonemize_string(word)
        features = self._ipa_to_features(espeak_ipa)
        pred = self.model.predict_single(features)
        phones = ''.join(pred).strip(".")
        return phones

    def save_model(self, path: str):
        import joblib
        joblib.dump(self.model, path)

    def load_model(self, path: str):
        import joblib
        self.model = joblib.load(path)


if __name__ == "__main__":
    phonemizer = CRFEspeakCorrector(dialect=Dialects.CENTRAL)

    # Evaluate on the same data (overfitting expected due to small dataset)
    stats = phonemizer.evaluate_on_gold(limit=None, detailed=False, show_changes=False)

    # --- Compute PER (Phoneme Error Rate) ---  # TODO - move this to evaluate_on_gold
    total_ref_len_stress = sum(len(v) for v in phonemizer.GOLD.values())
    total_ref_len_no_stress = sum(len(phonemizer.strip_stress(v)) for v in phonemizer.GOLD.values())

    per = stats['avg_edit_distance'] * stats['counts'] / total_ref_len_stress

    per_no_stress = stats['avg_edit_distance_no_stress'] * stats['counts'] / total_ref_len_no_stress

    # --- Print Summary Metrics ---
    print("\n" + "=" * 50)
    print("      Mirandese Phonemizer Espeak+CRF Evaluation")
    print("=" * 50)
    print(f"Total Words Evaluated: {stats['counts']}\n")

    print("## Phoneme Error Rate (PER, Full IPA Match, includes stress)")
    print(f"PER:    {per:.2%}")

    print("\n## Phoneme Error Rate (PER, Stress-Agnostic)")
    print(f"PER:    {per_no_stress:.2%}")

    # --- Print only 'wrong' words (ED > 0) ---
    print("\n--- Incorrectly Phonemized Words (Full IPA Match ED > 0) ---")
    wrong_words = stats.get("details", [])

    if wrong_words:
        print(f"Total Incorrect: {len(wrong_words)} words\n")

        # Print a header for the detailed list
        print(f"{'Word':<20} | {'Gold':<15} | {'Phonemized':<15} | {'ED After':<8}")
        print("-" * 75)

        # Print the detailed list
        for d in wrong_words:
            print(
                f"{d['word']:<20} | {d['gold']:<15} | {d['phonemes']:<15} | {d['ed']:<8}")
    else:
        print("All words achieved an exact match (100% Accuracy)!")

    # ==================================================
    #       Mirandese Phonemizer Espeak+CRF Evaluation
    # ==================================================
    # Total Words Evaluated: 145
    #
    # ## Phoneme Error Rate (PER, Full IPA Match, includes stress)
    # PER:    3.72%
    #
    # ## Phoneme Error Rate (PER, Stress-Agnostic)
    # PER:    4.26%
    #
    # --- Incorrectly Phonemized Words (Full IPA Match ED > 0) ---
    # Total Incorrect: 35 words
    #
    # Word                 | Gold            | Phonemized      | ED After
    # ---------------------------------------------------------------------------
    # amouchado            | amowˈtʃaðu      | amowˈtʃað       | 1
    # bibal                | biˈβaɫ          | biˈβal          | 1
    # biolento             | bjuˈlẽtu        | bjuˈlẽtɨ        | 1
    # cheno                | ˈtʃenu          | ˈtʃen           | 1
    # chober               | tʃuˈβeɾ         | tʃuˈβe          | 1
    # eras                 | ˈɛɾɐs̺          | ˈɛɾɐs           | 1
    # feliç                | fɨˈlis̻         | fɨˈlis          | 1
    # fumos                | ˈfumus̺         | ˈfumus          | 1
    # fuste                | ˈfus̺tɨ         | ˈfus̺t          | 1
    # lhabrar              | ʎɐˈbɾaɾi        | ʎɐˈbɾaɾ         | 1
    # lhobo                | ˈʎobʊ           | ˈʎoβʊ           | 1
    # lhuç                 | ˈʎus̻           | ˈʎus            | 1
    # luç                  | ˈʎus̻           | ˈʎus            | 1
    # maias                | ˈmajɐs̺         | ˈmajɐs          | 1
    # muola                | ˈmu̯olɐ         | ˈmu̯ol          | 1
    # puis                 | ˈpujs̺          | ˈpujs           | 1
    # pul                  | ˈpul            | ˈpu             | 1
    # puorta               | ˈpwoɾtɐ         | ˈpwɔɾtɐ         | 1
    # quelobrinas          | kɨluˈbrinas̺    | kɨluˈbɾinas̺    | 1
    # quemun               | kɨˈmun          | kɨˈmu           | 1
    # salir                | s̺ɐˈliɾ         | s̺ɐˈli          | 1
    # screbir              | s̺krɨˈβiɾ       | skɾɨˈβiɾ        | 2
    # segar                | s̺ɨˈɣaɾ         | s̺ɨˈɣa          | 1
    # sidas                | ˈsidɐs̺         | ˈsidɐs          | 1
    # sidos                | ˈsidus̺         | ˈsidus          | 1
    # sodes                | ˈsodɨs̺         | ˈsodɨs          | 1
    # somos                | ˈsomus̺         | ˈsomus          | 1
    # spanha               | ˈs̺pɐɲɐ         | ˈs̺pɐ           | 2
    # sós                  | ˈs̺ɔs̺          | ˈs̺ɔ            | 2
    # tascar               | tɐs̺ˈkaɾ        | tɐs̺ˈka         | 1
    # zastre               | ˈzas̺tɾɨ        | ˈzas̺tɾ         | 1
    # érades               | ˈɛɾɐdɨs̺        | ˈɛɾɐdɨs         | 1
    # éramos               | ˈɛɾɐmus̺        | ˈɛɾɐmus         | 1
    # ũa                   | ˈũŋɐ            | ˈũŋ             | 1
    # ua                   | ˈũŋɐ            | ˈũŋ             | 1