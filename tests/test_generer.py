import pytest
from PIL import Image

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


def test_sans_argument_liste_les_pieces(depot, capsys):
    depot.boite("alpha")
    depot.boite("beta")
    assert depot.generer() == 0
    assert "alpha, beta" in capsys.readouterr().out


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
