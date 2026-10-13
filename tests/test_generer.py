import os
import pty
import select

import pytest
from PIL import Image
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from atelier import generer
from atelier.generer import main
from atelier.rendu import VUES

BOITE = """
from build123d import Align, Box, BuildPart, Locations

def construire():
    with BuildPart() as p:
        with Locations({positions}):
            Box({x}, 10, 10, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return p.part
"""


class Depot:
    """Un dépôt jetable : `racine/pieces/<nom>/piece.py`, sorties dans `racine/out`."""

    def __init__(self, racine):
        self.racine = racine

    def ecrire(self, nom, source):
        fichier = self.racine / "pieces" / nom / "piece.py"
        fichier.parent.mkdir(parents=True, exist_ok=True)
        fichier.write_text(source, encoding="utf-8")

    def boite(self, nom, x=20, positions="(0, 0, 0)"):
        self.ecrire(nom, BOITE.format(x=x, positions=positions))

    def generer(self, *args):
        return main(list(args), racine=self.racine)

    def fichiers(self, nom):
        return sorted(p.name for p in (self.racine / "out" / nom).iterdir())


@pytest.fixture
def depot(tmp_path):
    return Depot(tmp_path)


PNG = sorted(f"{vue}.png" for vue in VUES)


def test_eprouvette_du_depot(tmp_path):
    assert main(["eprouvette_jeux"], sortie=tmp_path) == 0
    dossier = tmp_path / "eprouvette_jeux"
    assert sorted(p.name for p in dossier.iterdir()) == sorted(PNG + ["eprouvette_jeux.step", "eprouvette_jeux.stl"])
    assert (dossier / "eprouvette_jeux.step").stat().st_size > 1000
    assert (dossier / "eprouvette_jeux.stl").stat().st_size > 1000
    for nom in PNG:
        with Image.open(dossier / nom) as image:
            assert min(image.size) > 100
            assert image.convert("L").getextrema()[0] < 100, f"{nom} est vide"


def test_hors_terminal_liste_sans_ouvrir_le_menu(depot, capsys, monkeypatch):
    monkeypatch.setattr(generer, "_interactif", lambda: False)
    monkeypatch.setattr(generer, "_choisir", lambda disponibles: pytest.fail("menu ouvert hors terminal"))
    depot.boite("alpha")
    depot.boite("beta")
    assert depot.generer() == 0
    assert "alpha, beta" in capsys.readouterr().out
    assert not (depot.racine / "out").exists()


@pytest.mark.parametrize("nom", ["inconnue", "../x", "Majuscule", "a-b", "", "1abc"])
def test_nom_inconnu_ou_invalide(depot, nom, capsys):
    depot.boite("alpha")
    assert depot.generer(nom) == 2
    assert "generer :" in capsys.readouterr().err
    assert not (depot.racine / "out").exists()


def test_deux_arguments(depot):
    depot.boite("alpha")
    assert depot.generer("alpha", "alpha") == 2


def test_sans_construire(depot, capsys):
    depot.ecrire("vide", "def construir():\n    pass\n")
    assert depot.generer("vide") == 2
    erreur = capsys.readouterr().err
    assert "piece.py" in erreur and "construire()" in erreur
    assert "Traceback" not in erreur


def test_construire_leve(depot, capsys):
    depot.ecrire("casse", "def construire():\n    raise RuntimeError('cote negative')\n")
    assert depot.generer("casse") == 1
    assert "cote negative" in capsys.readouterr().err
    assert depot.fichiers("casse") == []


def test_echec_rend_les_png_sans_exporter(depot, capsys):
    depot.boite("geante", x=300)
    assert depot.generer("geante") == 1
    assert depot.fichiers("geante") == PNG
    assert "ÉCHEC" in capsys.readouterr().out


def test_deux_solides_echec_avec_png(depot):
    depot.boite("double", positions="(0, 0, 0), (50, 0, 0)")
    assert depot.generer("double") == 1
    assert depot.fichiers("double") == PNG


def test_pas_un_part(depot):
    depot.ecrire("texte", "def construire():\n    return 'piece'\n")
    assert depot.generer("texte") == 1
    assert depot.fichiers("texte") == []


def test_run_en_echec_efface_les_exports_precedents(depot):
    depot.boite("piece")
    assert depot.generer("piece") == 0
    assert "piece.step" in depot.fichiers("piece")
    depot.boite("piece", x=300)
    assert depot.generer("piece") == 1
    assert depot.fichiers("piece") == PNG


def test_avertissement_n_empeche_pas_l_export(depot, capsys):
    depot.boite("haute", positions="(0, 0, 5)")
    assert depot.generer("haute") == 0
    assert "AVERTISSEMENT" in capsys.readouterr().out
    assert "haute.step" in depot.fichiers("haute")


