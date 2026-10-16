"""Porte-avions Charles de Gaulle (R91) : maquette « ligne de flottaison » au 1/1200.

La coque est coupée à la flottaison, posée sur Z = 0. Toutes les cotes s'écrivent en
mètres réels et passent à l'échelle par `ECHELLE`. La poupe est en X = 0, l'étrave
vers +X, bâbord vers +Y : l'îlot est à tribord (Y < 0) et la piste oblique déborde
à bâbord. La coque est un loft réglé entre le contour de flottaison et le contour
du pont d'envol, point pour point : ses flancs s'évasent sans dépasser 50° de la
verticale. Piste oblique, catapultes et ascenseurs sont gravés dans le pont.
"""

from math import atan2, degrees, hypot

from build123d import Align, Box, Part, Pos, Rot, Solid, Vector, Wire

ECHELLE = 1 / 1200  # mm de maquette par mm réel ; les cotes ci-dessous sont en mètres réels
MM_PAR_M = 1000 * ECHELLE

# Contours appariés (pont d'envol, flottaison), même ordre, en m. Longueur hors tout 261,5,
# largeur du pont 64,4, largeur à la flottaison 31,5.
CONTOURS = (
    ((0.0, -14.0), (8.0, -12.0)),
    ((0.0, 14.0), (8.0, 12.0)),
    ((10.0, 18.0), (15.0, 13.5)),
    ((40.0, 26.0), (40.0, 15.5)),
    ((80.0, 32.2), (80.0, 15.75)),
    ((125.0, 32.2), (125.0, 15.75)),
    ((150.0, 24.0), (150.0, 15.5)),
    ((175.0, 17.0), (175.0, 14.5)),
    ((220.0, 16.0), (215.0, 10.0)),
    ((250.0, 10.0), (240.0, 4.5)),
    ((261.5, 4.0), (252.0, 0.5)),
    ((261.5, -4.0), (252.0, -0.5)),
    ((250.0, -12.0), (240.0, -4.5)),
    ((220.0, -18.0), (215.0, -10.0)),
    ((195.0, -24.0), (190.0, -13.5)),
    ((185.0, -31.0), (185.0, -15.0)),
    ((95.0, -31.0), (95.0, -15.75)),
    ((70.0, -26.0), (70.0, -15.75)),
    ((30.0, -20.0), (30.0, -15.0)),
    ((10.0, -17.0), (15.0, -13.5)),
)
FRANC_BORD = 16.0  # hauteur du pont d'envol au-dessus de la flottaison, m

# Îlot à tribord : deux blocs en retrait, puis le mât. (x début, x fin, y début, y fin, hauteur), m.
ILOT_BAS = (140.0, 176.0, -29.5, -20.0, 9.0)
ILOT_HAUT = (146.0, 170.0, -28.5, -21.5, 8.0)
MAT = (152.0, 157.0, -27.0, -23.0, 14.0)

# Gravures, en mm de maquette (trop fines pour s'écrire en mètres réels utiles).
GRAVURE_LARGEUR = 0.5
GRAVURE_PROFONDEUR = 0.3

# Axe de la piste oblique et catapultes : segments (x, y) → (x, y), m.
PISTE_OBLIQUE = ((12.0, -6.0), (150.0, 15.0))
CATAPULTES = (
    ((170.0, -4.0), (255.0, -2.0)),
    ((60.0, 14.0), (140.0, 26.0)),
)
# Ascenseurs à tribord, en bord de pont : (x début, x fin, y début), m ; ils débordent du pont.
ASCENSEURS = ((96.0, 114.0, -31.0), (118.0, 136.0, -31.0))
PROFONDEUR_ASCENSEUR = 14.0

BAS = (Align.MIN, Align.MIN, Align.MIN)


def _mm(*valeurs: float) -> list[float]:
    return [v * MM_PAR_M for v in valeurs]


def _contour(points: list[tuple[float, float]], z: float) -> Wire:
    return Wire.make_polygon([Vector(*_mm(x, y, z)) for x, y in points], close=True)


def _coque() -> Part:
    flottaison = _contour([f for _, f in CONTOURS], 0.0)
    pont = _contour([p for p, _ in CONTOURS], FRANC_BORD)
    return Part(Solid.make_loft([flottaison, pont], ruled=True).wrapped)


def _bloc(x0: float, x1: float, y0: float, y1: float, hauteur: float, z0: float) -> Part:
    x0, x1, y0, y1, hauteur, z0 = _mm(x0, x1, y0, y1, hauteur, z0)
    return Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, hauteur, align=BAS)


def _ilot() -> Part:
    bas = _bloc(*ILOT_BAS, z0=FRANC_BORD)
    haut = _bloc(*ILOT_HAUT, z0=FRANC_BORD + ILOT_BAS[4])
    mat = _bloc(*MAT, z0=FRANC_BORD + ILOT_BAS[4] + ILOT_HAUT[4])
    return bas + haut + mat


def _sillon(debut: tuple[float, float], fin: tuple[float, float]) -> Part:
    (x0, y0), (x1, y1) = _mm(*debut), _mm(*fin)
    centre = Pos((x0 + x1) / 2, (y0 + y1) / 2, FRANC_BORD * MM_PAR_M)
    angle = degrees(atan2(y1 - y0, x1 - x0))
    return centre * Rot(0, 0, angle) * Box(hypot(x1 - x0, y1 - y0), GRAVURE_LARGEUR, 2 * GRAVURE_PROFONDEUR)


def _cadre_ascenseur(x0: float, x1: float, y0: float) -> Part:
    z = FRANC_BORD * MM_PAR_M - GRAVURE_PROFONDEUR
    x0, x1, y0, profondeur = _mm(x0, x1, y0, PROFONDEUR_ASCENSEUR)
    exterieur = Pos(x0, y0, z) * Box(x1 - x0, profondeur, 2 * GRAVURE_PROFONDEUR, align=BAS)
    l = GRAVURE_LARGEUR
    interieur = Pos(x0 + l, y0 - 1.0, z) * Box(x1 - x0 - 2 * l, profondeur + 1.0 - l, 2 * GRAVURE_PROFONDEUR, align=BAS)
    return exterieur - interieur


def construire() -> Part:
    navire = _coque() + _ilot()
    for debut, fin in (PISTE_OBLIQUE, *CATAPULTES):
        navire -= _sillon(debut, fin)
    for ascenseur in ASCENSEURS:
        navire -= _cadre_ascenseur(*ascenseur)
    return navire
