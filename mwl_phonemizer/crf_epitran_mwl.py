from mwl_phonemizer.base import MirandesePhonemizer, Dialects
import os


class CRFEpitranCorrector(MirandesePhonemizer):
    def __init__(self, crf_model_path: str | None = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crf_model_path = crf_model_path
        self.model = None
        import epitran
        self.epitran = epitran.Epitran("por-Latn")
        if crf_model_path and os.path.exists(crf_model_path):
            self.load_model(crf_model_path)
        else:
            # Prepare training data: (epitran_ipa, gold_ipa)
            train_data = [(self.epitran.transliterate(word), gold)
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
        for epitran_ipa, gold_ipa in train_data:
            gold_ipa = self.strip_markers(gold_ipa)
            if len(epitran_ipa) != len(gold_ipa):
                gold_aligned = list(gold_ipa)
                while len(gold_aligned) < len(epitran_ipa):
                    gold_aligned.append(".")
                gold_aligned = gold_aligned[:len(epitran_ipa)]
            else:
                gold_aligned = list(gold_ipa)
            X.append(self._ipa_to_features(epitran_ipa))
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
        epitran_ipa = self.epitran.transliterate(word)
        features = self._ipa_to_features(epitran_ipa)
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
    phonemizer = CRFEpitranCorrector(dialect=Dialects.CENTRAL)

    # Evaluate on the same data (overfitting expected due to small dataset)
    stats = phonemizer.evaluate_on_gold(limit=None, detailed=False, show_changes=False)

    # --- Compute PER (Phoneme Error Rate) ---  # TODO - move this to evaluate_on_gold
    total_ref_len_stress = sum(len(v) for v in phonemizer.GOLD.values())
    total_ref_len_no_stress = sum(len(phonemizer.strip_stress(v)) for v in phonemizer.GOLD.values())

    per = stats['avg_edit_distance'] * stats['counts'] / total_ref_len_stress

    per_no_stress = stats['avg_edit_distance_no_stress'] * stats['counts'] / total_ref_len_no_stress

    # --- Print Summary Metrics ---
    print("\n" + "=" * 50)
    print("      Mirandese Phonemizer Epitran+CRF Evaluation")
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
    #       Mirandese Phonemizer Epitran+CRF Evaluation
    # ==================================================
    # Total Words Evaluated: 145
    #
    # ## Phoneme Error Rate (PER, Full IPA Match, includes stress)
    # PER:    16.54%
    #
    # ## Phoneme Error Rate (PER, Stress-Agnostic)
    # PER:    18.97%
    #
    # --- Incorrectly Phonemized Words (Full IPA Match ED > 0) ---
    # Total Incorrect: 110 words
    #
    # Word                 | Gold            | Phonemized      | ED After
    # ---------------------------------------------------------------------------
    # más                  | mas̺            | mas             | 1
    # mais                 | majs̺           | majs            | 1
    # alhá                 | ɐˈʎa            | ɐˈʎ             | 1
    # abandono             | abɐ̃ˈdonu       | abɐ̃ˈdon        | 1
    # adbertido            | ɐdbɨɾˈtidu      | ɐdbɨɾˈtid       | 1
    # adulto               | ɐˈdultu         | ɐˈdult          | 1
    # afamado              | ɐfɐˈmadu        | ɐfɐˈmad         | 1
    # afeito               | ɐˈfejtʊ         | ɐˈfejt          | 1
    # afelhado             | ɐfɨˈʎadu        | ɐfɨˈʎad         | 1
    # alternatibo          | altɨɾnɐˈtibu    | altɨɾnɐˈtib     | 1
    # amarielho            | ɐmɐˈɾjɛʎu       | ˈmɐˈɾjɛʎ        | 2
    # ambesible            | ɐ̃bɨˈs̺iblɨ     | ɐ̃bɨˈs̺ib       | 2
    # amouchado            | amowˈtʃaðu      | ɐmowˈtʃad       | 3
    # amportante           | ɐ̃puɾˈtɐ̃tɨ     | ɐ̃puɾˈtɐ̃t      | 1
    # anchir               | ɐ̃ˈtʃiɾ         | ɐ̃ˈtʃ           | 2
    # antender             | ɐ̃tɨ̃ˈdeɾ       | ɐ̃tɨ̃ˈde        | 1
    # arena                | ɐˈɾenɐ          | ɐˈɾen           | 1
    # açpuis               | ɐsˈpujs̺        | ɐsˈpuj          | 2
    # berde                | ˈveɾdɨ          | ˈveɾd           | 1
    # besible              | bɨˈz̺iblɨ       | bɨˈs̺ib         | 3
    # bibal                | biˈβaɫ          | biˈβa           | 1
    # biúba                | biˈuβɐ          | biˈuβ           | 1
    # burmeilho            | buɾˈmɐjʎu       | buɾˈmɐjʎ        | 1
    # cabresto             | kɐˈbɾeʃtu       | kɐˈbɾeʃt        | 1
    # canhona              | kɐˈɲonɐ         | kɐˈɲon          | 1
    # cheno                | ˈtʃenu          | ˈtʃu            | 2
    # chober               | tʃuˈβeɾ         | tʃuˈβ           | 2
    # ciguonha             | s̻iˈɣwoɲɐ       | s̻iˈɣw          | 3
    # dafeito              | ðɐˈfejtʊ        | ðɐˈfejt         | 1
    # defícel              | dɨˈfisɛl        | dɨˈfisɛ         | 1
    # eigual               | ɐjˈɡwal         | ɐjˈɡw           | 2
    # era                  | ˈɛɾɐ            | ˈɛɾ             | 1
    # eras                 | ˈɛɾɐs̺          | ˈɛɾɐ            | 2
    # feliç                | fɨˈlis̻         | fɨˈli           | 2
    # fierro               | ˈfjɛru          | ˈfjɛr           | 1
    # francesa             | fɾɐ̃ˈsɛzɐ       | fɾɐ̃ˈsɛz        | 1
    # francesas            | fɾɐ̃ˈsɛzɐs̺     | fɾɐ̃ˈsɛzɐ       | 2
    # franceses            | fɾɐ̃ˈsɛzɨs̺     | fɾɐ̃ˈsɛzɨ       | 2
    # francés              | fɾɐ̃ˈsɛs̺       | fɾɐ̃ˈsɛ         | 2
    # fumos                | ˈfumus̺         | ˈfumu           | 2
    # fuorte               | ˈfwɔɾtɨ         | ˈfwɔɾt          | 1
    # fuorça               | ˈfwɔɾs̻ɐ        | ˈfwɔɾs          | 2
    # fuste                | ˈfus̺tɨ         | ˈfus̺           | 2
    # fácele               | ˈfasɨlɨ         | ˈfasɨl          | 1
    # guapo                | ˈɡwapu          | ˈɡwa            | 2
    # haber                | ɐˈβeɾ           | ɐˈβe            | 1
    # l                    | l̩              | l               | 1
    # lhabrar              | ʎɐˈbɾaɾi        | ʎɐˈbɾa          | 2
    # lhimpo               | ˈʎĩpʊ           | ˈʎĩpu           | 1
    # lhobo                | ˈʎobʊ           | ˈʎoβ            | 2
    # lhuç                 | ˈʎus̻           | ˈʎu             | 2
    # lhéngua              | ˈʎɛ̃ɡwɐ         | ˈʎɛ̃ɡ           | 2
    # luç                  | ˈʎus̻           | ˈʎu             | 2
    # macado               | mɐˈkadu         | mɐˈkad          | 1
    # maias                | ˈmajɐs̺         | ˈmajɐ           | 2
    # mirandés             | miɾɐ̃ˈdes̺      | miɾɐ̃ˈde        | 2
    # molineiro            | mʊliˈnei̯rʊ     | mʊliˈnejɾ       | 4
    # molino               | muˈlinu         | muˈlin          | 1
    # muola                | ˈmu̯olɐ         | ˈmu̯o           | 2
    # neçairo              | nɨˈsajɾu        | nɨˈsajɾ         | 1
    # nuobo                | ˈnwoβʊ          | ˈnwoβ           | 1
    # nó                   | ˈnɔ             | ˈn              | 1
    # ourdenhar            | ou̯ɾdɨˈɲaɾ      | ou̯ɾdɨˈɲa       | 1
    # ourganizaçon         | ou̯rɡɐnizɐˈsõ   | ou̯rɡɐnizɐˈs    | 1
    # piranha              | piˈraɲɐ         | piˈraɲ          | 1
    # puis                 | ˈpujs̺          | ˈpuj            | 2
    # pul                  | ˈpul            | ˈpu             | 1
    # puorta               | ˈpwoɾtɐ         | ˈpwɔɾt          | 2
    # purmeiro             | puɾˈmɐjɾu       | puɾˈmɐjɾ        | 1
    # quaije               | ˈkwajʒɨ         | ˈkwaj           | 2
    # quando               | ˈkwɐ̃du         | ˈkwad           | 3
    # quelobrinas          | kɨluˈbrinas̺    | kɨluˈbrinas     | 1
    # quemun               | kɨˈmun          | kɨˈmu           | 1
    # rabielho             | rɐˈβjeʎu        | rɐˈβjɛʎ         | 2
    # rico                 | ˈriku           | ˈrik            | 1
    # salir                | s̺ɐˈliɾ         | s̺ɐˈl           | 2
    # screbir              | s̺krɨˈβiɾ       | skɾɨˈβi         | 3
    # segar                | s̺ɨˈɣaɾ         | s̺ɨˈɣ           | 2
    # ser                  | ˈseɾ            | ˈse             | 1
    # sida                 | ˈsidɐ           | ˈsid            | 1
    # sidas                | ˈsidɐs̺         | ˈsidɐ           | 2
    # sido                 | ˈsidu           | ˈsid            | 1
    # sidos                | ˈsidus̺         | ˈsidu           | 2
    # simple               | ˈs̺ĩplɨ         | ˈs̺ĩpl          | 1
    # sobrino              | s̺uˈbɾinu       | s̺uˈbɾi         | 2
    # sodes                | ˈsodɨs̺         | ˈsodɨ           | 2
    # somos                | ˈsomus̺         | ˈsomu           | 2
    # son                  | ˈsõ             | ˈs              | 1
    # spanha               | ˈs̺pɐɲɐ         | ˈs̺pɐ           | 2
    # squierdo             | ˈs̺kjeɾdu       | ˈs̺kjeɾd        | 1
    # sós                  | ˈs̺ɔs̺          | ˈs̺             | 3
    # talbeç               | talˈbes         | talˈbe          | 1
    # tascar               | tɐs̺ˈkaɾ        | tɐs̺ˈk          | 2
    # tener                | tɨˈneɾ          | tɨˈne           | 1
    # trasdonte            | ˈtɾɐz̺dõtɨ      | ˈtɾɐz̺dõt       | 1
    # ye                   | ˈje             | ˈj              | 1
    # yê                   | ˈje             | ˈj              | 1
    # zastre               | ˈzas̺tɾɨ        | ˈzas̺t          | 2
    # zeigual              | zɐjˈɡwal        | zɐjˈɡw          | 2
    # zenhar               | zɨˈɲaɾ          | zɨˈɲa           | 1
    # áfrica               | ˈafɾikɐ         | ˈafɾik          | 1
    # çcansar              | skɐ̃ˈs̺aɾ       | skɐ̃ˈs̺         | 2
    # çcrebir              | skɾɨˈβiɾ        | skɾɨˈβi         | 1
    # çcriçon              | skɾiˈsõ         | skɾiˈs          | 1
    # érades               | ˈɛɾɐdɨs̺        | ˈɛɾɐdɨ          | 2
    # éramos               | ˈɛɾɐmus̺        | ˈɛɾɐmu          | 2
    # éran                 | ˈɛɾɐn           | ˈɛɾɐ            | 1
    # ũ                    | ˈũ              | ˈ               | 1
    # ũa                   | ˈũŋɐ            | ˈũ              | 2
    # ua                   | ˈũŋɐ            | ˈũ              | 2