FLECHE_BAS, FLECHE_HAUT, ENTREE, RETOUR, ECHAP, CTRL_C = "\x1b[B", "\x1b[A", "\r", "\x7f", "\x1b", "\x03"
TROIS = ["alpha", "beta", "gamma"]


def taper(touches, pieces):
    """Joue des touches dans le vrai menu, sans terminal."""
    with create_pipe_input() as clavier:
        clavier.send_text(touches)
        with create_app_session(input=clavier, output=DummyOutput()):
            return generer._choisir(pieces)


@pytest.mark.parametrize(
    ("pieces", "touches", "attendu"),
    [
        (TROIS, ENTREE, "alpha"),
        (TROIS, FLECHE_BAS + ENTREE, "beta"),
        (TROIS, FLECHE_HAUT + ENTREE, "gamma"),
        (TROIS, "ga" + ENTREE, "gamma"),  # la frappe filtre la liste
        (TROIS, "AL" + ENTREE, "alpha"),  # le filtre ignore la casse, comme le menu
        (TROIS, "zz" + RETOUR + RETOUR + ENTREE, "alpha"),  # filtre effacé : le menu redevient entier
        (TROIS, "g" + RETOUR + "b" + ENTREE, "beta"),
        (["alpha", "jeux", "kilo"], "j" + ENTREE, "jeux"),  # j et k filtrent, ils ne déplacent pas
        (["alpha", "jeux", "kilo"], "k" + ENTREE, "kilo"),
        (["alpha", "eprouvette_jeux", "p2"], "e_j" + ENTREE, "eprouvette_jeux"),
        (["alpha", "eprouvette_jeux", "p2"], "2" + ENTREE, "p2"),
        (["alpha"], ENTREE, "alpha"),
        (TROIS, CTRL_C, None),
        (TROIS, ECHAP + ENTREE, None),
    ],
)
def test_menu_pilote_au_clavier(pieces, touches, attendu):
    assert taper(touches, pieces) == attendu


@pytest.mark.parametrize("filtre", ["zz", "é", "épr", "alé", "\xa0", "\u202f", "\u200b"])
def test_menu_entree_sans_effet_quand_rien_ne_correspond(filtre, capsys):
    # Entrée ne ferme pas le menu : il faut encore Ctrl-C pour en sortir.
    assert taper(filtre + ENTREE + CTRL_C, TROIS) is None
    # ... et après avoir effacé le filtre, le menu sert toujours.
    assert taper(filtre + ENTREE + RETOUR * len(filtre) + "ga" + ENTREE, TROIS) == "gamma"
    assert capsys.readouterr().err == ""


def test_menu_saut_de_ligne_sans_effet_quand_rien_ne_correspond():
    assert taper("zz" + "\n" + CTRL_C, TROIS) is None


COLLAGE = "\x1b[200~gamma\x1b[201~"


def test_menu_collage_refuse_sur_le_champ(capsys):
    # Un collage arrive d'un bloc, hors du filtre : le menu se ferme sans rien choisir.
    assert taper(COLLAGE, TROIS) is None
    assert "collage" in capsys.readouterr().err


def test_menu_echap_quitte(capsys):
    assert taper(ECHAP, TROIS) is None
    assert "Annulé" in capsys.readouterr().out


def test_menu_echap_quitte_meme_avec_un_filtre(capsys):
    assert taper("zz" + ECHAP, TROIS) is None
    assert "Annulé" in capsys.readouterr().out


def test_menu_echap_entree_dit_annule(capsys):
    assert taper(ECHAP + ENTREE, TROIS) is None
    assert "Annulé" in capsys.readouterr().out


def test_vider_la_frappe_jette_l_entree_en_avance(monkeypatch):
    maitre, esclave = pty.openpty()
    with os.fdopen(esclave, "r") as entree:
        try:
            monkeypatch.setattr(generer.sys, "stdin", entree)
            os.write(maitre, b"\r")
            assert select.select([esclave], [], [], 1.0)[0], "la frappe en avance devrait être en attente"
            generer._vider_la_frappe()
            assert not select.select([esclave], [], [], 0.2)[0]
        finally:
            os.close(maitre)


def test_vider_la_frappe_sans_terminal_ne_leve_pas(monkeypatch):
    monkeypatch.setattr(generer.sys, "stdin", None)
    generer._vider_la_frappe()


def test_menu_vide_la_frappe_avant_de_s_afficher(monkeypatch):
    appels = []
    monkeypatch.setattr(generer, "_vider_la_frappe", lambda: appels.append("vide"))
    assert taper(ENTREE, TROIS) == "alpha"
    assert appels == ["vide"]


class Flux:
    def __init__(self, terminal):
        self.terminal = terminal

    def isatty(self):
        return self.terminal


