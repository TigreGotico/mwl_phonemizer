"""Phenomenon-level unit tests for the hand-crafted orthography rules.

Each test names one phonological rule of Mirandese and cites its source:

- Wikipedia, "Mirandese language" (Orthography table / Consonants / Vowels
  sections, after the Convenção Ortográfica da Língua Mirandesa, 1999)
- Quarteu & Frías Conde (2001), "L Mirandés: Ũa Lhéngua Minoritaira an
  Pertual" (Ianua 2)

The tests exercise the pure rule engine (``phonemize_word`` /
``lookup_word=False``) so the gold-dictionary shortcut never masks a rule.
"""
import unittest

from mwl_phonemizer.orthography_hand_rules import OrthographyRulesMWL


class TestNasalVowelDigraphs(unittest.TestCase):
    """⟨an/en/in/on/un⟩: nasalisation is a coda phenomenon.

    Wikipedia, "Mirandese language", Orthography table: AN /ɐ̃(ŋ)/,
    EN /ẽ(ŋ)/, IN /ĩ(ŋ)/, ON /õ(ŋ)/, UN /ũ(ŋ)/ — the velar appendix is
    optional and not realised word-internally. Before a vowel the ⟨n⟩ is
    a plain onset: "Retention of intervocalic /l/, /n/" (ibid., Phonology;
    Quarteu & Frías Conde 2001 on the conservation of Latin -N-).
    """

    def setUp(self):
        self.pho = OrthographyRulesMWL()

    def test_no_velar_appendix_word_internally(self):
        # gold: brincar -> bɾĩkaɾ (no ŋ before the internal consonant)
        self.assertNotIn("ŋ", self.pho.phonemize_word("brincar"))
        self.assertIn("ĩ", self.pho.phonemize_word("brincar"))

    def test_intervocalic_n_keeps_vowel_oral(self):
        # gold: paxarina -> pɐʃɐɾinɐ (oral [i] + onset [n], no *[ĩŋ])
        out = self.pho.phonemize_word("paxarina")
        self.assertIn("in", out)
        self.assertNotIn("ĩ", out)

    def test_word_final_high_nasal_keeps_velar_appendix(self):
        # gold: botin -> bʉtĩŋ (optional (ŋ) realised finally after /ĩ/)
        self.assertTrue(self.pho.phonemize_word("botin").endswith("ĩŋ"))


class TestVoicedDentalStopLenition(unittest.TestCase):
    """⟨d⟩ = [d] by default, lenited [ð] in weak position.

    Wikipedia, "Mirandese language", Consonants: "Voiced stops /b, d, ɡ/
    can be lenited as fricatives [β, ð, ɣ]"; the Orthography table lists
    D = /d/, /ð/ in that order. The g2p.json map previously listed [ð]
    first, inverting the rule (word-initial *[ð], intervocalic *[d]).
    """

    def setUp(self):
        self.pho = OrthographyRulesMWL()

    def test_word_initial_d_is_a_stop(self):
        # gold: defrente -> dɨfɾẽtɨ (not *[ð]-initial)
        self.assertTrue(self.pho.phonemize_word("defrente").startswith("d"))

    def test_intervocalic_d_lenites_to_fricative(self):
        # V_V position: lenition applies (gold: burrada -> bʉraðɐ)
        self.assertIn("ð", self.pho.phonemize_word("burrada"))


class TestCedillaIsVoicelessLaminal(unittest.TestCase):
    """⟨ç⟩ = voiceless laminal dental [s̻].

    Wikipedia, "Mirandese language", Consonants: "the laminal dental
    sibilants ... are spelled c/ç and z" — ⟨c/ç⟩ is the voiceless member,
    ⟨z⟩ the voiced one. The Convenção Ortográfica (1999) uses ⟨ç⟩ for /s/
    before ⟨a, o, u⟩ and word-finally. The old rule always emitted *[z̻].
    """

    def setUp(self):
        self.pho = OrthographyRulesMWL()

    def test_word_final_cedilla(self):
        # gold: lhuç -> ʎus̻
        self.assertTrue(self.pho.phonemize_word("lhuç").endswith("s̻"))

    def test_preconsonantal_and_prevocalic_cedilla(self):
        # gold: fuorça -> fwɔɾs̻ɐ
        self.assertIn("s̻", self.pho.phonemize_word("fuorça"))
        self.assertNotIn("z̻", self.pho.phonemize_word("fuorça"))


class TestStressedEInFinalEr(unittest.TestCase):
    """⟨e⟩ in word-final ⟨-er⟩ is the stressed close-mid [e].

    Convenção Ortográfica da Língua Mirandesa (1999): consonant-final
    words carry final stress (as in Portuguese), and stressed /e/ is [e]
    while reduced [ɨ] belongs to unstressed syllables (Wikipedia,
    "Mirandese language", Vowels: /e/ has allophones [ɛ, e, ɨ]).
    """

    def setUp(self):
        self.pho = OrthographyRulesMWL()

    def test_infinitive_er_is_close_mid_e(self):
        # gold: chober -> tʃuβeɾ, haber -> ɐβeɾ
        self.assertTrue(self.pho.phonemize_word("chober").endswith("eɾ"))
        self.assertTrue(self.pho.phonemize_word("haber").endswith("eɾ"))


class TestStressConditionedA(unittest.TestCase):
    """/a/ = open [a] under stress, reduced [ɐ] unstressed.

    Wikipedia, "Mirandese language", Vowels: "/a/ has allophones of
    [ä, ɐ]", distributed by stress as in Portuguese; default stress
    placement per the Convenção Ortográfica (1999): paroxytone for
    vowel(-s)-final words, oxytone for consonant-final words.
    """

    def setUp(self):
        self.pho = OrthographyRulesMWL()

    def test_penultimate_stressed_a_is_open(self):
        # gold: afelhado -> ɐfɨʎadu (initial ⟨a⟩ reduced, penult ⟨a⟩ open)
        out = self.pho.phonemize_word("afelhado")
        self.assertTrue(out.startswith("ɐ"))
        self.assertIn("ʎa", out)

    def test_final_stressed_a_in_consonant_final_word(self):
        # oxytone: brincar -> bɾĩkaɾ (gold), stressed ⟨a⟩ stays [a]
        self.assertIn("a", self.pho.phonemize_word("brincar"))


class TestRulesPERImproves(unittest.TestCase):
    """The rule fixes above must lower PER against the native-speaker gold."""

    def test_per_below_pre_fix_baseline(self):
        stats = OrthographyRulesMWL().evaluate_on_gold()
        # pre-wave baseline: per=0.3586, per_no_stress=0.2791
        self.assertLess(stats["per"], 0.30)
        self.assertLess(stats["per_no_stress"], 0.20)


if __name__ == "__main__":
    unittest.main()
