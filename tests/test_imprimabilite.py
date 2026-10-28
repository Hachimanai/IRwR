import pytest
from build123d import Align, Box, BuildPart, BuildSketch, Locations, Mode, Plane, Polygon, extrude

from atelier.controles import AVERTISSEMENT
from atelier.imprimabilite import PAROI_MIN, mesurer, resumer

BAS = (Align.CENTER, Align.CENTER, Align.MIN)


def boite(x, y, z):
    with BuildPart() as piece:
        Box(x, y, z, align=BAS)
    return piece.part


def test_boite_pleine_sans_surplomb_ni_paroi_mince():
    mesures = mesurer(boite(40, 30, 10))
    assert mesures["surplomb_mm2"] == 0 and mesures["surplomb_z"] is None
    assert min(mesures["epaisseurs"]) == pytest.approx(10, abs=0.01)
    assert set(round(e) for e in mesures["epaisseurs"]) <= {10, 30, 40}
    assert resumer(mesures)[1] == []


def test_plateau_en_porte_a_faux():
    with BuildPart() as table:
        Box(10, 10, 10, align=BAS)
        with Locations((0, 0, 10)):
            Box(30, 30, 2, align=BAS)
    mesures = mesurer(table.part)
    assert mesures["surplomb_mm2"] == pytest.approx(30 * 30 - 10 * 10, rel=1e-6)
    assert mesures["surplomb_z"] == pytest.approx([10, 10])
    assert "8.00 cm², Z 10.0 à 10.0 mm" in resumer(mesures)[0]


def talus(pente_x):
    """Prisme dont le flanc droit, vu de face, monte de (10, 0) à (10 + pente_x, 10)."""
    with BuildPart() as piece:
        with BuildSketch(Plane.XZ):
            Polygon((0, 0), (10, 0), (10 + pente_x, 10), (0, 10), align=None)
        extrude(amount=-10)
    return piece.part


@pytest.mark.parametrize(("pente_x", "surplomb"), [(10, False), (12, True), (5, False)])
def test_seuil_a_45_degres(pente_x, surplomb):
    assert (mesurer(talus(pente_x))["surplomb_mm2"] > 0) is surplomb


def test_paroi_mince_avertit():
    with BuildPart() as bac:
        Box(40, 40, 20, align=BAS)
        with Locations((0, 0, 2)):
            Box(39, 39, 20, align=BAS, mode=Mode.SUBTRACT)
    ligne, ecarts = resumer(mesurer(bac.part))
    assert [e.niveau for e in ecarts] == [AVERTISSEMENT]
    assert f"sous {PAROI_MIN:g} mm" in ecarts[0].message
    assert "paroi min 0.50 mm" in ligne


def test_paroi_non_mesuree():
    ligne, ecarts = resumer({"surplomb_mm2": 0.0, "surplomb_z": None, "epaisseurs": []})
    assert "paroi non mesurée" in ligne and ecarts == []