@pytest.mark.parametrize(
    ("entree", "sortie", "attendu"),
    [(True, True, True), (True, False, False), (False, True, False), (False, False, False)],
)
def test_interactif_exige_un_terminal_des_deux_cotes(monkeypatch, entree, sortie, attendu):
    monkeypatch.setattr(generer.sys, "stdin", Flux(entree))
    monkeypatch.setattr(generer.sys, "stdout", Flux(sortie))
    assert generer._interactif() is attendu


@pytest.mark.parametrize("ferme", ["stdin", "stdout"])
def test_interactif_flux_ferme(monkeypatch, ferme):
    monkeypatch.setattr(generer.sys, "stdin", Flux(True))
    monkeypatch.setattr(generer.sys, "stdout", Flux(True))
    monkeypatch.setattr(generer.sys, ferme, None)
    assert generer._interactif() is False


@pytest.fixture
def terminal(monkeypatch):
    """Fait croire à un terminal et remplace le menu par une réponse choisie."""

    def repondre(choix):
        vus = []
        monkeypatch.setattr(generer, "_interactif", lambda: True)
        monkeypatch.setattr(generer, "_choisir", lambda disponibles: vus.append(disponibles) or choix)
        return vus

    return repondre


def test_terminal_le_choix_du_menu_est_genere(depot, terminal):
    depot.boite("alpha")
    depot.boite("beta")
    vus = terminal("beta")
    assert depot.generer() == 0
    assert vus == [["alpha", "beta"]]
    assert "beta.step" in depot.fichiers("beta")
    assert not (depot.racine / "out" / "alpha").exists()


def test_terminal_annulation_ne_genere_rien(depot, terminal):
    depot.boite("alpha")
    assert depot.generer("alpha") == 0
    terminal(None)
    assert depot.generer() == 130
    assert "alpha.step" in depot.fichiers("alpha")


def test_terminal_piece_choisie_en_echec(depot, terminal):
    depot.boite("geante", x=300)
    terminal("geante")
    assert depot.generer() == 1
    assert depot.fichiers("geante") == PNG


def test_terminal_sans_piece_pas_de_menu(depot, terminal, capsys):
    vus = terminal("fantome")
    assert depot.generer() == 0
    assert vus == []
    assert "aucune" in capsys.readouterr().out


def test_terminal_un_nom_donne_ne_passe_pas_par_le_menu(depot, terminal):
    depot.boite("alpha")
    vus = terminal("fantome")
    assert depot.generer("alpha") == 0
    assert vus == []


def test_dossier_au_nom_invalide_ecarte_et_signale(depot, terminal, capsys):
    depot.boite("alpha")
    depot.boite("Ma-Piece")
    vus = terminal("alpha")
    assert depot.generer() == 0
    assert vus == [["alpha"]]
    assert "Ma-Piece" in capsys.readouterr().err


def test_hors_terminal_dossier_au_nom_invalide_absent_de_la_liste(depot, capsys, monkeypatch):
    monkeypatch.setattr(generer, "_interactif", lambda: False)
    depot.boite("alpha")
    depot.boite("Ma-Piece")
    assert depot.generer() == 0
    sortie = capsys.readouterr()
    assert "alpha" in sortie.out
    assert "Ma-Piece" not in sortie.out
    assert "Ma-Piece" in sortie.err


def test_nom_de_dossier_piege_affiche_echappe(depot, capsys):
    depot.boite("alpha")
    depot.boite("x\x1b[31mrouge")
    assert depot.generer("alpha") == 0
    assert "\x1b" not in capsys.readouterr().err


def test_inventaire_ne_garde_que_de_vrais_fichiers(depot):
    depot.boite("alpha")
    (depot.racine / "pieces" / "faux" / "piece.py").mkdir(parents=True)
    assert generer.inventaire(depot.racine) == (["alpha"], [])


def liste_affichee(filtre):
    _, menu = generer._preparer(TROIS)
    for caractere in filtre or "":
        menu.add_search_character(caractere)
    return "".join(texte for _style, texte, *_ in menu.text())


@pytest.mark.parametrize("filtre", ["é", "alé"])
def test_menu_lettre_accentuee_vide_la_liste(filtre):
    assert "aucune pièce" in liste_affichee(filtre)


def test_menu_filtre_sans_resultat_vide_la_liste():
    affiche = liste_affichee("zz")
    assert "aucune pièce" in affiche
    assert not any(nom in affiche for nom in TROIS)


def test_menu_filtre_avec_resultat_reduit_la_liste():
    affiche = liste_affichee("ga")
    assert "gamma" in affiche
    assert "alpha" not in affiche and "aucune pièce" not in affiche


def test_menu_sans_filtre_montre_tout():
    affiche = liste_affichee(None)
    assert all(nom in affiche for nom in TROIS)
