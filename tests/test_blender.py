"""Filière Blender : aiguillage de `generer` avec un faux Blender, puis le vrai s'il est installé."""

import json
import shutil
import sys
import textwrap

import pytest
from PIL import Image

from atelier import blender, generer
from atelier.generer import main
from atelier.rendu import VUES

PNG = sorted(f"{vue}.png" for vue in VUES)
CUBE = {
    "type": "MESH",
    "faces": 6,
    "triangles": 12,
    "triangles_stl": 12,
    "parties": 1,
    "aretes_non_manifold": 0,
    "aretes_normales_opposees": 0,
    "volume": 1000.0,
    "boite_min": [-5.0, -5.0, 0.0],
    "boite_max": [5.0, 5.0, 10.0],
}

# Le faux Blender lit la réponse à rendre dans la scène elle-même (du JSON), écrit des exports
# factices et une image par vue, comme `atelier/blender_scene.py`.
FAUX = """#!{python}
import json, sys, time
from pathlib import Path
from PIL import Image

demande = json.loads(Path(sys.argv[sys.argv.index("--") + 1]).read_text())
reponse = json.loads(Path(demande["scene"]).read_text())
if reponse.pop("dormir", 0):
    time.sleep(30)
if reponse.pop("planter", False):
    print("Segmentation fault", file=sys.stderr)
    sys.exit(139)
Path(demande["stl"]).write_bytes(b"stl")
Path(demande["blend"]).write_bytes(b"blend")
if reponse.pop("rendre", False):
    reponse["centre"], reponse["rendus"] = [0, 0, 5], {{}}
    for nom in demande["vues"]:
        fichier = Path(demande["rendus"]) / f"{{nom}}.png"
        Image.new("RGBA", (200, 200), (90, 90, 90, 255)).save(fichier)
        reponse["rendus"][nom] = {{"fichier": str(fichier), "emprise": [-5, 5, -5, 5], "cadrage": [-5, 5, -5, 5]}}
Path(demande["reponse"]).write_text(json.dumps(reponse))
"""


class Depot:
    def __init__(self, racine):
        self.racine = racine

    def scene(self, nom, reponse=None, source=None):
        fichier = self.racine / "pieces" / nom / "scene.py"
        fichier.parent.mkdir(parents=True, exist_ok=True)
        fichier.write_text(source if source is not None else json.dumps(reponse), encoding="utf-8")

    def generer(self, *args):
        return main(list(args), racine=self.racine)

    def fichiers(self, nom):
        return sorted(p.name for p in (self.racine / "out" / nom).iterdir())


@pytest.fixture
def depot(tmp_path):
    return Depot(tmp_path)


@pytest.fixture
def faux_blender(tmp_path, monkeypatch):
    executable = tmp_path / "faux-blender"
    executable.write_text(FAUX.format(python=sys.executable), encoding="utf-8")
    executable.chmod(0o755)
    monkeypatch.setenv("BLENDER", str(executable))
    return executable


def test_succes_exporte_stl_et_blend_avec_les_vues(depot, faux_blender, capsys):
    depot.scene("vase", {"mesures": CUBE, "rendre": True})
    assert depot.generer("vase") == 0
    assert depot.fichiers("vase") == sorted(PNG + ["vase.stl", "vase.blend"])
    assert "maillage Blender" in capsys.readouterr().out
    with Image.open(depot.racine / "out" / "vase" / "dessus.png") as image:
        assert image.convert("L").getextrema()[0] < 100


def test_maillage_ouvert_rien_n_est_exporte(depot, faux_blender, capsys):
    depot.scene("vase", {"mesures": CUBE | {"aretes_non_manifold": 4}, "rendre": True})
    assert depot.generer("vase") == 1
    assert depot.fichiers("vase") == PNG
    assert "non étanche" in capsys.readouterr().out


def test_echec_efface_les_exports_precedents(depot, faux_blender):
    depot.scene("vase", {"mesures": CUBE})
    assert depot.generer("vase") == 0
    depot.scene("vase", {"mesures": CUBE | {"parties": 2}})
    assert depot.generer("vase") == 1
    assert depot.fichiers("vase") == []


def test_construire_leve(depot, faux_blender, capsys):
    depot.scene("vase", {"erreur": "Traceback ...\nValueError: rayon negatif\n"})
    assert depot.generer("vase") == 1
    assert "rayon negatif" in capsys.readouterr().err
    assert depot.fichiers("vase") == []


def test_construire_absent_erreur_d_usage(depot, faux_blender, capsys):
    depot.scene("vase", {"erreur_usage": "scene.py doit exposer une fonction construire()"})
    assert depot.generer("vase") == 2
    assert "construire()" in capsys.readouterr().err


def test_rendu_impossible_n_empeche_pas_l_export(depot, faux_blender, capsys):
    depot.scene("vase", {"mesures": CUBE, "erreur_rendu": "RuntimeError : pas de contexte OpenGL"})
    assert depot.generer("vase") == 0
    assert depot.fichiers("vase") == ["vase.blend", "vase.stl"]
    assert "rendu impossible" in capsys.readouterr().err


