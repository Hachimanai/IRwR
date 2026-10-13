from commun.jeux import JEUX, jeu
from commun.visserie import PASSAGE, TETE


def test_chaque_materiau_a_tous_ses_ajustements():
    for materiau, ajustements in JEUX.items():
        assert set(ajustements) == {"serre", "glissant", "libre"}, materiau
        assert ajustements["serre"] < ajustements["glissant"] < ajustements["libre"], materiau
    assert jeu("PLA", "glissant") == JEUX["PLA"]["glissant"]


def test_visserie_coherente():
    tailles = sorted(PASSAGE, key=lambda t: float(t[1:]))
    assert set(TETE) == set(PASSAGE)
    passages = [PASSAGE[t] for t in tailles]
    assert passages == sorted(set(passages))
    for taille in tailles:
        nominal = float(taille[1:])
        assert nominal < PASSAGE[taille] < TETE[taille][0]
