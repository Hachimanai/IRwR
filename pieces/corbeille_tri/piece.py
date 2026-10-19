"""Corbeille de tri : bac hexagonal ouvert, pour que l'enfant y range ses jouets par couleur.

Une seule pièce, imprimée une fois par couleur (filament choisi dans Bambu Studio). Parois
évasées : les bacs vides s'emboîtent les uns dans les autres, et vus de dessus ils se
posent côte à côte en nid d'abeille. Aucune arête vive : coins arrondis, fond intérieur en
congé (facile à vider et à nettoyer), bord du haut arrondi.

S'imprime ouverture vers le haut : la dépouille reste loin des 45°, aucun support.
"""

from math import cos, radians, tan

from build123d import (
    Axis,
    BuildPart,
    BuildSketch,
    Mode,
    Part,
    Plane,
    RegularPolygon,
    chamfer,
    fillet,
    loft,
)

MATERIAU = "PLA"

PLATS_HAUT = 150.0  # entre plats opposés, au bord du haut, à l'extérieur
HAUTEUR = 80.0
DEPOUILLE = 8.0  # degrés ; un bac gigogne dépasse de PAROI / tan(DEPOUILLE) ≈ 17 mm
PAROI = 2.4  # épaisseur normale à la paroi : six largeurs de buse 0,4
FOND = 2.0
RAYON_COIN = 12.0  # coins verticaux de l'hexagone, à l'extérieur
CONGE_FOND = 8.0  # raccord intérieur paroi / fond
CONGE_BORD = 1.1  # bord du haut, presque un demi-rond
CHANFREIN_PIED = 0.8  # arête posée sur le plateau (patte d'éléphant)

_PENTE = tan(radians(DEPOUILLE))
_PAROI_HORIZONTALE = PAROI / cos(radians(DEPOUILLE))


def _plats_exterieurs(z: float) -> float:
    return PLATS_HAUT - 2 * (HAUTEUR - z) * _PENTE


def _tronc(z_bas: float, z_haut: float, retrait: float, rayon: float) -> Part:
    """Tronc de pyramide hexagonale à coins arrondis, retrait horizontal pris sur l'extérieur."""
    with BuildPart() as tronc:
        for z in (z_bas, z_haut):
            with BuildSketch(Plane.XY.offset(z)) as esquisse:
                RegularPolygon((_plats_exterieurs(z) / 2) - retrait, 6, major_radius=False)
                fillet(esquisse.vertices(), rayon)
        loft()
    return tronc.part


def construire() -> Part:
    exterieur = _tronc(0, HAUTEUR, 0, RAYON_COIN)
    exterieur = chamfer(exterieur.edges().group_by(Axis.Z)[0], CHANFREIN_PIED)

    rayon_interieur = RAYON_COIN - _PAROI_HORIZONTALE
    cavite = _tronc(FOND, HAUTEUR + 5, _PAROI_HORIZONTALE, rayon_interieur)
    cavite = fillet(cavite.edges().group_by(Axis.Z)[0], CONGE_FOND)

    bac = exterieur - cavite
    return fillet(bac.edges().group_by(Axis.Z)[-1], CONGE_BORD)
