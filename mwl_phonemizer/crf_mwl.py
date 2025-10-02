from mwl_phonemizer.base import MirandesePhonemizer, Dialects


class CRFPhonemizer(MirandesePhonemizer):
    def __init__(self, crf_model_path: str | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crf_model_path = crf_model_path
        self.model = None
        if crf_model_path and os.path.exists(crf_model_path):
            self.load_model(crf_model_path)
        else:
            # Prepare training data from GOLD dictionary
            train_data = list(self.GOLD.items())  # [(word, ipa), ...]
            # Train CRF
            self.train_crf(train_data)

    def _word_to_features(self, word):
        # Simple character-level features for CRF
        features = []
        for i, char in enumerate(word):
            feats = {
                'char': char,
                'is_first': i == 0,
                'is_last': i == len(word) - 1,
                'prev_char': '' if i == 0 else word[i - 1],
                'next_char': '' if i == len(word) - 1 else word[i + 1],
                'is_upper': char.isupper(),
                'is_digit': char.isdigit()
            }
            features.append(feats)
        return features

    def train_crf(self, train_data):
        # train_data: list of (word, ipa) pairs
        X, y = [], []
        for word, ipa in train_data:
            if len(word) != len(ipa):
                # If word and IPA lengths differ, use character-level alignment with padding
                # This is a simple heuristic: repeat last IPA to match word length
                ipa_aligned = list(ipa)
                while len(ipa_aligned) < len(word):
                    ipa_aligned.append(ipa_aligned[-1])
                ipa_aligned = ipa_aligned[:len(word)]
            else:
                ipa_aligned = list(ipa)
            X.append(self._word_to_features(word))
            y.append(ipa_aligned)

        import sklearn_crfsuite # imported here so it's optional
        self.model = sklearn_crfsuite.CRF(
            algorithm='lbfgs',
            c1=0.1,
            c2=0.1,
            max_iterations=100,
            all_possible_transitions=True
        )
        self.model.fit(X, y)

        if self.crf_model_path:
            self.save_model(self.crf_model_path)

    def phonemize(self, word: str, lookup_word: bool = True) -> str:
        if lookup_word and word.lower() in self.GOLD:
            return self.GOLD[word.lower()]
        if not self.model:
            raise ValueError("CRF model is not trained or loaded.")
        features = self._word_to_features(word)
        pred = self.model.predict_single(features)
        return ''.join(pred)

    def save_model(self, path: str):
        import joblib
        joblib.dump(self.model, path)

    def load_model(self, path: str):
        import joblib
        self.model = joblib.load(path)


if __name__ == "__main__":
    phonemizer = CRFPhonemizer(dialect=Dialects.CENTRAL)



    # Evaluate on the same data (overfitting expected due to small dataset)
    stats = phonemizer.evaluate_on_gold(limit=None, detailed=False, show_changes=False)

    # --- Compute PER (Phoneme Error Rate) ---  # TODO - move this to evaluate_on_gold
    total_ref_len_stress = sum(len(v) for v in phonemizer.GOLD.values())
    total_ref_len_no_stress = sum(len(phonemizer.strip_stress(v)) for v in phonemizer.GOLD.values())

    per = stats['avg_edit_distance'] * stats['counts'] / total_ref_len_stress

    per_no_stress = stats['avg_edit_distance_no_stress'] * stats['counts'] / total_ref_len_no_stress

    # --- Print Summary Metrics ---
    print("\n" + "=" * 50)
    print("      Mirandese Phonemizer Rule Evaluation")
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
    #       Mirandese Phonemizer Rule Evaluation
    # ==================================================
    # Total Words Evaluated: 145
    #
    # ## Phoneme Error Rate (PER, Full IPA Match, includes stress)
    # PER:    20.25%
    #
    # ## Phoneme Error Rate (PER, Stress-Agnostic)
    # PER:    20.76%
    #
    # --- Incorrectly Phonemized Words (Full IPA Match ED > 0) ---
    # Total Incorrect: 117 words
    #
    # Word                 | Gold            | Phonemized      | ED After
    # ---------------------------------------------------------------------------
    # hai                  | aj              | ɐˈj             | 2
    # más                  | mas̺            | mas             | 1
    # mais                 | majs̺           | ˈmaj            | 3
    # deimingo             | dejˈmĩgʊ        | ˈdɨˈmĩgʊ        | 3
    # abandono             | abɐ̃ˈdonu       | abɐ̃ˈdon        | 1
    # adbertido            | ɐdbɨɾˈtidu      | ɐdbɨɾˈtid       | 1
    # adulto               | ɐˈdultu         | ɐˈdult          | 1
    # afamado              | ɐfɐˈmadu        | ɐfɐˈmad         | 1
    # afeito               | ɐˈfejtʊ         | ɐˈfejt          | 1
    # alternatibo          | altɨɾnɐˈtibu    | altɨˈnɐˈtib     | 2
    # ambesible            | ɐ̃bɨˈs̺iblɨ     | ɐ̃bɨˈs̺ib       | 2
    # amouchado            | amowˈtʃaðu      | ɐmowˈtʃad       | 3
    # amportante           | ɐ̃puɾˈtɐ̃tɨ     | ɐ̃puɾtɐ̃tɨ      | 1
    # ampressionante       | ɐ̃pɾɨsjuˈnɐ̃tɨ  | ɐ̃pɾɨˈs̺inɐ̃tɨ  | 4
    # anchir               | ɐ̃ˈtʃiɾ         | ɐ̃ˈtʃi          | 1
    # antender             | ɐ̃tɨ̃ˈdeɾ       | ɐ̃tɨ̃ˈde        | 1
    # arena                | ɐˈɾenɐ          | ɐˈɾen           | 1
    # açpuis               | ɐsˈpujs̺        | ɐ̃ˈpuj          | 3
    # berde                | ˈveɾdɨ          | ˈβeɾd           | 2
    # besible              | bɨˈz̺iblɨ       | bɨˈs̺ib         | 3
    # bexanar              | bɨʃɐˈnaɾ        | bɨʃɐˈna         | 1
    # bibal                | biˈβaɫ          | biˈβa           | 1
    # bielho               | bjɛʎu           | ˈβjɛʎu          | 2
    # biúba                | biˈuβɐ          | biˈbɐ           | 2
    # burmeilho            | buɾˈmɐjʎu       | buɾˈmɐˈʎu       | 1
    # cabresto             | kɐˈbɾeʃtu       | kɐˈbɾeʃt        | 1
    # cheno                | ˈtʃenu          | ˈtʃen           | 1
    # chober               | tʃuˈβeɾ         | tʃuˈβe          | 1
    # ciguonha             | s̻iˈɣwoɲɐ       | s̻iˈɣwoɲ        | 1
    # dafeito              | ðɐˈfejtʊ        | ðɐˈfejt         | 1
    # defícel              | dɨˈfisɛl        | dɨˈfisɛ         | 1
    # eigual               | ɐjˈɡwal         | ɐjˈɡwa          | 1
    # era                  | ˈɛɾɐ            | ˈɛɾ             | 1
    # eras                 | ˈɛɾɐs̺          | ˈɛɾɐ            | 2
    # feliç                | fɨˈlis̻         | fɨˈli           | 2
    # fierro               | ˈfjɛru          | ˈfjeɾu          | 2
    # francesa             | fɾɐ̃ˈsɛzɐ       | fɾɐ̃ˈsɛz        | 1
    # francesas            | fɾɐ̃ˈsɛzɐs̺     | fɾɐ̃ˈsɛzɐ       | 2
    # franceses            | fɾɐ̃ˈsɛzɨs̺     | fɾɐ̃ˈsɛzɨ       | 2
    # francés              | fɾɐ̃ˈsɛs̺       | fɾɐ̃ˈsɛ         | 2
    # fui                  | fuj             | ˈfi             | 3
    # fumos                | ˈfumus̺         | ˈfumu           | 2
    # fuorte               | ˈfwɔɾtɨ         | ˈfwɔɾt          | 1
    # fuortemente          | fwɔɾtɨˈmẽtɨ     | ˈfuɾtɨˈmẽtɨ     | 3
    # fuorça               | ˈfwɔɾs̻ɐ        | ˈfwɔɾɐ          | 2
    # fuste                | ˈfus̺tɨ         | ˈfus̺           | 2
    # fácele               | ˈfasɨlɨ         | ˈfasɨl          | 1
    # guapo                | ˈɡwapu          | ˈɡwap           | 1
    # haber                | ɐˈβeɾ           | ɐˈbɨɾ           | 2
    # l                    | l̩              | l               | 1
    # lhabrar              | ʎɐˈbɾaɾi        | ˈʎabɾaɾ         | 4
    # lhimpo               | ˈʎĩpʊ           | ˈʎĩpʊʊ          | 1
    # lhobo                | ˈʎobʊ           | ˈʎobu           | 1
    # lhuç                 | ˈʎus̻           | ˈʎus            | 1
    # luç                  | ˈʎus̻           | ˈʎu             | 2
    # macado               | mɐˈkadu         | mɐˈkad          | 1
    # maias                | ˈmajɐs̺         | ˈmajɐ           | 2
    # mirandés             | miɾɐ̃ˈdes̺      | miɾɐ̃ˈdu        | 3
    # molineiro            | mʊliˈnei̯rʊ     | mʊliˈnejɾ       | 4
    # molino               | muˈlinu         | muˈlin          | 1
    # muola                | ˈmu̯olɐ         | ˈmuˈl           | 3
    # ne l                 | nɨl             | nɨll            | 1
    # neçairo              | nɨˈsajɾu        | nɨˈsajɾ         | 1
    # nuobo                | ˈnwoβʊ          | ˈnwoβ           | 1
    # nó                   | ˈnɔ             | ˈn              | 1
    # oucidental           | ows̻idẽˈtal     | ows̻idɨˈta      | 2
    # oufecialmente        | owfɨˌsjalˈmẽtɨ  | owfɨˈs̺ɐˈmẽtɨ   | 4
    # ourdenhar            | ou̯ɾdɨˈɲaɾ      | owɔɾdɨˈɲa       | 3
    # oureginal            | owɾɨʒiˈnal      | owɾɨʒiˈna       | 1
    # ourganizaçon         | ou̯rɡɐnizɐˈsõ   | ou̯rɡɐnizɐˈn    | 2
    # ouropeu              | owɾuˈpew        | owɾuˈpe         | 1
    # ourriêta             | ˈowrjetɐ        | owˈrjetɐ        | 2
    # paxarina             | pɐʃɐˈɾinɐ       | pɐʃɐˈɾin        | 1
    # pequeinho            | pɨˈkɐiɲu        | pɨˈkɐjˈɲu       | 2
    # piranha              | piˈraɲɐ         | piˈɾɐˈɲ         | 4
    # puis                 | ˈpujs̺          | ˈpuj            | 2
    # pul                  | ˈpul            | ˈpu             | 1
    # puorta               | ˈpwoɾtɐ         | ˈpwɔɾt          | 2
    # purmeiro             | puɾˈmɐjɾu       | puɾˈmɐjɾ        | 1
    # quaije               | ˈkwajʒɨ         | ˈkwajʒ          | 1
    # quando               | ˈkwɐ̃du         | ˈkɐ̃ˈd          | 3
    # quelobrinas          | kɨluˈbrinas̺    | kɨluˈbɾiˈnɐ     | 5
    # rabielho             | rɐˈβjeʎu        | ɾɐˈβjɛʎu        | 2
    # rico                 | ˈriku           | ˈrik            | 1
    # salir                | s̺ɐˈliɾ         | ˈsali           | 5
    # screbir              | s̺krɨˈβiɾ       | s̺kɨˈβi         | 2
    # segar                | s̺ɨˈɣaɾ         | s̺ɨˈɣ           | 2
    # ser                  | ˈseɾ            | ˈse             | 1
    # sida                 | ˈsidɐ           | ˈsid            | 1
    # sidas                | ˈsidɐs̺         | ˈsidɐ           | 2
    # sido                 | ˈsidu           | ˈsid            | 1
    # sidos                | ˈsidus̺         | ˈsidu           | 2
    # simple               | ˈs̺ĩplɨ         | ˈs̺ĩpl          | 1
    # sobrino              | s̺uˈbɾinu       | s̺uˈɾin         | 2
    # sodes                | ˈsodɨs̺         | ˈsodɨ           | 2
    # somos                | ˈsomus̺         | ˈsomu           | 2
    # sou                  | ˈsow            | ˈso             | 1
    # spanha               | ˈs̺pɐɲɐ         | ˈs̺ɐˈɲ          | 3
    # squierdo             | ˈs̺kjeɾdu       | ˈs̺kjeɾd        | 1
    # sós                  | ˈs̺ɔs̺          | ˈs̺             | 3
    # talbeç               | talˈbes         | talˈbe          | 1
    # tascar               | tɐs̺ˈkaɾ        | tas̺ka          | 3
    # tener                | tɨˈneɾ          | tɨˈne           | 1
    # trasdonte            | ˈtɾɐz̺dõtɨ      | ˈtɾɐz̺dõt       | 1
    # ye                   | ˈje             | ˈj              | 1
    # yê                   | ˈje             | ˈj              | 1
    # zastre               | ˈzas̺tɾɨ        | ˈzɐs̺ɨ          | 3
    # zeigual              | zɐjˈɡwal        | zɐjˈɡwa         | 1
    # áfrica               | ˈafɾikɐ         | ˈafɾik          | 1
    # çcansar              | skɐ̃ˈs̺aɾ       | skɐ̃ˈs̺         | 2
    # çcrebir              | skɾɨˈβiɾ        | skɾɨˈβi         | 1
    # érades               | ˈɛɾɐdɨs̺        | ˈɛɾɐdɨ          | 2
    # éramos               | ˈɛɾɐmus̺        | ˈɛɾɐmu          | 2
    # éran                 | ˈɛɾɐn           | ˈɛɾɐ            | 1
    # ũ                    | ˈũ              | ˈ               | 1
    # ũa                   | ˈũŋɐ            | ˈũ              | 2
    # ua                   | ˈũŋɐ            | ˈũ              | 2