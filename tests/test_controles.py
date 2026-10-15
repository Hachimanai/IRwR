import pytest
from build123d import Align, Box, BuildPart, Locations

from atelier.controles import AVERTISSEMENT, ECHEC, controler, controler_maillage

BAS = (Align.CENTER, Align.CENTER, Align.MIN)


def boite(x, y, z, *positions):
    with BuildPart() as piece:
        with Locations(*(positions or [(0, 0, 0)])):
            Box(x, y, z, align=BAS)
    return piece.part


def niveaux(piece):
    return [e.niveau for e in controler(piece)]


def test_solide_valide_sans_ecart():
    assert controler(boite(40, 30, 10)) == []


@pytest.mark.parametrize(
    ("dimensions", "attendu"),
    [
        ((256.0, 256.0, 256.0), []),  # limite exacte
        ((256.01, 10, 10), [ECHEC]),
        ((10, 256.01, 10), [ECHEC]),
        ((10, 10, 260.0), []),  # hauteur maximale de la buse principale
        ((10, 10, 260.01), [ECHEC]),
        ((235.5, 256.0, 256.0), []),
        ((256.0, 235.5, 256.0), []),  # tournée de 90° sur le plateau
        ((240, 240, 10), []),  # hors buse auxiliaire : sans effet, elle ne sert pas
    ],
)
def test_limites_du_volume(dimensions, attendu):
    assert niveaux(boite(*dimensions)) == attendu


def test_deux_solides_disjoints():
    assert niveaux(boite(10, 10, 10, (0, 0, 0), (50, 0, 0))) == [ECHEC]


def test_piece_decollee_du_plateau():
    assert niveaux(boite(10, 10, 10, (0, 0, 5))) == [AVERTISSEMENT]


@pytest.mark.parametrize("intrus", [None, "piece", 42])
def test_pas_un_part(intrus):
    assert niveaux(intrus) == [ECHEC]


def test_part_vide():
    with BuildPart() as vide:
        pass
    assert niveaux(vide.part) == [ECHEC]


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


@pytest.mark.parametrize(
    ("ecart", "attendu"),
    [
        ({}, []),
        ({"parties": 2}, [ECHEC]),
        ({"aretes_non_manifold": 4}, [ECHEC]),
        ({"aretes_normales_opposees": 3}, [ECHEC]),
        ({"volume": -1000.0}, [ECHEC]),  # normales tournées vers l'intérieur
        ({"volume": 0.0}, [ECHEC]),
        ({"triangles_stl": 0}, [ECHEC]),  # objet masqué : STL vide
        ({"erreur_export": "RuntimeError : ViewLayer does not contain object"}, [ECHEC]),
        ({"boite_min": [0, 0, 5], "boite_max": [10, 10, 15]}, [AVERTISSEMENT]),
        ({"boite_max": [5, 5, 260.01]}, [ECHEC]),
        ({"boite_min": [-120, -120, 0], "boite_max": [120, 120, 10]}, []),  # 240 × 240 : hors buse auxiliaire, sans effet
    ],
)
def test_maillage(ecart, attendu):
    assert [e.niveau for e in controler_maillage(CUBE | ecart)] == attendu


@pytest.mark.parametrize("mesures", [{"type": "CURVE"}, {"type": "str"}, CUBE | {"faces": 0}])
def test_maillage_absent(mesures):
    assert [e.niveau for e in controler_maillage(mesures)] == [ECHEC]
