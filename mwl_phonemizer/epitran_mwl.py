"""experiment using epitran for pt-PT phonemization and then correcting the output"""
import re
from collections import Counter
from mwl_phonemizer.base import MirandesePhonemizer


class EpitranMWL(MirandesePhonemizer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        import epitran
        self.pho = epitran.Epitran("por-Latn")

    # -------------------------
    # Phonemizer interface
    # -------------------------
    def phonemize(self, word: str, lookup_word: bool = True) -> str:
        """Phonemize a single Mirandese word via epitran + correction rules."""
        if lookup_word and word.lower() in self.GOLD:
            return self.GOLD[word.lower()]
        epitran_ipa = self.pho.transliterate(word)
        corrected = self.apply_with_ortho(epitran_ipa, word)
        return corrected

    # -------------------------
    # Hand rules
    # -------------------------
    @staticmethod
    def apply_with_ortho(ipa: str, ortho: str) -> str:
        out = ipa

        # handle common standalone words, like determinants
        if ortho == "l":
            return "l̩"
        elif ortho == "ls":
            return "l̩s̺"

        # -------------------------
        # Global substitutions
        # -------------------------
        # Rhotics
        out = out.replace("ɹ", "ɾ").replace("ʁ", "r")

        # Intervocalic lenition (optional, add exceptions if needed)
        out = re.sub(r'([aeiouɐɛɔuiɨ])b([aeiouɐɛɔuiɨ])', r'β', out)
        out = re.sub(r'([aeiouɐɛɔuiɨ])d([aeiouɐɛɔuiɨ])', r'ð', out)
        out = re.sub(r'([aeiouɐɛɔuiɨ])g([aeiouɐɛɔuiɨ])', r'ɣ', out)

        # -------------------------
        # Palatalization / Nasals
        # -------------------------
        out = re.sub(r"lh", "ʎ", out)
        out = re.sub(r"nh", "ɲ", out)

        # -------------------------
        # Diphthongs and glides
        # -------------------------
        out = out.replace("aɪ", "aj")
        out = out.replace("eɪ", "ej")
        out = out.replace("oʊ", "ow")
        out = out.replace("au", "aw")

        # -------------------------
        # Nasal vowels
        # -------------------------
        out = out.replace("iŋ", "ĩ")
        out = out.replace("uŋ", "ũ")
        out = out.replace("ãŋ", "ɐ̃")
        out = out.replace("eɪŋ", "ej̃")
        out = out.replace("aɪŋ", "aj̃")
        out = out.replace("oʊŋ", "ow̃")

        # -------------------------
        # Sibilants
        # -------------------------
        if out.endswith("ʃ"):
            out = out[:-1] + "s̺"

        # sibilant context rules
        out = re.sub(r'^s(?=[^aeiouɐɛɔuiɨ])', 's̺', out)
        out = re.sub(r's(?=[eiɨ])', 's̻', out)

        # -------------------------
        # Latin clusters / consonant corrections
        # -------------------------
        out = re.sub(r'^(pl|kl|fl)', 'tʃ', out)
        out = re.sub(r'^l(?=[aeiouɐɛɔuiɨ])', 'ʎ', out)

        # -------------------------
        # Final vowel shifts
        # -------------------------
        out = re.sub(r'o$', 'u', out)

        # -------------------------
        # Orthography-specific retroflex sibilants
        # -------------------------
        if "ç" in ortho.lower() or re.search(r"c[ei]", ortho.lower()):
            out = out.replace("s̺", "s̻").replace("z̺", "z̻")

        # -------------------------
        # Stress normalization: place before main vowel
        # -------------------------
        out = re.sub(r'ˈ([^aeiouɐɛɔuiɨ]*)([aeiouɐɛɔuiɨ])', r'ˈ\2', out)

        # Misc fixes based on experimental output comparison
        out = out.replace("ɨɾə", "ɨɾ")
        out = out.replace("bˈiɾ", "ˈβiɾ")
        out = out.replace("ʃk", "s̺k")
        if ortho.startswith("be") and out.startswith("bˌe"):
            out = "bɨ" + out[3:]
        if ortho.startswith("amb") and out.startswith("ɐ̃mb"):
            out = "ɐ̃b" + out[3:]
        if ortho.endswith("uç") and out.endswith("us"):
            out = out[:-1] + "s̻"
        if out.endswith("oŋ"):
            out = out[:-2] + "õ"
        if out.endswith("ɾədʊ"):
            out = out[-4:] + "ɾdu"
        return out

    def evaluate_against_base(self, limit=None, detailed=False, show_changes=False):
        pairs = list(self.GOLD.items())
        if limit:
            pairs = pairs[:limit]

        total_ed_before = 0
        total_ed_after = 0
        cnt = 0
        improvements = Counter()
        details = []

        # Stress-agnostic metrics
        total_ed_no_stress_before = 0
        total_ed_no_stress_after = 0

        for ortho, gold_ipa in pairs:
            epitran_ipa = self.pho.transliterate(ortho)
            corrected = self.apply_with_ortho(epitran_ipa, ortho)

            # Standard metrics (includes stress)
            ed_before = self.word_edit_distance(epitran_ipa, gold_ipa)
            ed_after = self.word_edit_distance(corrected, gold_ipa)
            total_ed_before += ed_before
            total_ed_after += ed_after
            cnt += 1

            if ed_after < ed_before:
                improvements["better"] += 1
            elif ed_after == ed_before:
                improvements["same"] += 1
            else:
                improvements["worse"] += 1

            # Stress-agnostic metrics (ignores stress)
            epitran_ipa_no_stress = self.strip_stress(epitran_ipa)
            corrected_no_stress = self.strip_stress(corrected)
            gold_ipa_no_stress = self.strip_stress(gold_ipa)

            ed_before_no_stress = self.word_edit_distance(epitran_ipa_no_stress, gold_ipa_no_stress)
            ed_after_no_stress = self.word_edit_distance(corrected_no_stress, gold_ipa_no_stress)

            total_ed_no_stress_before += ed_before_no_stress
            total_ed_no_stress_after += ed_after_no_stress

            # Only append to details if the final corrected IPA does not match the gold (ED > 0)
            if ed_after > 0:
                details.append({
                    "word": ortho,
                    "epitran": epitran_ipa,
                    "corrected": corrected,
                    "gold": gold_ipa,
                    "ed_before": ed_before,
                    "ed_after": ed_after,
                })

        result = {
            # Standard Metrics
            "avg_edit_distance_before": total_ed_before / cnt if cnt else 0,
            "avg_edit_distance_after": total_ed_after / cnt if cnt else 0,

            # Stress-Agnostic Metrics
            "avg_edit_distance_no_stress_before": total_ed_no_stress_before / cnt if cnt else 0,
            "avg_edit_distance_no_stress_after": total_ed_no_stress_after / cnt if cnt else 0,

            "counts": cnt,
            "improvements": improvements,
            "details": details
        }
        return result



if __name__ == "__main__":

    pho = EpitranMWL("/run/media/miro/endeavouros/PycharmProjects/mwl_phonemizer/mwl_phonemizer/central.json")
    stats = pho.evaluate_against_base(limit=None, detailed=False, show_changes=False)

    # --- Compute PER (Phoneme Error Rate) ---  # TODO - move this to evaluate_on_gold
    total_ref_len_stress = sum(len(v) for v in pho.GOLD.values())
    total_ref_len_no_stress = sum(len(pho.strip_stress(v)) for v in pho.GOLD.values())

    per_before = stats['avg_edit_distance_before'] * stats['counts'] / total_ref_len_stress
    per_after = stats['avg_edit_distance_after'] * stats['counts'] / total_ref_len_stress

    per_no_stress_before = stats['avg_edit_distance_no_stress_before'] * stats['counts'] / total_ref_len_no_stress
    per_no_stress_after = stats['avg_edit_distance_no_stress_after'] * stats['counts'] / total_ref_len_no_stress

    # --- Print Summary Metrics ---
    print("\n" + "=" * 50)
    print("      Mirandese Phonemizer Rule Evaluation")
    print("=" * 50)
    print(f"Total Words Evaluated: {stats['counts']}\n")

    print("## Phoneme Error Rate (PER, Full IPA Match, includes stress)")
    print(f"PER (Initial Epitran): {per_before:.2%}")
    print(f"PER (After Rules):    {per_after:.2%}")

    print("\n## Phoneme Error Rate (PER, Stress-Agnostic)")
    print(f"PER (Initial Epitran): {per_no_stress_before:.2%}")
    print(f"PER (After Rules):    {per_no_stress_after:.2%}")

    # Rule Performance Breakdown
    improvements = stats['improvements']
    total_improved = improvements['better'] + improvements['worse'] + improvements['same']
    better_percent = (improvements['better'] / total_improved) if total_improved else 0
    worse_percent = (improvements['worse'] / total_improved) if total_improved else 0
    print("\n## Rule Performance (vs. Initial Epitran)")
    print(f"Words Improved: {improvements['better']} ({better_percent:.1%} of total)")
    print(f"Words Degraded: {improvements['worse']} ({worse_percent:.1%} of total)")
    print(f"Words Unchanged: {improvements['same']}\n")
    print("=" * 50)

    # --- Print only 'wrong' words (ED > 0) ---
    print("\n--- Incorrectly Phonemized Words (Full IPA Match ED > 0) ---")
    wrong_words = stats.get("details", [])

    if wrong_words:
        print(f"Total Incorrect: {len(wrong_words)} words\n")

        # Print a header for the detailed list
        print(f"{'Word':<20} | {'Gold':<15} | {'Epitran':<15} | {'Corrected':<15} | {'ED After':<8} | {'ED Before':<8}")
        print("-" * 75)

        # Print the detailed list
        for d in wrong_words:
            print(
                f"{d['word']:<20} | {d['gold']:<15} |  {d['epitran']:<15} | {d['corrected']:<15} | {d['ed_after']:<8} | {d['ed_before']:<8}")
    else:
        print("All words achieved an exact match (100% Accuracy)!")

    # ==================================================
    #       Mirandese Phonemizer Epitran Evaluation
    # ==================================================
    # Total Words Evaluated: 145
    #
    # ## Phoneme Error Rate (PER, Full IPA Match, includes stress)
    # PER (Initial Epitran): 51.37%
    # PER (After Rules):    47.26%
    #
    # ## Phoneme Error Rate (PER, Stress-Agnostic)
    # PER (Initial Epitran): 44.89%
    # PER (After Rules):    40.07%
    #
    # ## Rule Performance (vs. Initial Epitran)
    # Words Improved: 50 (34.5% of total)
    # Words Degraded: 19 (13.1% of total)
    # Words Unchanged: 76
    #
    # ==================================================
    #
    # --- Incorrectly Phonemized Words (Full IPA Match ED > 0) ---
    # Total Incorrect: 137 words
    #
    # Word                 | Gold            | Epitran         | Corrected       | ED After | ED Before
    # ---------------------------------------------------------------------------
    # alhá                 | ɐˈʎa            |  ɐla             | ɐla             | 2        | 2
    # deimingo             | dejˈmĩgʊ        |  dɛjminɡo        | dɛjminɡu        | 6        | 6
    # abandono             | abɐ̃ˈdonu       |  ɐbɐndono        | βndonu          | 5        | 4
    # adbertido            | ɐdbɨɾˈtidu      |  ɐdbɛɾtido       | ɐdbɛɾtð         | 5        | 3
    # adulto               | ɐˈdultu         |  ɐdulto          | ðltu            | 4        | 2
    # afamado              | ɐfɐˈmadu        |  ɐfɐmɐdo         | ɐfɐmð           | 4        | 3
    # afeito               | ɐˈfejtʊ         |  ɐfɛjto          | ɐfɛjtu          | 3        | 3
    # afelhado             | ɐfɨˈʎadu        |  ɐfɛlɐdo         | ɐfɛlð           | 6        | 5
    # alternatibo          | altɨɾnɐˈtibu    |  ɐltɛɾnɐtibo     | ɐltɛɾnɐtβ       | 6        | 4
    # amarielho            | ɐmɐˈɾjɛʎu       |  ɐmɐɾiɛlo        | ɐmɐɾiɛlu        | 3        | 4
    # ambesible            | ɐ̃bɨˈs̺iblɨ     |  ɐmbɛziblɛ       | ɐmbɛziblɛ       | 6        | 6
    # amouchado            | amowˈtʃaðu      |  ɐmowukɐdo       | ɐmowukð         | 6        | 7
    # amportante           | ɐ̃puɾˈtɐ̃tɨ     |  ɐmpoɾtɐntɛ      | ɐmpoɾtɐntɛ      | 5        | 5
    # ampossible           | ɐ̃puˈsiblɨ      |  ɐmpoʃsiblɛ      | ɐmpoʃs̻iblɛ     | 5        | 4
    # ampressionante       | ɐ̃pɾɨsjuˈnɐ̃tɨ  |  ɐmpɾɛʃsionɐntɛ  | ɐmpɾɛʃs̻ionɐntɛ | 8        | 8
    # anchir               | ɐ̃ˈtʃiɾ         |  ɐnkiɾ           | ɐnkiɾ           | 4        | 4
    # antender             | ɐ̃tɨ̃ˈdeɾ       |  ɐntɛndɛɾ        | ɐntɛndɛɾ        | 5        | 5
    # arena                | ɐˈɾenɐ          |  ɐɾɛnɐ           | ɐɾɛnɐ           | 2        | 2
    # açpuis               | ɐsˈpujs̺        |  ɐspujʃ          | ɐspujs̻         | 2        | 3
    # berde                | ˈveɾdɨ          |  bɛɾdɛ           | bɛɾdɛ           | 4        | 4
    # besible              | bɨˈz̺iblɨ       |  bɛziblɛ         | bɛziblɛ         | 4        | 4
    # bexanar              | bɨʃɐˈnaɾ        |  bɛksɐnɐɾ        | bɛksɐnɐɾ        | 5        | 5
    # bibal                | biˈβaɫ          |  bibɐl           | bβl             | 4        | 4
    # bielho               | bjɛʎu           |  biɛlo           | biɛlu           | 2        | 3
    # biolento             | bjuˈlẽtu        |  biolɛnto        | biolɛntu        | 5        | 6
    # biúba                | biˈuβɐ          |  biẃbɐ           | biẃbɐ           | 3        | 3
    # brabo                | bɾabu           |  bɾɐbo           | bɾβ             | 3        | 2
    # branco               | bɾɐ̃ku          |  bɾɐnko          | bɾɐnku          | 1        | 2
    # buono                | bwonu           |  buono           | buonu           | 1        | 2
    # burmeilho            | buɾˈmɐjʎu       |  buɾmɛjlo        | buɾmɛjlu        | 3        | 4
    # cabresto             | kɐˈbɾeʃtu       |  kɐbʁɛʃto        | kɐbrɛʃtu        | 3        | 4
    # canhona              | kɐˈɲonɐ         |  kɐnonɐ          | kɐnonɐ          | 2        | 2
    # cheno                | ˈtʃenu          |  kɛno            | kɛnu            | 4        | 5
    # chober               | tʃuˈβeɾ         |  kobɛɾ           | kβɾ             | 5        | 6
    # ciguonha             | s̻iˈɣwoɲɐ       |  siɡonɐ          | s̻iɡonɐ         | 4        | 5
    # dafeito              | ðɐˈfejtʊ        |  dɐfɛjto         | dɐfɛjtu         | 4        | 4
    # defrente             | dɨˈfɾẽtɨ        |  dɛfʁɛntɛ        | dɛfrɛntɛ        | 6        | 6
    # defícel              | dɨˈfisɛl        |  dɛfizɛl         | dɛfizɛl         | 3        | 3
    # drento               | ˈdɾẽtu          |  dɾɛnto          | dɾɛntu          | 3        | 4
    # eigual               | ɐjˈɡwal         |  ɛjɡɐl           | ɛjɡɐl           | 4        | 4
    # era                  | ˈɛɾɐ            |  ɛɾɐ             | ɛɾɐ             | 1        | 1
    # eras                 | ˈɛɾɐs̺          |  ɛɾɐʃ            | ɛɾɐs̺           | 1        | 3
    # feliç                | fɨˈlis̻         |  fɛlis           | fɛlis           | 3        | 3
    # fierro               | ˈfjɛru          |  fiɛʁo           | fiɛru           | 2        | 4
    # francesa             | fɾɐ̃ˈsɛzɐ       |  fɾɐnsɛzɐ        | fɾɐnsɛzɐ        | 2        | 2
    # francesas            | fɾɐ̃ˈsɛzɐs̺     |  fɾɐnsɛzɐʃ       | fɾɐnsɛzɐs̻      | 3        | 4
    # franceses            | fɾɐ̃ˈsɛzɨs̺     |  fɾɐnsɛzɛʃ       | fɾɐnsɛzɛs̻      | 4        | 5
    # francés              | fɾɐ̃ˈsɛs̺       |  fɾɐnseʃ         | fɾɐns̻es̺       | 4        | 5
    # fumos                | ˈfumus̺         |  fumoʃ           | fumos̺          | 2        | 4
    # fuogo                | fwoɣʊ           |  fuoɡo           | fuoɡu           | 3        | 3
    # fuonte               | ˈfwõtɨ          |  fuontɛ          | fuontɛ          | 5        | 5
    # fuorte               | ˈfwɔɾtɨ         |  fuoɾtɛ          | fuoɾtɛ          | 4        | 4
    # fuortemente          | fwɔɾtɨˈmẽtɨ     |  fuoɾtɛmɛntɛ     | fuoɾtɛmɛntɛ     | 7        | 7
    # fuorça               | ˈfwɔɾs̻ɐ        |  fuoɾsɐ          | fuoɾsɐ          | 4        | 4
    # fuste                | ˈfus̺tɨ         |  fuʃtɛ           | fuʃtɛ           | 4        | 4
    # fácele               | ˈfasɨlɨ         |  fazɛlɛ          | fazɛlɛ          | 4        | 4
    # guapo                | ˈɡwapu          |  ɡɐpo            | ɡɐpu            | 3        | 4
    # haber                | ɐˈβeɾ           |  ɐbɛɾ            | βɾ              | 3        | 3
    # houmano              | owˈmɐnu         |  owumɐno         | owumɐnu         | 1        | 2
    # lhabrar              | ʎɐˈbɾaɾi        |  lɐbʁɐɾ          | ʎɐbrɐɾ          | 4        | 5
    # lhimpo               | ˈʎĩpʊ           |  limpo           | ʎimpu           | 4        | 4
    # lhobo                | ˈʎobʊ           |  lobo            | lβ              | 5        | 3
    # lhuç                 | ˈʎus̻           |  lus             | ʎus̻            | 1        | 3
    # lhéngua              | ˈʎɛ̃ɡwɐ         |  lenɡɐ           | ʎenɡɐ           | 4        | 5
    # luç                  | ˈʎus̻           |  lus             | ʎus̻            | 1        | 3
    # macado               | mɐˈkadu         |  mɐkɐdo          | mɐkð            | 4        | 3
    # maias                | ˈmajɐs̺         |  mɐjɐʃ           | mɐjɐs̺          | 2        | 4
    # mirandés             | miɾɐ̃ˈdes̺      |  miɾɐndeʃ        | miɾɐndes̺       | 2        | 4
    # molineiro            | mʊliˈnei̯rʊ     |  molinɛjɾo       | molinɛjɾu       | 7        | 7
    # molino               | muˈlinu         |  molino          | molinu          | 2        | 3
    # muola                | ˈmu̯olɐ         |  muolɐ           | muolɐ           | 2        | 2
    # ne l                 | nɨl             |  nɛ l            | nɛ l            | 2        | 2
    # neçairo              | nɨˈsajɾu        |  nɛsajɾo         | nɛsajɾu         | 2        | 3
    # nuobo                | ˈnwoβʊ          |  nuobo           | nuβ             | 4        | 4
    # nó                   | ˈnɔ             |  nɔ              | nɔ              | 1        | 1
    # onte                 | ˈõtɨ            |  ontɛ            | ontɛ            | 3        | 3
    # oucidental           | ows̻idẽˈtal     |  owuzidɛntɐl     | owuzðntɐl       | 7        | 5
    # oufecialmente        | owfɨˌsjalˈmẽtɨ  |  owufɛziɐlmɛntɛ  | owufɛziɐlmɛntɛ  | 10       | 10
    # ourdenhar            | ou̯ɾdɨˈɲaɾ      |  owuɾdɛnɐɾ       | owuɾdɛnɐɾ       | 6        | 6
    # oureginal            | owɾɨʒiˈnal      |  owuɾɛʒinɐl      | owuɾɛʒinɐl      | 4        | 4
    # ourganizaçon         | ou̯rɡɐnizɐˈsõ   |  owuɾɡɐnizɐsõ    | owuɾɡɐnizɐsõ    | 4        | 4
    # ouropeu              | owɾuˈpew        |  owuɾopew        | owuɾopew        | 3        | 3
    # ourriêta             | ˈowrjetɐ        |  owuʁietɐ        | owurietɐ        | 3        | 4
    # paxarina             | pɐʃɐˈɾinɐ       |  pɐksɐɾinɐ       | pɐksɐɾinɐ       | 3        | 3
    # pequeinho            | pɨˈkɐiɲu        |  pɛkʷɛjno        | pɛkʷɛjnu        | 6        | 7
    # piranha              | piˈraɲɐ         |  piɾɐnɐ          | piɾɐnɐ          | 4        | 4
    # puis                 | ˈpujs̺          |  pujʃ            | pujs̺           | 1        | 3
    # pul                  | ˈpul            |  pul             | pul             | 1        | 1
    # puorta               | ˈpwoɾtɐ         |  puoɾtɐ          | puoɾtɐ          | 2        | 2
    # purmeiro             | puɾˈmɐjɾu       |  puɾmɛjɾo        | puɾmɛjɾu        | 2        | 3
    # quaije               | ˈkwajʒɨ         |  kajʒɛ           | kajʒɛ           | 3        | 3
    # quando               | ˈkwɐ̃du         |  kɐndo           | kɐndu           | 3        | 4
    # quelobrinas          | kɨluˈbrinas̺    |  kʷɛlobʁinɐʃ     | kʷɛlobrinɐs̺    | 5        | 8
    # quemun               | kɨˈmun          |  kʷɛmũ           | kʷɛmũ           | 4        | 4
    # rabielho             | rɐˈβjeʎu        |  ʁɐbiɛlo         | rβɛlu           | 5        | 7
    # rico                 | ˈriku           |  ʁiko            | riku            | 1        | 3
    # salir                | s̺ɐˈliɾ         |  sɐliɾ           | sɐliɾ           | 2        | 2
    # screbir              | s̺krɨˈβiɾ       |  skɾɛbiɾ         | s̺kɾβɾ          | 4        | 5
    # segar                | s̺ɨˈɣaɾ         |  sɛɡɐɾ           | sɛɡɐɾ           | 5        | 5
    # sendo                | ˈsẽdu           |  sɛndo           | sɛndu           | 3        | 4
    # ser                  | ˈseɾ            |  sɛɾ             | sɛɾ             | 2        | 2
    # sida                 | ˈsidɐ           |  sidɐ            | s̺ð             | 4        | 1
    # sidas                | ˈsidɐs̺         |  sidɐʃ           | s̺ðs̺           | 4        | 3
    # sido                 | ˈsidu           |  sido            | s̺ð             | 4        | 2
    # sidos                | ˈsidus̺         |  sidoʃ           | s̺ðs̺           | 4        | 4
    # simple               | ˈs̺ĩplɨ         |  simplɛ          | s̻implɛ         | 5        | 4
    # sobrino              | s̺uˈbɾinu       |  sobʁino         | sobrinu         | 4        | 5
    # sodes                | ˈsodɨs̺         |  sodɛʃ           | s̺ðs̺           | 4        | 4
    # somos                | ˈsomus̺         |  somoʃ           | somos̺          | 2        | 4
    # son                  | ˈsõ             |  sõ              | s̺õ             | 2        | 1
    # sou                  | ˈsow            |  sowu            | sowu            | 2        | 2
    # spanha               | ˈs̺pɐɲɐ         |  spɐnɐ           | s̺pɐnɐ          | 2        | 3
    # squierdo             | ˈs̺kjeɾdu       |  skʷiɛɾdo        | s̺kʷiɛɾdu       | 4        | 6
    # sós                  | ˈs̺ɔs̺          |  sɔʃ             | sɔs̺            | 2        | 4
    # talbeç               | talˈbes         |  tɐlbɛs          | tɐlbɛs          | 3        | 3
    # tamien               | tɐˈmjẽ          |  tɐmiɛ̃          | tɐmiɛ̃          | 4        | 4
    # tascar               | tɐs̺ˈkaɾ        |  tɐʃkɐɾ          | tɐs̺kɐɾ         | 2        | 4
    # tener                | tɨˈneɾ          |  tɛnɛɾ           | tɛnɛɾ           | 3        | 3
    # trasdonte            | ˈtɾɐz̺dõtɨ      |  tɾɐʃdontɛ       | tɾɐʃdontɛ       | 6        | 6
    # trasdontonte         | ˈtɾɐz̺dõtõtɨ    |  tɾɐʃdontontɛ    | tɾɐʃdontontɛ    | 8        | 8
    # ye                   | ˈje             |  jɛ              | jɛ              | 2        | 2
    # you                  | jow             |  jowu            | jowu            | 1        | 1
    # yê                   | ˈje             |  je              | je              | 1        | 1
    # zastre               | ˈzas̺tɾɨ        |  zɐʃtɾɛ          | zɐʃtɾɛ          | 5        | 5
    # zeigual              | zɐjˈɡwal        |  zɛjɡɐl          | zɛjɡɐl          | 4        | 4
    # zenhar               | zɨˈɲaɾ          |  zɛnɐɾ           | zɛnɐɾ           | 4        | 4
    # áfrica               | ˈafɾikɐ         |  afʁikɐ          | afrikɐ          | 2        | 2
    # çcansar              | skɐ̃ˈs̺aɾ       |  skɐnsɐɾ         | s̻kɐnsɐɾ        | 5        | 4
    # çcrebir              | skɾɨˈβiɾ        |  skɾɛbiɾ         | s̻kɾβɾ          | 4        | 3
    # çcriçon              | skɾiˈsõ         |  skɾisõ          | s̻kɾisõ         | 2        | 1
    # çtinto               | ˈstĩtu          |  stinto          | s̻tintu         | 4        | 4
    # érades               | ˈɛɾɐdɨs̺        |  eɾɐdɛʃ          | eɾðs̺           | 5        | 5
    # éramos               | ˈɛɾɐmus̺        |  eɾɐmoʃ          | eɾɐmos̺         | 3        | 5
    # éran                 | ˈɛɾɐn           |  eɾɐ̃            | eɾɐ̃            | 3        | 3
    # ũ                    | ˈũ              |  ũ               | ũ               | 1        | 1
    # ũa                   | ˈũŋɐ            |  ũɐ              | ũɐ              | 2        | 2
    # ua                   | ˈũŋɐ            |  uɐ              | uɐ              | 3        | 3