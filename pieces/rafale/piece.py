"""Rafale (Dassault) : maquette d'exposition simplifiée au 1/72, dessous plat.

Le nez pointe vers X = 0, l'aile droite vers +Y. Le dessous est rasé à Z = 0 pour
que l'aile delta et le ventre portent sur le plateau ; les plans canard, le
dessous avant du fuselage et le cône du nez demandent du support.
Silhouette : fuselage lissé par sections elliptiques, aile delta amincie vers le
saumon, plans canard au-dessus des entrées d'air, dérive unique, verrière en
bulle, deux tuyères.
"""

from build123d import (
    Axis,
    Box,
    Cylinder,
    Ellipse,
    Keep,
    Part,
    Plane,
    Polygon,
    Pos,
    Rot,
    Sphere,
    extrude,
    fillet,
    loft,
    mirror,
    scale,
    split,
)

# Fuselage : (x, largeur, hauteur) de chaque section elliptique, du nez à la queue.
SECTIONS = (
    (0.0, 1.0, 1.0),
    (10.0, 7.0, 6.0),
    (30.0, 13.0, 11.0),
    (50.0, 16.0, 14.0),
    (70.0, 18.0, 17.0),
    (90.0, 19.0, 17.0),
    (120.0, 20.0, 17.0),
    (160.0, 22.0, 16.0),
    (195.0, 24.0, 14.0),
    (212.0, 22.0, 12.0),
)
AXE = 0.4  # centre de chaque section, en fraction de sa hauteur : le bas passe sous Z = 0 et se rase

# Demi-aile delta : bord d'attaque à 48°, saumon court.
AILE = ((100.0, 0.0), (167.0, 75.5), (188.0, 75.5), (205.0, 0.0))
EPAISSEUR_AILE_EMPLANTURE = 3.0
EPAISSEUR_AILE_SAUMON = 1.5
Y_EMPLANTURE = 10.0

# Demi-plan canard, posé sur l'entrée d'air.
CANARD = ((80.0, 9.0), (106.0, 36.0), (112.0, 36.0), (102.0, 9.0))
Z_CANARD = 10.5
EPAISSEUR_CANARD = 1.4

# Entrée d'air : bloc sous le canard, bouche ouverte vers l'avant.
ENTREE_X = (85.0, 150.0)
ENTREE_Y = (8.0, 17.0)
HAUTEUR_ENTREE = 11.0
BOUCHE = (5.0, 6.0, 8.0)  # profondeur, largeur, hauteur
CONGE_ENTREE = 3.0

# Dérive, dans le plan XZ.
DERIVE = ((150.0, 10.0), (200.0, 10.0), (208.0, 50.0), (195.0, 50.0))
EPAISSEUR_DERIVE = 2.0

# Verrière : ellipsoïde (centre, demi-axes).
VERRIERE_CENTRE = (66.0, 0.0, 14.0)
VERRIERE_DEMI_AXES = (20.0, 5.5, 6.0)

# Tuyères : deux cylindres le long de X, creusés à l'arrière.
TUYERE_X = (200.0, 216.0)
TUYERE_Y = 5.5
TUYERE_RAYON = 5.0
TUYERE_ALESAGE = (3.8, 6.0)  # rayon, profondeur


def _fuselage() -> Part:
    sections = [
        Plane(origin=(x, 0, AXE * hauteur), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
        * Ellipse(largeur / 2, hauteur / 2)
        for x, largeur, hauteur in SECTIONS
    ]
    return loft(sections)


def _demi_aile() -> Part:
    aile = extrude(Polygon(*AILE, align=None), EPAISSEUR_AILE_EMPLANTURE, dir=(0, 0, 1))
    envergure = AILE[1][1] - Y_EMPLANTURE
    pente = EPAISSEUR_AILE_SAUMON - EPAISSEUR_AILE_EMPLANTURE
    biseau = Plane(origin=(0, Y_EMPLANTURE, EPAISSEUR_AILE_EMPLANTURE), z_dir=(0, -pente, envergure))
    return split(aile, biseau, keep=Keep.BOTTOM)


def _demi_canard() -> Part:
    return Pos(0, 0, Z_CANARD) * extrude(Polygon(*CANARD, align=None), EPAISSEUR_CANARD, dir=(0, 0, 1))


def _entree_air() -> Part:
    longueur = ENTREE_X[1] - ENTREE_X[0]
    largeur = ENTREE_Y[1] - ENTREE_Y[0]
    bloc = Pos(ENTREE_X[0] + longueur / 2, ENTREE_Y[0] + largeur / 2, HAUTEUR_ENTREE / 2) * Box(
        longueur, largeur, HAUTEUR_ENTREE
    )
    arete = bloc.edges().filter_by(Axis.X).sort_by(lambda a: a.center().Y + a.center().Z)[-1]
    bloc = fillet(arete, CONGE_ENTREE)
    profondeur, largeur_bouche, hauteur_bouche = BOUCHE
    bouche = Pos(
        ENTREE_X[0] + profondeur / 2 - 0.5,
        ENTREE_Y[0] + largeur / 2,
        HAUTEUR_ENTREE / 2,
    ) * Box(profondeur + 1.0, largeur_bouche, hauteur_bouche)
    return bloc - bouche


def _derive() -> Part:
    return extrude(Plane.XZ * Polygon(*DERIVE, align=None), EPAISSEUR_DERIVE / 2, both=True)


def _verriere() -> Part:
    return Pos(*VERRIERE_CENTRE) * scale(Sphere(1.0), by=VERRIERE_DEMI_AXES)


def _tuyere(y: float) -> Part:
    longueur = TUYERE_X[1] - TUYERE_X[0]
    return Pos(TUYERE_X[0], y, TUYERE_RAYON) * Rot(0, 90, 0) * Cylinder(TUYERE_RAYON, longueur, align=None)


def _alesage(y: float) -> Part:
    rayon, profondeur = TUYERE_ALESAGE
    return Pos(TUYERE_X[1] - profondeur, y, TUYERE_RAYON) * Rot(0, 90, 0) * Cylinder(
        rayon, profondeur + 1.0, align=None
    )


def construire() -> Part:
    cote = _demi_aile() + _demi_canard() + _entree_air()
    avion = _fuselage() + cote + mirror(cote, Plane.XZ) + _derive() + _verriere()
    avion = avion + _tuyere(TUYERE_Y) + _tuyere(-TUYERE_Y) - _alesage(TUYERE_Y) - _alesage(-TUYERE_Y)
    return split(avion, Plane.XY, keep=Keep.TOP)
