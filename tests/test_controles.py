import pytest
from build123d import Align, Box, BuildPart, Locations

from atelier.controles import AVERTISSEMENT, ECHEC, controler

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
        ((256.0, 256.0, 256.0), [AVERTISSEMENT]),  # limite exacte : imprimable, hors buse auxiliaire
        ((256.01, 10, 10), [ECHEC]),
        ((10, 256.01, 10), [ECHEC]),
        ((10, 10, 260.0), [AVERTISSEMENT]),  # Z entre 256 (auxiliaire) et 260 (principale)
        ((10, 10, 260.01), [ECHEC]),
        ((235.5, 256.0, 256.0), []),
        ((256.0, 235.5, 256.0), []),  # tournée de 90° sur le plateau
        ((240, 240, 10), [AVERTISSEMENT]),
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
