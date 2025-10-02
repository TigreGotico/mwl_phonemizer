import re
from collections import defaultdict, Counter
from mwl_phonemizer.base import MirandesePhonemizer, Dialects


class NgramMWLPhonemizer(MirandesePhonemizer):
    """
    Mirandese Phonemizer using a statistical N-gram model
    learned from Grapheme-Phoneme alignments.
    """

    def __init__(self, n: int = 4, *args, **kwargs):
        """
        Initializes the N-gram model.
        Args:
            gold_data (dict): The GOLD dictionary {ortho: ipa}.
            n (int): The size of the N-gram (e.g., n=3 uses 2 preceding graphemes).
        """
        super().__init__(*args, **kwargs)
        self.n = n
        self.g2p_model = defaultdict(Counter)
        # Padding tokens for context at word boundaries (e.g., <S><S><S> for n=4)
        self.padding = ["<S>"] * (n - 1)
        # Train the model immediately on initialization
        if self.dialect == Dialects.RAIANO:
            self.train({**self.GOLD, **self.RAIANO_GOLD})
        elif self.dialect == Dialects.SENDINESE:
            self.train({**self.GOLD, **self.SENDINESE_GOLD})
        else:
            self.train(self.GOLD)

    # -----------------------------------------------
    # 1. Grapheme-Phoneme Alignment (Simplified)
    # -----------------------------------------------

    def _align(self, grapheme: str, phoneme: str) -> list[tuple[str, str]]:
        """
        Simplified aligner to map sequences of graphemes to phonemes.
        In a statistical model, this step is CRUCIAL for accuracy.
        It uses a basic substitution and alignment for common Mirandese
        multigraphs ('lh', 'nh') and stress.
        """
        g = grapheme.lower().replace('lh', 'L̃').replace('nh', 'Ñ').replace('ch', 'Tʃ')
        p = phoneme.replace('ʎ', 'L̃').replace('ɲ', 'Ñ').replace('ʃ', 'Tʃ')

        # Split into list of single characters/multigraphs
        g_list = list(g)
        p_list = list(p)

        # Pad the shorter sequence with NULL to enable simple zip alignment.
        # This is a crude approximation of the many-to-many problem.
        max_len = max(len(g_list), len(p_list))
        g_list.extend(['<NULL>'] * (max_len - len(g_list)))
        p_list.extend(['<NULL>'] * (max_len - len(p_list)))

        aligned_pairs = []
        for g_char, p_char in zip(g_list, p_list):
            if g_char != '<NULL>' and p_char != '<NULL>':
                # Reverse the temporary substitution for the final pair
                if g_char == 'L̃': g_char = 'lh'
                if g_char == 'Ñ': g_char = 'nh'
                if g_char == 'Tʃ': g_char = 'ch'
                if p_char == 'L̃': p_char = 'ʎ'
                if p_char == 'Ñ': p_char = 'ɲ'
                if p_char == 'Tʃ': p_char = 'ʃ'

                # Strip stress from the phoneme for the mapping,
                # we'll use a separate rule for stress if needed.
                p_char = p_char.replace('ˈ', '').replace('ˌ', '')
                aligned_pairs.append((g_char, p_char))

        return aligned_pairs

    # -----------------------------------------------
    # 2. Training (G-P N-gram Counting)
    # -----------------------------------------------

    def train(self, gold_data: dict):
        """Populates the g2p_model with counts from the GOLD data."""
        for ortho, ipa in gold_data.items():
            ortho = ortho.lower()

            # 1. Align the word
            aligned_pairs = self._align(ortho, ipa)

            # Separate graphemes (inputs) and phonemes (outputs)
            graphemes_sequence = [g for g, p in aligned_pairs]
            phonemes_sequence = [p for g, p in aligned_pairs]

            # 2. Add padding to the input graphemes for context
            padded_graphemes = self.padding + graphemes_sequence + self.padding

            # 3. Count N-grams (Grapheme Context -> Phoneme)
            for i in range(len(phonemes_sequence)):
                # The current grapheme to be mapped
                g = graphemes_sequence[i]

                # The context: N-1 preceding graphemes
                context = tuple(padded_graphemes[i: i + self.n - 1])

                # The target phoneme
                p = phonemes_sequence[i]

                # Store the count: P(p | context, g) is approximated by frequency
                self.g2p_model[(context, g)][p] += 1

    # -----------------------------------------------
    # 3. Prediction (N-gram Lookup)
    # -----------------------------------------------

    def phonemize(self, word: str, lookup_word=False) -> str:
        """
        Phonemize a single word using the trained N-gram model.
        """
        word = word.lower()

        # Special case handling (can be kept if data is sparse)
        if word == "l":
            return "l̩"

        # The grapheme tokenization should ideally mirror the alignment logic
        temp_g = word.lower().replace('lh', 'L̃').replace('nh', 'Ñ').replace('ch', 'Tʃ')
        graphemes = list(temp_g)
        # Reverse the temporary substitution for the final grapheme list used in N-gram context lookup
        graphemes = [g.replace('L̃', 'lh').replace('Ñ', 'nh').replace('Tʃ', 'ch') for g in graphemes]

        # Use the tokenized graphemes for prediction and padding context
        padded_graphemes = self.padding + graphemes
        predicted_phonemes = []

        # 1. Predict phonemes for each grapheme
        for i in range(len(graphemes)):
            g = graphemes[i]
            # Context is the N-1 characters preceding the current grapheme
            context = tuple(padded_graphemes[i: i + self.n - 1])
            key = (context, g)

            if key in self.g2p_model:
                # Maximum Likelihood Estimate (MLE): choose the most frequent phoneme
                best_p = self.g2p_model[key].most_common(1)[0][0]
                predicted_phonemes.append(best_p)
            else:
                # Back-off (Simplest form: Grapheme = Phoneme)
                predicted_phonemes.append(g)

        ipa_sequence = "".join(predicted_phonemes)

        # 2. Add Stress (This still requires a hand-rule or a separate stress model)
        # Stress is typically the most complex part of G2P. For MLE, we can apply
        # a simple stress rule (e.g., penult stress common in Mirandese).
        if len(ipa_sequence) > 1 and 'ˈ' not in ipa_sequence:
            # Crude penult stress approximation
            # (Requires a full syllabification model for accuracy)
            ipa_sequence = re.sub(r'(.{1})(.{1})$', r'ˈ\1\2', ipa_sequence)

        # 3. Clean up any remaining artifacts from the back-off or alignment
        return ipa_sequence.replace('̃', '').replace('ː', '')  # Example cleanup