def test_blender_plante(depot, faux_blender, capsys):
    depot.scene("vase", {"planter": True})
    assert depot.generer("vase") == 1
    erreur = capsys.readouterr().err
    assert "sans réponse (code 139)" in erreur and "Segmentation fault" in erreur


def test_blender_bloque(depot, faux_blender, tmp_path):
    depot.scene("vase", {"dormir": True})
    travail = tmp_path / "travail"
    travail.mkdir()
    with pytest.raises(blender.BlenderEchoue, match="n'a pas fini"):
        blender.executer(str(faux_blender), depot.racine / "pieces" / "vase" / "scene.py", {}, travail, delai=1)


def test_blender_introuvable(depot, monkeypatch, capsys):
    monkeypatch.delenv("BLENDER", raising=False)
    monkeypatch.setattr(shutil, "which", lambda nom: None)
    depot.scene("vase", {"mesures": CUBE})
    assert depot.generer("vase") == 2
    assert "pacman -S blender" in capsys.readouterr().err
    assert not (depot.racine / "out").exists()


@pytest.mark.parametrize("valeur", ["/nexiste/pas", "/etc/passwd"])
def test_variable_blender_invalide(depot, monkeypatch, capsys, valeur):
    monkeypatch.setenv("BLENDER", valeur)
    depot.scene("vase", {"mesures": CUBE})
    assert depot.generer("vase") == 2
    assert f"BLENDER={valeur}" in capsys.readouterr().err
    assert not (depot.racine / "out").exists()


def test_deux_filieres_dans_un_dossier(depot, faux_blender, capsys):
    depot.scene("vase", {"mesures": CUBE})
    (depot.racine / "pieces" / "vase" / "piece.py").write_text("def construire():\n    pass\n")
    assert depot.generer("vase") == 2
    assert "piece.py et scene.py" in capsys.readouterr().err


def test_inventaire_voit_les_deux_filieres(depot):
    depot.scene("vase", {})
    (depot.racine / "pieces" / "equerre").mkdir()
    (depot.racine / "pieces" / "equerre" / "piece.py").write_text("")
    assert generer.inventaire(depot.racine) == (["equerre", "vase"], [])


# --- Le vrai Blender -------------------------------------------------------------------------

REEL = pytest.mark.skipif(not shutil.which("blender"), reason="Blender absent de ce poste")

SCENE_CUBE = textwrap.dedent("""
    import bpy

    def construire():
        bpy.ops.mesh.primitive_cube_add(size=20, location=(0, 0, 10))
        return bpy.context.object
""")

SCENE_OUVERTE = textwrap.dedent("""
    import bmesh
    import bpy

    def construire():
        bpy.ops.mesh.primitive_cube_add(size=20, location=(0, 0, 10))
        cube = bpy.context.object
        maillage = bmesh.new()
        maillage.from_mesh(cube.data)
        maillage.faces.ensure_lookup_table()
        bmesh.ops.delete(maillage, geom=[maillage.faces[0]], context="FACES_ONLY")
        maillage.to_mesh(cube.data)
        return cube
""")


@REEL
def test_reel_cube(depot, capsys):
    depot.scene("cube", source=SCENE_CUBE)
    assert depot.generer("cube") == 0, capsys.readouterr().err
    assert depot.fichiers("cube") == sorted(PNG + ["cube.stl", "cube.blend"])
    assert "20.00 × 20.00 × 20.00 mm, 8.00 cm³" in capsys.readouterr().out
    stl = (depot.racine / "out" / "cube" / "cube.stl").read_bytes()
    assert int.from_bytes(stl[80:84], "little") == 12  # STL binaire : 6 faces carrées, 12 triangles


@REEL
def test_reel_maillage_ouvert(depot, capsys):
    depot.scene("ouvert", source=SCENE_OUVERTE)
    assert depot.generer("ouvert") == 1
    assert "non étanche : 4 arêtes" in capsys.readouterr().out


@REEL
def test_reel_vase_du_depot(tmp_path):
    assert main(["vase_torsade"], sortie=tmp_path) == 0
    dossier = tmp_path / "vase_torsade"
    assert sorted(p.name for p in dossier.iterdir()) == sorted(PNG + ["vase_torsade.stl", "vase_torsade.blend"])
    for nom in PNG:
        with Image.open(dossier / nom) as image:
            assert image.convert("L").getextrema()[0] < 100, f"{nom} est vide"


SCENE_CUBE_AVEC = textwrap.dedent("""
    import bpy

    def construire():
        bpy.ops.mesh.primitive_cube_add(size=20, location=(0, 0, 10))
        cube = bpy.context.object
        {reglage}
        return cube
""")


@REEL
@pytest.mark.parametrize("reglage", ["cube.hide_set(True)", "cube.hide_viewport = True", "cube.scale = (-1, 1, 1)"])
def test_reel_objet_masque_ou_en_miroir(depot, capsys, reglage):
    depot.scene("cube", source=SCENE_CUBE_AVEC.format(reglage=reglage))
    assert depot.generer("cube") == 0, capsys.readouterr().out
    assert "8.00 cm³" in capsys.readouterr().out
    stl = (depot.racine / "out" / "cube" / "cube.stl").read_bytes()
    assert int.from_bytes(stl[80:84], "little") == 12
