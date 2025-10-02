"""experiment using espeak for pt-PT phonemization and then correcting the output"""
import re
import subprocess
from collections import Counter

from mwl_phonemizer.base import MirandesePhonemizer


class _EspeakPhonemizer:
    """
    A phonemizer class that uses the espeak-ng command-line tool to convert text into phonemes.
    """

    @staticmethod
    def _run_espeak_command(args: list[str], input_text: str = None, check: bool = True) -> str:
        """
        Helper function to run espeak-ng commands via subprocess.
        Executes 'espeak-ng' with the given arguments and input text.
        Captures stdout and stderr, and raises EspeakError on failure.

        Args:
            args (List[str]): A list of command-line arguments for espeak-ng.
            input_text (str, optional): The text to pass to espeak-ng's stdin. Defaults to None.
            check (bool, optional): If True, raises a CalledProcessError if the command returns a non-zero exit code. Defaults to True.

        Returns:
            str: The stripped standard output from the espeak-ng command.

        Raises:
            EspeakError: If espeak-ng command is not found, or if the subprocess call fails.
        """
        command: List[str] = ['espeak-ng'] + args
        try:
            process: subprocess.CompletedProcess = subprocess.run(
                command,
                input=input_text,
                capture_output=True,
                text=True,
                check=check,
                encoding='utf-8',
                errors='replace'  # Replaces unencodable characters with a placeholder
            )
            return process.stdout.strip()
        except FileNotFoundError:
            raise EspeakError(
                "espeak-ng command not found. Please ensure espeak-ng is installed "
                "and available in your system's PATH."
            )
        except subprocess.CalledProcessError as e:
            raise EspeakError(
                f"espeak-ng command failed with error code {e.returncode}:\n"
                f"STDOUT: {e.stdout}\n"
                f"STDERR: {e.stderr}"
            )
        except Exception as e:
            raise EspeakError(f"An unexpected error occurred while running espeak-ng: {e}")

    def phonemize_string(self, text: str, lang: str = "pt") -> str:
        return self._run_espeak_command(
            ['-q', '-x', '--ipa', '-v', lang],
            input_text=text
        )