if __name__ == "__main__":

    pho = NgramMWLPhonemizer(n=4)

    stats = pho.evaluate_on_gold(limit=None, detailed=False, show_changes=False)

    # --- Compute PER (Phoneme Error Rate) ---  # TODO - move this to evaluate_on_gold
    total_ref_len_stress = sum(len(v) for v in pho.GOLD.values())
    total_ref_len_no_stress = sum(len(pho.strip_stress(v)) for v in pho.GOLD.values())

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

    # for N=4

    # ==================================================
    #       Mirandese Phonemizer NGRAM (n=4) Evaluation
    # ==================================================
    # Total Words Evaluated: 145
    #
    # ## Phoneme Error Rate (PER, Full IPA Match, includes stress)
    # PER:    43.93%
    #
    # ## Phoneme Error Rate (PER, Stress-Agnostic)
    # PER:    30.98%
    #
    # --- Incorrectly Phonemized Words (Full IPA Match ED > 0) ---
    # Total Incorrect: 141 words
    #
    # Word                 | Gold            | Phonemized      | ED After
    # ---------------------------------------------------------------------------
    # hai                  | aj              | aˈji            | 2
    # más                  | mas̺            | mˈas            | 2
    # mais                 | majs̺           | maˈjs           | 2
    # alhá                 | ɐˈʎa            | ɐˈL             | 2
    # deimingo             | dejˈmĩgʊ        | dɨjmĩˈgʊ        | 3
    # abandono             | abɐ̃ˈdonu       | ɐbɐdˈon         | 4
    # adbertido            | ɐdbɨɾˈtidu      | ɐdbɨɾtˈid       | 3
    # adulto               | ɐˈdultu         | ɐdduˈlt         | 3
    # afamado              | ɐfɐˈmadu        | ɐfɐmˈad         | 3
    # afeito               | ɐˈfejtʊ         | ɐffeˈjt         | 3
    # afelhado             | ɐfɨˈʎadu        | ɐffLˈad         | 4
    # alternatibo          | altɨɾnɐˈtibu    | ɐltɨɾnɐtˈib     | 4
    # amarielho            | ɐmɐˈɾjɛʎu       | ɐɐɾjɛˈL         | 4
    # ambesible            | ɐ̃bɨˈs̺iblɨ     | ɐbɨs̺ˈib        | 5
    # amouchado            | amowˈtʃaðu      | ɐowtTˈʃa        | 7
    # amportante           | ɐ̃puɾˈtɐ̃tɨ     | ɐpuɾtɐˈɨ        | 4
    # ampossible           | ɐ̃puˈsiblɨ      | ɐpusibˈib       | 5
    # ampressionante       | ɐ̃pɾɨsjuˈnɐ̃tɨ  | ɐpɾɨsjunɐˈtɨ    | 3
    # anchir               | ɐ̃ˈtʃiɾ         | ɐtˈTʃ           | 4
    # antender             | ɐ̃tɨ̃ˈdeɾ       | ɐtɨˈde          | 3
    # arena                | ɐˈɾenɐ          | ɐɾˈen           | 3
    # açpuis               | ɐsˈpujs̺        | ɐspˈuj          | 4
    # berde                | ˈveɾdɨ          | bɨeˈɾd          | 4
    # besible              | bɨˈz̺iblɨ       | bɨs̺ˈib         | 5
    # bexanar              | bɨʃɐˈnaɾ        | bɨTʃˈɐn         | 5
    # bibal                | biˈβaɫ          | biˈβa           | 1
    # bielho               | bjɛʎu           | biɛLˈL          | 4
    # biolento             | bjuˈlẽtu        | biulẽˈtu        | 3
    # biúba                | biˈuβɐ          | biˈuβ           | 1
    # brabo                | bɾabu           | bɾaˈbu          | 1
    # branco               | bɾɐ̃ku          | bɾaˈu           | 3
    # buono                | bwonu           | bwoˈnu          | 1
    # burmeilho            | buɾˈmɐjʎu       | bwɾmɐjˈL        | 4
    # bíblico              | bibliku         | bibliˈku        | 1
    # cabresto             | kɐˈbɾeʃtu       | kɐbɾeˈTʃ        | 4
    # canhona              | kɐˈɲonɐ         | kɐNˈon          | 3
    # cheno                | ˈtʃenu          | tTˈʃe           | 5
    # chober               | tʃuˈβeɾ         | tʃˈuβ           | 4
    # ciguonha             | s̻iˈɣwoɲɐ       | k̻iɣwˈoN        | 5
    # cul                  | kul             | kˈul            | 1
    # dafeito              | ðɐˈfejtʊ        | dɐfeˈjt         | 4
    # defrente             | dɨˈfɾẽtɨ        | dɨfɾẽˈtɨ        | 2
    # defícel              | dɨˈfisɛl        | dɨfiˈsɛ         | 3
    # drento               | ˈdɾẽtu          | ddɾẽˈtu         | 2
    # eigual               | ɐjˈɡwal         | jɡˈwa           | 4
    # era                  | ˈɛɾɐ            | ˈɛɾ             | 1
    # eras                 | ˈɛɾɐs̺          | ɛˈɾɐ            | 4
    # feliç                | fɨˈlis̻         | fɨˈli           | 2
    # fierro               | ˈfjɛru          | ffjɛˈru         | 2
    # francesa             | fɾɐ̃ˈsɛzɐ       | fɾɐsˈɛz         | 3
    # francesas            | fɾɐ̃ˈsɛzɐs̺     | fɾɐsɛˈzɐ        | 5
    # franceses            | fɾɐ̃ˈsɛzɨs̺     | fɾɐsɛˈzɨ        | 5
    # francés              | fɾɐ̃ˈsɛs̺       | fɾɐˈsɛ          | 3
    # fui                  | fuj             | fˈfj            | 2
    # fumos                | ˈfumus̺         | ffuˈmu          | 4
    # fuogo                | fwoɣʊ           | ffwˈɣʊ          | 2
    # fuonte               | ˈfwõtɨ          | ffwõˈtɨ         | 2
    # fuorte               | ˈfwɔɾtɨ         | ffwɔˈɾt         | 3
    # fuortemente          | fwɔɾtɨˈmẽtɨ     | ffwɔɾtmẽˈtɨ     | 4
    # fuorça               | ˈfwɔɾs̻ɐ        | ffwɔˈɾs         | 4
    # fuste                | ˈfus̺tɨ         | ffuˈs̺          | 4
    # fácele               | ˈfasɨlɨ         | ffasˈɨl         | 3
    # guapo                | ˈɡwapu          | ɡwˈap           | 3
    # haber                | ɐˈβeɾ           | ajβˈeɾ          | 3
    # houmano              | owˈmɐnu         | awmɐˈnu         | 3
    # lhabrar              | ʎɐˈbɾaɾi        | Lɐbˈɾa          | 5
    # lhimpo               | ˈʎĩpʊ           | Lĩˈpʊ           | 3
    # lhobo                | ˈʎobʊ           | Lˈob            | 3
    # lhuç                 | ˈʎus̻           | Lˈu             | 4
    # lhéngua              | ˈʎɛ̃ɡwɐ         | Lɛˈɡw           | 4
    # luç                  | ˈʎus̻           | lˈL             | 5
    # macado               | mɐˈkadu         | makˈad          | 4
    # maias                | ˈmajɐs̺         | majˈjɐ          | 4
    # mirandés             | miɾɐ̃ˈdes̺      | miɾɐˈde         | 3
    # molineiro            | mʊliˈnei̯rʊ     | mʊlineˈi̯       | 4
    # molino               | muˈlinu         | mʊlˈin          | 4
    # muola                | ˈmu̯olɐ         | mmuˈ̯o          | 4
    # ne l                 | nɨl             | nɨˈll           | 2
    # neçairo              | nɨˈsajɾu        | nɨsaˈjɾ         | 3
    # nuobo                | ˈnwoβʊ          | nnwˈoβ          | 3
    # nó                   | ˈnɔ             | ˈnn             | 1
    # onte                 | ˈõtɨ            | oõˈtɨ           | 2
    # oucidental           | ows̻idẽˈtal     | ows̻idẽˈta      | 1
    # oufecialmente        | owfɨˌsjalˈmẽtɨ  | owfɨsjalmˈtɨ    | 3
    # ourdenhar            | ou̯ɾdɨˈɲaɾ      | ow̯ɾdɨˈN        | 4
    # oureginal            | owɾɨʒiˈnal      | ow̯ɨʒiˈna       | 2
    # ourganizaçon         | ou̯rɡɐnizɐˈsõ   | ow̯rɡɐnizˈɐs    | 4
    # ouropeu              | owɾuˈpew        | ow̯uˈpe         | 2
    # ourriêta             | ˈowrjetɐ        | ow̯rjeˈtɐ       | 3
    # paxarina             | pɐʃɐˈɾinɐ       | pɐTʃɐˈɾi        | 3
    # pequeinho            | pɨˈkɐiɲu        | pɨkɐiNˈu        | 3
    # piranha              | piˈraɲɐ         | piraˈN          | 3
    # puis                 | ˈpujs̺          | ppˈuj           | 4
    # pul                  | ˈpul            | pˈpu            | 2
    # puorta               | ˈpwoɾtɐ         | ppwoˈɾt         | 3
    # purmeiro             | puɾˈmɐjɾu       | ppɾmɐˈj̯        | 5
    # quaije               | ˈkwajʒɨ         | kwaˈjʒ          | 3
    # quando               | ˈkwɐ̃du         | kwɐˈd           | 3
    # quelobrinas          | kɨluˈbrinas̺    | klubrinˈis      | 5
    # quemun               | kɨˈmun          | klmˈun          | 3
    # rabielho             | rɐˈβjeʎu        | rɐβjLˈL         | 4
    # rico                 | ˈriku           | rrˈik           | 3
    # salir                | s̺ɐˈliɾ         | ̺ˈɐl            | 5
    # screbir              | s̺krɨˈβiɾ       | ̺krˈɨβ          | 5
    # segar                | s̺ɨˈɣaɾ         | sˈɨɣ            | 4
    # sendo                | ˈsẽdu           | sẽˈdu           | 2
    # ser                  | ˈseɾ            | ˈse             | 1
    # sida                 | ˈsidɐ           | sˈid            | 3
    # sidas                | ˈsidɐs̺         | siˈdɐ           | 4
    # sido                 | ˈsidu           | sˈid            | 3
    # sidos                | ˈsidus̺         | siˈdu           | 4
    # simple               | ˈs̺ĩplɨ         | s̺ĩˈpl          | 3
    # sobrino              | s̺uˈbɾinu       | suiˈni          | 6
    # sodes                | ˈsodɨs̺         | soˈdɨ           | 4
    # somos                | ˈsomus̺         | soˈmu           | 4
    # sou                  | ˈsow            | ˈso             | 1
    # spanha               | ˈs̺pɐɲɐ         | s̺pˈɐ           | 3
    # squierdo             | ˈs̺kjeɾdu       | s̺kjeˈɾd        | 3
    # sós                  | ˈs̺ɔs̺          | ˈs̺             | 3
    # talbeç               | talˈbes         | tɐlˈbe          | 2
    # tamien               | tɐˈmjẽ          | tɐmˈjẽ          | 2
    # tascar               | tɐs̺ˈkaɾ        | tɐsˈ̺k          | 4
    # tener                | tɨˈneɾ          | tɨˈne           | 1
    # trasdonte            | ˈtɾɐz̺dõtɨ      | ttɾɐz̺dˈõɨ      | 3
    # trasdontonte         | ˈtɾɐz̺dõtõtɨ    | ttɾɐz̺dõtõˈtɨ   | 2
    # ye                   | ˈje             | j               | 2
    # you                  | jow             | ˈow             | 1
    # yê                   | ˈje             | j               | 2
    # zastre               | ˈzas̺tɾɨ        | zzasˈ̺t         | 4
    # zeigual              | zɐjˈɡwal        | zɐjɡˈwa         | 3
    # zenhar               | zɨˈɲaɾ          | zɐNˈN           | 5
    # áfrica               | ˈafɾikɐ         | afɾˈik          | 3
    # çcansar              | skɐ̃ˈs̺aɾ       | skɐˈs̺          | 3
    # çcrebir              | skɾɨˈβiɾ        | skɾɨˈɨβ         | 3
    # çtinto               | ˈstĩtu          | sstĩˈtu         | 2
    # érades               | ˈɛɾɐdɨs̺        | ɛɾɐˈdɨ          | 4
    # éramos               | ˈɛɾɐmus̺        | ɛɾɐˈmu          | 4
    # éran                 | ˈɛɾɐn           | ɛˈɾɐ            | 3
    # ũ                    | ˈũ              |                 | 2
    # ũa                   | ˈũŋɐ            | ũ               | 3
    # ua                   | ˈũŋɐ            | ũ               | 3