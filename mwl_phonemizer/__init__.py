from mwl_phonemizer.crf_mwl import  CRFPhonemizer
from mwl_phonemizer.epitran_mwl import EpitranMWL
from mwl_phonemizer.espeak_mwl import EspeakMWL
from mwl_phonemizer.ngram_mwl import NgramMWLPhonemizer
from mwl_phonemizer.orthography_hand_rules import OrthographyRulesMWL
from mwl_phonemizer.crf_espeak_mwl import CRFEspeakCorrector
from mwl_phonemizer.crf_epitran_mwl import CRFEpitranCorrector
from mwl_phonemizer.char_lookup_mwl import LookupTableMWL



if __name__ == "__main__":
    sample_texts = [
        "Muitas lhénguas ténen proua de ls sous pergaminos antigos, de la lhiteratura screbida hai cientos d'anhos i de scritores hai muito afamados, hoije bandeiras dessas lhénguas. Mas outras hai que nun puoden tener proua de nada desso, cumo ye l causo de la lhéngua mirandesa.",
        "Todos ls seres houmanos nácen lhibres i eiguales an honra i an dreitos. Dotados de rezon i de cuncéncia, dében de se dar bien uns culs outros i cumo armano",
        "Hai más fuogo alhá, i ye deimingo!",
        """Quien dirie qu'antre ls matos eiriçados
    Las ourriêtas i ls rius d'esta tiêrra,
    Bibie, cumo l chaugarço de la siêrra,
    Ua lhéngua de sons tan bariados?

    Mostre-se i fale-s' essa lhéngua filha
    D'un pobo que ten neilha l choro i l canto!
    Nada por ciêrto mos cautiba tanto
    Cumo la form' an que l'eideia brilha.

    Zgraçiado d'aquel, qu'abandonando
    La patri' an que naciu, la casa i l huôrto.
    Tamien se squeçe de la fala! Quando
    L furdes ber, talbéç que stéia muôrto!"""
    ]

    phonemizer = CRFEspeakCorrector()
    for text in sample_texts:
        print(f"Original: {text}")
        print(f"Phonemized: {phonemizer.phonemize_sentence(text)}\n")

    # Original: Muitas lhénguas ténen proua de ls sous pergaminos antigos, de la lhiteratura screbida hai cientos d'anhos i de scritores hai muito afamados, hoije bandeiras dessas lhénguas. Mas outras hai que nun puoden tener proua de nada desso, cumo ye l causo de la lhéngua mirandesa.
    # Phonemized: mujtɐs̺ ʎenɡɐs̺ tenɛ̃ pɾowuɐ dɛ ls̺ sowus̺ pɛɾɡɐminos̺ ɐntiɡos̺, dɛ ʎɐ ʎitɛɾɐtuɾɐ s̺kɾβdɐ aj s̻iɛntos̻ d'ɐnos̺ i dɛ s̺kɾitoɾɛs̺ aj mujtu ɐfɐmðs̺, owiʒɛ bɐndɛjɾɐs̺ dɛʃsɐs̺ ʎenɡɐs̺. mɐs̺ owutrɐs̺ aj kʷɛ nũ puð̃ tɨˈneɾ pɾowuɐ dɛ nð dɛʃsu, kumu ˈje l̩ kawzu dɛ ʎɐ ˈʎɛ̃ɡwɐ miɾɐndɛzɐ.
    #
    # Original: Todos ls seres houmanos nácen lhibres i eiguales an honra i an dreitos. Dotados de rezon i de cuncéncia, dében de se dar bien uns culs outros i cumo armano
    # Phonemized: tðs̺ ls̺ sɛɾɛs̺ owumɐnos̺ nazɛ̃ ʎibrɛs̺ i ɛjɡɐlɛs̺ ɐ̃ onrɐ i ɐ̃ dɾɛjtos̺. dotðs̺ dɛ rɛzõ i dɛ kuns̻ens̻iɐ, dβ̃ dɛ sɛ dɐɾ biɛ̃ uns̺ kuls̺ owutros̺ i kumu ɐɾmɐnu
    #
    # Original: Hai más fuogo alhá, i ye deimingo!
    # Phonemized: aj mas̺ fwoɣʊ ɐˈʎa, i ˈje dejˈmĩgʊ!
    #
    # Original: Quien dirie qu'antre ls matos eiriçados
    #     Las ourriêtas i ls rius d'esta tiêrra,
    #     Bibie, cumo l chaugarço de la siêrra,
    #     Ua lhéngua de sons tan bariados?
    #
    #     Mostre-se i fale-s' essa lhéngua filha
    #     D'un pobo que ten neilha l choro i l canto!
    #     Nada por ciêrto mos cautiba tanto
    #     Cumo la form' an que l'eideia brilha.
    #
    #     Zgraçiado d'aquel, qu'abandonando
    #     La patri' an que naciu, la casa i l huôrto.
    #     Tamien se squeçe de la fala! Quando
    #     L furdes ber, talbéç que stéia muôrto!
    # Phonemized: kʷiɛ̃ diɾiɛ k'ɐntɾɛ ls̺ mɐtos̺ ɛjɾisðs̻
    #     ʎɐs̺ owurietɐs̺ i ls̺ riws̺ d'ɛʃtɐ tierɐ,
    #     bβɛ, kumu l̩ kawɡɐɾsu dɛ ʎɐ s̻ierɐ,
    #     ˈũŋɐ ˈʎɛ̃ɡwɐ dɛ sons̺ tɐ̃ bɐɾiðs̺?
    #
    #     moʃtɾɛ sɛ i fɐlɛ s̺̺' ɛʃsɐ ˈʎɛ̃ɡwɐ filɐ
    #     d'ũ pβ kʷɛ tɛ̃ nɛjlɐ l̩ koɾu i l̩ kɐntu!
    #     nð poɾ s̻ieɾtu mos̺ kawtβ tɐntu
    #     kumu ʎɐ foɾ' ɐ̃ kʷɛ l̩'ɛjdɛjɐ bɾilɐ.
    #
    #     zɡɾɐs̻ið d'ɐkʷɛl, k'βndonɐndu
    #     ʎɐ pɐtri' ɐ̃ kʷɛ nɐziw, ʎɐ kɐzɐ i l̩ uoɾtu.
    #     tɐˈmjẽ sɛ s̻kʷɛsɛ dɛ ʎɐ fɐlɐ! ˈkwɐ̃du
    #     l̩ fuɾdɛs̺ bɛɾ, tɐlbes kʷɛ s̺tejɐ muoɾtu!