class EspeakMWL(MirandesePhonemizer):
    pho = _EspeakPhonemizer()

    # -------------------------
    # Phonemizer interface
    # -------------------------
    def phonemize(self, word: str, lookup_word: bool = True) -> str:
        """Phonemize a single Mirandese word via espeak + correction rules."""
        if lookup_word and word.lower() in self.GOLD:
            return self.GOLD[word.lower()]
        espeak_ipa = self.pho.phonemize_string(word, "pt-PT")
        corrected = self._apply_with_ortho(espeak_ipa, word)
        return corrected

    # -------------------------
    # Hand rules
    # -------------------------
    @staticmethod
    def _apply_with_ortho(ipa: str, ortho: str) -> str:
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
            espeak_ipa = self.pho.phonemize_string(ortho, "pt-PT")
            corrected = self._apply_with_ortho(espeak_ipa, ortho)

            # Standard metrics (includes stress)
            ed_before = self.word_edit_distance(espeak_ipa, gold_ipa)
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
            espeak_ipa_no_stress = self.strip_stress(espeak_ipa)
            corrected_no_stress = self.strip_stress(corrected)
            gold_ipa_no_stress = self.strip_stress(gold_ipa)

            ed_before_no_stress = self.word_edit_distance(espeak_ipa_no_stress, gold_ipa_no_stress)
            ed_after_no_stress = self.word_edit_distance(corrected_no_stress, gold_ipa_no_stress)

            total_ed_no_stress_before += ed_before_no_stress
            total_ed_no_stress_after += ed_after_no_stress

            # Only append to details if the final corrected IPA does not match the gold (ED > 0)
            if ed_after > 0:
                details.append({
                    "word": ortho,
                    "espeak": espeak_ipa,
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

    pho = EspeakMWL()
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
    print(f"PER (Initial Espeak): {per_before:.2%}")
    print(f"PER (After Rules):    {per_after:.2%}")

    print("\n## Phoneme Error Rate (PER, Stress-Agnostic)")
    print(f"PER (Initial Espeak): {per_no_stress_before:.2%}")
    print(f"PER (After Rules):    {per_no_stress_after:.2%}")

    # Rule Performance Breakdown
    improvements = stats['improvements']
    total_improved = improvements['better'] + improvements['worse'] + improvements['same']
    better_percent = (improvements['better'] / total_improved) if total_improved else 0
    worse_percent = (improvements['worse'] / total_improved) if total_improved else 0
    print("\n## Rule Performance (vs. Initial Espeak)")
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
        print(f"{'Word':<20} | {'Gold':<15} | {'Espeak':<15} | {'Corrected':<15} | {'ED After':<8} | {'ED Before':<8}")
        print("-" * 75)

        # Print the detailed list
        for d in wrong_words:
            print(
                f"{d['word']:<20} | {d['gold']:<15} |  {d['espeak']:<15} | {d['corrected']:<15} | {d['ed_after']:<8} | {d['ed_before']:<8}")
    else:
        print("All words achieved an exact match (100% Accuracy)!")

    # ==================================================
    #       Mirandese Phonemizer Rule Evaluation
    # ==================================================
    # Total Words Evaluated: 145
    #
    # ## Phoneme Error Rate (PER, Full IPA Match, includes stress)
    # PER (Initial Espeak): 59.98%
    # PER (After Rules):    52.35%
    #
    # ## Phoneme Error Rate (PER, Stress-Agnostic)
    # PER (Initial Espeak): 39.51%
    # PER (After Rules):    30.30%
    #
    # ## Rule Performance (vs. Initial Espeak)
    # Words Improved: 62 (42.8% of total)
    # Words Degraded: 10 (6.9% of total)
    # Words Unchanged: 73
    #
    # ==================================================
    #
    # --- Incorrectly Phonemized Words (Full IPA Match ED > 0) ---
    # Total Incorrect: 142 words
    #
    # Word                 | Gold            | Espeak          | Corrected       | ED After | ED Before
    # ---------------------------------------------------------------------------
    # hai                  | aj              |  ˈaɪ             | ˈaj             | 1        | 2
    # más                  | mas̺            |  mˈaʃ            | mˈas̺           | 1        | 3
    # mais                 | majs̺           |  mˈaɪʃ           | mˈajs̺          | 1        | 4
    # alhá                 | ɐˈʎa            |  ɐʎˈa            | ɐʎˈa            | 2        | 2
    # deimingo             | dejˈmĩgʊ        |  dˌeɪmˈiŋɡʊ      | dˌejmˈĩɡʊ       | 4        | 6
    # abandono             | abɐ̃ˈdonu       |  ˌɐbɐ̃ŋdˈonʊ     | ˌβ̃ŋdˈonʊ       | 6        | 5
    # adbertido            | ɐdbɨɾˈtidu      |  ˌɐdbɨɾətˈidʊ    | ˌɐdbɨɾtˈidʊ     | 4        | 4
    # adulto               | ɐˈdultu         |  ˌɐdˈuwtʊ        | ˌɐdˈuwtʊ        | 5        | 5
    # afamado              | ɐfɐˈmadu        |  ˌɐfɐmˈadʊ       | ˌɐfɐmˈadʊ       | 4        | 4
    # afeito               | ɐˈfejtʊ         |  ˌɐfˈeɪtʊ        | ˌɐfˈejtʊ        | 3        | 4
    # afelhado             | ɐfɨˈʎadu        |  ˌɐfɨʎˈadʊ       | ˌɐfɨʎˈadʊ       | 4        | 4
    # alternatibo          | altɨɾnɐˈtibu    |  ˌɑltɨɾənɐtˈibʊ  | ˌɑltɨɾnɐtˈibʊ   | 5        | 6
    # amarielho            | ɐmɐˈɾjɛʎu       |  ɐmˌɐɾiˈeʎʊ      | ɐmˌɐɾiˈeʎʊ      | 6        | 6
    # ambesible            | ɐ̃bɨˈs̺iblɨ     |  ˌɐ̃mbɨzˈiblɨ    | ˌɐ̃mbɨzˈiblɨ    | 5        | 5
    # amouchado            | amowˈtʃaðu      |  ɐmuwʃˈadʊ       | ɐmuwʃˈadʊ       | 7        | 7
    # amportante           | ɐ̃puɾˈtɐ̃tɨ     |  ˌɐ̃mpuɾətˈɐ̃ŋtɨ | ˌɐ̃mpuɾətˈɐ̃ŋtɨ | 5        | 5
    # ampossible           | ɐ̃puˈsiblɨ      |  ˌɐ̃mpusˈiblɨ    | ˌɐ̃mpusˈiblɨ    | 4        | 4
    # ampressionante       | ɐ̃pɾɨsjuˈnɐ̃tɨ  |  ˌɐ̃mpɹɨsˌiunˈɐ̃ŋtɨ | ˌɐ̃mpɾɨsˌiunˈɐ̃ŋtɨ | 7        | 8
    # anchir               | ɐ̃ˈtʃiɾ         |  ɐ̃ŋʃˈiɹ         | ɐ̃ŋʃˈiɾ         | 3        | 4
    # antender             | ɐ̃tɨ̃ˈdeɾ       |  ˌɐ̃ŋteɪŋdˈeɹ    | ˌɐ̃ŋtejŋdˈeɾ    | 6        | 7
    # arena                | ɐˈɾenɐ          |  ˌɐɾˈenɐ         | ˌɐɾˈenɐ         | 3        | 3
    # açpuis               | ɐsˈpujs̺        |  ˌɐspuˈiʃ        | ˌɐspuˈis̻       | 5        | 5
    # berde                | ˈveɾdɨ          |  bˈɛɾədɨ         | bˈɛɾədɨ         | 4        | 4
    # besible              | bɨˈz̺iblɨ       |  bˌezˈiblɨ       | bɨzˈiblɨ        | 2        | 3
    # bexanar              | bɨʃɐˈnaɾ        |  bˌeʃɐnˈaɹ       | bɨʃɐnˈaɾ        | 2        | 5
    # bibal                | biˈβaɫ          |  bibˈɑl          | bibˈɑl          | 4        | 4
    # bielho               | bjɛʎu           |  bˌiˈeʎʊ         | bˌiˈeʎʊ         | 5        | 5
    # biolento             | bjuˈlẽtu        |  bˌiulˈeɪŋtʊ     | bˌiulˈejŋtʊ     | 7        | 7
    # biúba                | biˈuβɐ          |  bˌiˈubɐ         | bˌiˈβ           | 3        | 2
    # brabo                | bɾabu           |  bɹˈabʊ          | bɾˈabʊ          | 2        | 3
    # branco               | bɾɐ̃ku          |  bɹˈɐ̃ŋkʊ        | bɾˈɐ̃ŋkʊ        | 3        | 4
    # buono                | bwonu           |  bwˈonʊ          | bwˈonʊ          | 2        | 2
    # burmeilho            | buɾˈmɐjʎu       |  bˌuɾəmɨˈiʎʊ     | bˌuɾəmɨˈiʎʊ     | 6        | 6
    # bíblico              | bibliku         |  bˈiblikʊ        | bˈiblikʊ        | 2        | 2
    # cabresto             | kɐˈbɾeʃtu       |  kˌɐbɹˈeʃtʊ      | kˌɐbɾˈeʃtʊ      | 4        | 5
    # canhona              | kɐˈɲonɐ         |  kˌɐ̃ɲˈonɐ       | kˌɐ̃ɲˈonɐ       | 3        | 3
    # cheno                | ˈtʃenu          |  ʃˈenʊ           | ʃˈenʊ           | 4        | 4
    # chober               | tʃuˈβeɾ         |  ʃubˈeɹ          | ʃubˈeɾ          | 3        | 4
    # ciguonha             | s̻iˈɣwoɲɐ       |  sˌiɡwˈoɲɐ       | s̻ˌiɡwˈoɲɐ      | 4        | 4
    # cul                  | kul             |  kˈuw            | kˈuw            | 2        | 2
    # dafeito              | ðɐˈfejtʊ        |  dˌɐfˈeɪtʊ       | dˌɐfˈejtʊ       | 4        | 5
    # defrente             | dɨˈfɾẽtɨ        |  dˌɨfɹˈeɪŋtɨ     | dˌɨfɾˈejŋtɨ     | 6        | 6
    # defícel              | dɨˈfisɛl        |  dˌɨfˈisɨl       | dˌɨfˈis̻ɨl      | 5        | 4
    # drento               | ˈdɾẽtu          |  dɹˈeɪŋtʊ        | dɾˈejŋtʊ        | 6        | 6
    # eigual               | ɐjˈɡwal         |  eɪɡwˈɑl         | ejɡwˈɑl         | 4        | 5
    # eras                 | ˈɛɾɐs̺          |  ˈeɾɐʃ           | ˈeɾɐs̺          | 1        | 3
    # feliç                | fɨˈlis̻         |  fɨlˈis          | fɨlˈis          | 3        | 3
    # fierro               | ˈfjɛru          |  fˌiˈɛʁʊ         | fˌiˈɛrʊ         | 5        | 6
    # francesa             | fɾɐ̃ˈsɛzɐ       |  fɹˌɐ̃ŋsˈezɐ     | fɾˌɐ̃ŋsˈezɐ     | 4        | 5
    # francesas            | fɾɐ̃ˈsɛzɐs̺     |  fɹˌɐ̃ŋsˈezɐʃ    | fɾˌɐ̃ŋsˈezɐs̻   | 5        | 7
    # franceses            | fɾɐ̃ˈsɛzɨs̺     |  fɹˌɐ̃ŋsˈezɨs    | fɾˌɐ̃ŋsˈezɨs    | 5        | 6
    # francés              | fɾɐ̃ˈsɛs̺       |  fɹɐ̃ŋsˈɛʃ       | fɾɐ̃ŋsˈɛs̺      | 2        | 5
    # fui                  | fuj             |  fˈuɪ            | fˈuɪ            | 2        | 2
    # fumos                | ˈfumus̺         |  fˈumʊʃ          | fˈumʊs̺         | 3        | 5
    # fuogo                | fwoɣʊ           |  fwˈɔɡʊ          | fwˈɔɡʊ          | 3        | 3
    # fuonte               | ˈfwõtɨ          |  fwˈoŋtɨ         | fwˈoŋtɨ         | 4        | 4
    # fuorte               | ˈfwɔɾtɨ         |  fwˈɔɾətɨ        | fwˈɔɾətɨ        | 3        | 3
    # fuortemente          | fwɔɾtɨˈmẽtɨ     |  fwˌuɾətɨmˈeɪŋtɨ | fwˌuɾətɨmˈejŋtɨ | 7        | 7
    # fuorça               | ˈfwɔɾs̻ɐ        |  fwˈɔɾəsɐ        | fwˈɔɾəsɐ        | 4        | 4
    # fuste                | ˈfus̺tɨ         |  fˈuʃtɨ          | fˈuʃtɨ          | 4        | 4
    # fácele               | ˈfasɨlɨ         |  fˈasɨlɨ         | fˈas̻ɨlɨ        | 3        | 2
    # guapo                | ˈɡwapu          |  ɡwˈapʊ          | ɡwˈapʊ          | 3        | 3
    # haber                | ɐˈβeɾ           |  ɐbˈeɹ           | ɐbˈeɾ           | 2        | 3
    # houmano              | owˈmɐnu         |  ˌuwmˈɐ̃nʊ       | ˌuwmˈɐ̃nʊ       | 6        | 6
    # i                    | i               |  ˈi              | ˈi              | 1        | 1
    # lhabrar              | ʎɐˈbɾaɾi        |  ʎɐbɹˈaɹ         | ʎɐbɾˈaɾ         | 3        | 5
    # lhimpo               | ˈʎĩpʊ           |  ʎˈimpʊ          | ʎˈimpʊ          | 3        | 3
    # lhobo                | ˈʎobʊ           |  ʎˈobʊ           | ʎˈobʊ           | 2        | 2
    # lhuç                 | ˈʎus̻           |  ʎˈus            | ʎˈus̻           | 2        | 3
    # lhéngua              | ˈʎɛ̃ɡwɐ         |  ʎˈɛnɡwɐ         | ʎˈɛnɡwɐ         | 3        | 3
    # luç                  | ˈʎus̻           |  lˈus            | lˈus̻           | 2        | 3
    # macado               | mɐˈkadu         |  mˌɐkˈadʊ        | mˌɐkˈadʊ        | 4        | 4
    # maias                | ˈmajɐs̺         |  mˈaɪɐʃ          | mˈajɐs̺         | 2        | 5
    # mirandés             | miɾɐ̃ˈdes̺      |  mˌiɾɐ̃ŋdˈɛʃ     | mˌiɾɐ̃ŋdˈɛs̺    | 4        | 5
    # molineiro            | mʊliˈnei̯rʊ     |  mˌulinˈeɪɾʊ     | mˌulinˈejɾʊ     | 7        | 7
    # molino               | muˈlinu         |  mˌulˈinʊ        | mˌulˈinʊ        | 4        | 4
    # muola                | ˈmu̯olɐ         |  mwˈɔlɐ          | mwˈɔlɐ          | 4        | 4
    # ne l                 | nɨl             |  nˈɨ ˈɛl         | nˈɨ ˈɛl         | 4        | 4
    # neçairo              | nɨˈsajɾu        |  nˌesˈaɪɾʊ       | nˌesˈajɾʊ       | 4        | 5
    # nuobo                | ˈnwoβʊ          |  nwˈobʊ          | nwˈobʊ          | 3        | 3
    # nó                   | ˈnɔ             |  nˈɔ             | nˈɔ             | 2        | 2
    # onte                 | ˈõtɨ            |  ˈoŋtɨ           | ˈoŋtɨ           | 2        | 2
    # oucidental           | ows̻idẽˈtal     |  ˌuwsideɪŋtˈɑl   | ˌuwsðɪŋtˈɑl     | 8        | 8
    # oufecialmente        | owfɨˌsjalˈmẽtɨ  |  ˌuwfɨsiˌɑlmˈeɪŋtɨ | ˌuwfɨs̻iˌɑlmˈejŋtɨ | 11       | 10
    # ourdenhar            | ou̯ɾdɨˈɲaɾ      |  ˌuwɾədɨɲˈaɹ     | ˌuwɾədɨɲˈaɾ     | 5        | 6
    # oureginal            | owɾɨʒiˈnal      |  ˌuwɾɨʒinˈɑl     | ˌuwɾɨʒinˈɑl     | 5        | 5
    # ourganizaçon         | ou̯rɡɐnizɐˈsõ   |  ˌuwɾəɡɐnˌizɐsˈoŋ | ˌuwɾəɡɐnˌizɐsˈõ | 7        | 8
    # ouropeu              | owɾuˈpew        |  ˌuwɾupˈeʊ       | ˌuwɾupˈeʊ       | 5        | 5
    # ourriêta             | ˈowrjetɐ        |  ˌuwʁiˈetɐ       | ˌuwriˈetɐ       | 4        | 5
    # paxarina             | pɐʃɐˈɾinɐ       |  pˌɐʃɐɾˈinɐ      | pˌɐʃɐɾˈinɐ      | 3        | 3
    # pequeinho            | pɨˈkɐiɲu        |  pˌekɨˈiɲʊ       | pˌekɨˈiɲʊ       | 5        | 5
    # piranha              | piˈraɲɐ         |  pˌiɾˈɐ̃ɲɐ       | pˌiɾˈɐ̃ɲɐ       | 4        | 4
    # puis                 | ˈpujs̺          |  puˈiʃ           | puˈis̺          | 3        | 4
    # pul                  | ˈpul            |  pˈuw            | pˈuw            | 3        | 3
    # puorta               | ˈpwoɾtɐ         |  pwˈɔɾətɐ        | pwˈɔɾətɐ        | 4        | 4
    # purmeiro             | puɾˈmɐjɾu       |  pˌuɾəmˈeɪɾʊ     | pˌuɾəmˈejɾʊ     | 5        | 6
    # quaije               | ˈkwajʒɨ         |  kwˈaɪʒɨ         | kwˈajʒɨ         | 2        | 3
    # quando               | ˈkwɐ̃du         |  kwˈɐ̃ŋdʊ        | kwˈɐ̃ŋdʊ        | 4        | 4
    # quelobrinas          | kɨluˈbrinas̺    |  kˌelubɹˈinɐʃ    | kˌelubɾˈinɐs̺   | 6        | 8
    # quemun               | kɨˈmun          |  kɨmˈũŋ         | kɨmˈũŋ         | 4        | 4
    # rabielho             | rɐˈβjeʎu        |  ʁˌɐbiˈeʎʊ       | rˌβˈeʎʊ         | 4        | 6
    # rico                 | ˈriku           |  ʁˈikʊ           | rˈikʊ           | 3        | 3
    # salir                | s̺ɐˈliɾ         |  sɐlˈiɹ          | sɐlˈiɾ          | 3        | 4
    # screbir              | s̺krɨˈβiɾ       |  skɹɨbˈiɹ        | s̺kɾɨˈβiɾ       | 1        | 5
    # segar                | s̺ɨˈɣaɾ         |  sɨɡˈaɹ          | s̻ɨɡˈaɾ         | 3        | 4
    # sendo                | ˈsẽdu           |  sˈeɪŋdʊ         | s̺ˈejŋdʊ        | 6        | 5
    # ser                  | ˈseɾ            |  sˈɨɹ            | s̺ˈɨɾ           | 4        | 4
    # sida                 | ˈsidɐ           |  sˈidɐ           | s̺ˈð            | 4        | 2
    # sidas                | ˈsidɐs̺         |  sˈidɐʃ          | s̺ˈðs̺          | 4        | 4
    # sido                 | ˈsidu           |  sˈidʊ           | s̺ˈidʊ          | 4        | 3
    # sidos                | ˈsidus̺         |  sˈidʊʃ          | s̺ˈidʊs̺        | 4        | 5
    # simple               | ˈs̺ĩplɨ         |  sˈimplɨ         | s̺ˈimplɨ        | 4        | 4
    # sobrino              | s̺uˈbɾinu       |  sˌubɹˈinʊ       | s̺ˌubɾˈinʊ      | 4        | 5
    # sodes                | ˈsodɨs̺         |  sˈodɨʃ          | s̺ˈðs̺          | 4        | 4
    # somos                | ˈsomus̺         |  sˈumʊʃ          | s̺ˈumʊs̺        | 5        | 6
    # son                  | ˈsõ             |  sˈoŋ            | s̺ˈõ            | 3        | 3
    # sou                  | ˈsow            |  sˈuw            | s̺ˈuw           | 4        | 3
    # spanha               | ˈs̺pɐɲɐ         |  spˈɐ̃ɲɐ         | s̺pˈɐ̃ɲɐ        | 3        | 4
    # squierdo             | ˈs̺kjeɾdu       |  skˌiˈeɾədʊ      | ɾədʊɾdu         | 6        | 7
    # sós                  | ˈs̺ɔs̺          |  sˈɔʃ            | s̺ˈɔs̺          | 2        | 4
    # talbeç               | talˈbes         |  tˌɑlbˈes        | tˌɑlbˈes        | 4        | 4
    # tamien               | tɐˈmjẽ          |  tɐmˈieɪŋ        | tɐmˈiejŋ        | 4        | 5
    # tascar               | tɐs̺ˈkaɾ        |  tɐʃkˈaɹ         | tɐs̺kˈaɾ        | 2        | 4
    # tener                | tɨˈneɾ          |  tɨnˈeɹ          | tɨnˈeɾ          | 2        | 3
    # trasdonte            | ˈtɾɐz̺dõtɨ      |  tɹˌɐʒdˈoŋtɨ     | tɾˌɐʒdˈoŋtɨ     | 7        | 8
    # trasdontonte         | ˈtɾɐz̺dõtõtɨ    |  tɹˌɐʒduŋtˈoŋtɨ  | tɾˌɐʒdũtˈoŋtɨ   | 8        | 10
    # ye                   | ˈje             |  jˈɨ             | jˈɨ             | 3        | 3
    # you                  | jow             |  jˈow            | jˈow            | 1        | 1
    # yê                   | ˈje             |  jˈe             | jˈe             | 2        | 2
    # zastre               | ˈzas̺tɾɨ        |  zˈaʃtɹɨ         | zˈaʃtɾɨ         | 4        | 5
    # zeigual              | zɐjˈɡwal        |  zeɪɡwˈɑl        | zejɡwˈɑl        | 4        | 5
    # zenhar               | zɨˈɲaɾ          |  zɨɲˈaɹ          | zɨɲˈaɾ          | 2        | 3
    # çcansar              | skɐ̃ˈs̺aɾ       |  skɐ̃ŋsˈaɹ       | s̻kɐ̃ŋsˈaɾ      | 3        | 3
    # çcrebir              | skɾɨˈβiɾ        |  skɹɨbˈiɹ        | s̻kɾɨˈβiɾ       | 1        | 4
    # çcriçon              | skɾiˈsõ         |  skɹisˈoŋ        | s̻kɾisˈõ        | 3        | 4
    # çtinto               | ˈstĩtu          |  stˈiŋtʊ         | s̻tˈĩtʊ         | 4        | 5
    # érades               | ˈɛɾɐdɨs̺        |  ˈɛɾɐdɨʃ         | ˈɛɾðs̺          | 3        | 2
    # éramos               | ˈɛɾɐmus̺        |  ˈɛɾɐmʊʃ         | ˈɛɾɐmʊs̺        | 1        | 3
    # éran                 | ˈɛɾɐn           |  ˈɛɾɐ̃ŋ          | ˈɛɾɐ̃ŋ          | 2        | 2
    # ũ                    | ˈũ              |  ˌutˈil          | ˌutˈil          | 5        | 5
    # ũa                   | ˈũŋɐ            |  ˈuɐ             | ˈuɐ             | 2        | 2
    # ua                   | ˈũŋɐ            |  ˈuɐ             | ˈuɐ             | 2        | 2