"""Détente : levier pivotant, avec une chape où se loge la gâchette et deux vis M3 de réglage.

Reproduction d'une pièce moulée fissurée au pied de sa chape. Le profil (vu de flanc) est
relevé sur une photo à plat avec un mètre ruban dans le plan, puis recalé sur la longueur et
la hauteur hors tout mesurées au pied à coulisse ; il s'extrude sur l'épaisseur du corps.
S'y ajoutent : le bossage du pivot (côté dessus seulement, celui du dessous est la pièce
`gachette_rondelle`), la fente de la chape dans le plan médian, les deux taraudages M3 qui
débouchent au fond de la fente, et le téton de l'encoche.

Repère : X de l'arrière du crochet vers le bout de la lame, Y du bas de la lame vers le
pivot, Z l'épaisseur. La pièce s'imprime à plat sur son flanc, les couches dans le plan du
profil : l'effort du doigt et celui du pivot tirent le long des couches.
"""

from math import asin, atan2, cos, hypot, sin, sqrt

from build123d import (
    Align,
    BuildLine,
    BuildPart,
    BuildSketch,
    Circle,
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    Polygon,
    Polyline,
    Spline,
    extrude,
    make_face,
)

from commun.jeux import jeu

MATERIAU = "PETG"

# Pied à coulisse, 2026-10-17, sauf mention contraire.
EPAISSEUR = 6.8  # flanc à flanc, hors bossage
LONGUEUR = 50.2  # hors tout, du crochet au bout de la lame
HAUTEUR = 44.3  # hors tout, du bas de la lame au haut du bossage

# Pivot.
DIAMETRE_BOSSAGE = 9.0  # bord tangent au dos de la plaque et au pan supérieur, sans déport
SAILLIE_BOSSAGE = (10.2 - EPAISSEUR) / 2  # 10,2 hors tout aux deux bossages
DIAMETRE_ALESAGE = 3.5  # trou de l'original ; l'axe est un peu plus petit et tourne libre

# Chape : fente dans le plan médian, ouverte sur le dos de la plaque et autour du pivot.
# Son fond est un plan parallèle à la face avant, qui descend jusqu'à l'arête du cran.
EPAISSEUR_GACHETTE = 3.4  # fente de l'original : 3,5
LARGEUR_FENTE = EPAISSEUR_GACHETTE + jeu(MATERIAU, "glissant")
PROFONDEUR_FENTE = 7.5  # mesurée du dos au fond : contrôle seulement, le fond suit l'arête

# Vis de réglage M3, taraudées dans le PETG, perpendiculaires à la face avant et au fond.
DIAMETRE_TARAUDAGE = 2.5  # perçage de taraudage M3 ; trous de l'original : 2,4
ENTRAXE_VIS = 6.0
ARETE_VIS = 3.4  # le long de la face avant, de son arête du haut au bord du trou de la vis haute
DIAMETRE_TROU_ORIGINE = 2.4  # pour passer du bord mesuré au centre

# Téton dans l'encoche, axe selon X, sortant du bord de l'encoche vers l'arrière.
TETON_DIAMETRE = 3.4
TETON_SAILLIE = 2.6

# --- Relevé sur la photo à plat, avant recalage (mm de la photo) ---
PIVOT_PHOTO = (12.5, 41.9)
DOS_BAS = (4.1, 26.45)  # coin bas du dos de la plaque ; le dos monte, tangent au bossage
CRAN_HAUT = (12.5, 24.4)  # coin du cran sous la plaque, où débouche le fond de la fente
ENCOCHE_HAUT = (15.3, 18.3)  # le cran descend jusqu'au haut de l'encoche
FACE_AVANT = ((25.4, 35.9), (23.0, 21.25))  # arête du haut, puis départ de la lame
BORD_ENCOCHE_X = 16.9
TETON_Y_PHOTO = 14.15
DEBUT_CONTOUR = [  # sens horaire depuis le bas du crochet, jusqu'au haut de l'encoche
    (0.0, 5.8), (0.0, 12.5), (4.5, 12.5), (4.5, 8.5),  # crochet
    (14.6, 8.5), (BORD_ENCOCHE_X, 11.2),  # bras, pan vers l'encoche
    (BORD_ENCOCHE_X, 15.8), ENCOCHE_HAUT,  # encoche
]
LAME = [  # intérieur de la lame, bout arrondi, dessous : une seule courbe
    (23.0, 21.25), (25.0, 18.0), (28.0, 14.0), (31.0, 10.5), (34.0, 8.0), (37.0, 6.5),
    (40.5, 5.6), (45.0, 5.5), (49.0, 6.25), (51.2, 5.6), (51.9, 4.5), (51.2, 3.5),
    (47.0, 2.25), (42.0, 1.25), (37.0, 0.9), (32.0, 1.4), (28.0, 3.0), (25.0, 4.5),
    (21.5, 5.1), (19.9, 4.4), (16.9, 2.8), (14.6, 1.1), (13.0, 0.1),
]
CONTOUR_PIED = [  # petit pied sous le bras, retour au crochet
    (13.0, 0.1), (9.9, 0.1), (9.9, 1.8), (7.1, 1.8), (7.1, 5.8), (0.0, 5.8),
]

# Recalage : la photo sort le profil 3 à 5 % trop grand. Les échelles ramènent la longueur et
# la hauteur hors tout (bossage compris, Ø mesuré) sur les mesures.
X_MAX_PHOTO, Y_MIN_PHOTO = 51.9, 0.1
ECHELLE_X = LONGUEUR / X_MAX_PHOTO
ECHELLE_Y = (HAUTEUR - DIAMETRE_BOSSAGE / 2) / (PIVOT_PHOTO[1] - Y_MIN_PHOTO)


def _recale(x, y):
    return x * ECHELLE_X, (y - Y_MIN_PHOTO) * ECHELLE_Y


def _unitaire(dx, dy):
    n = hypot(dx, dy)
    return dx / n, dy / n


def _tangente(depuis, centre, rayon, sens):
    """Point où la droite issue de `depuis` touche le cercle ; sens +1 à gauche, -1 à droite."""
    (px, py), (cx, cy) = depuis, centre
    d = hypot(cx - px, cy - py)
    a = atan2(cy - py, cx - px) + sens * asin(rayon / d)
    longueur = sqrt(d * d - rayon * rayon)
    return px + longueur * cos(a), py + longueur * sin(a)


PIVOT = _recale(*PIVOT_PHOTO)
ARETE, PIED_FACE = (_recale(*q) for q in FACE_AVANT)
DIRECTION = _unitaire(ARETE[0] - PIED_FACE[0], ARETE[1] - PIED_FACE[1])  # face avant, vers le haut
NORMALE = (DIRECTION[1], -DIRECTION[0])  # sortante de la face avant, vers l'avant


Y_ENTRE_VIS = ARETE[1] - (ARETE_VIS + DIAMETRE_TROU_ORIGINE / 2 + ENTRAXE_VIS / 2) * DIRECTION[1]


def _sur_dos(y):
    dos_bas = _recale(*DOS_BAS)
    tx, ty = _tangente(dos_bas, PIVOT, DIAMETRE_BOSSAGE / 2, +1)
    return dos_bas[0] + (y - dos_bas[1]) * (tx - dos_bas[0]) / (ty - dos_bas[1]), y


def _sur_fond(y):
    """Point du plan de fond à la hauteur y : il passe par l'arête du cran."""
    x0, y0 = _recale(*CRAN_HAUT)
    return x0 + (y - y0) * DIRECTION[0] / DIRECTION[1], y


def profondeur_fente(y=Y_ENTRE_VIS):
    """Du dos au fond, perpendiculairement au dos : à comparer à PROFONDEUR_FENTE."""
    (ax, ay), (bx, by) = _sur_dos(y), _sur_dos(y + 1.0)
    dx, dy = _unitaire(bx - ax, by - ay)
    return (_sur_fond(y)[0] - ax) * dy


def construire() -> Part:
    rayon = DIAMETRE_BOSSAGE / 2
    dos_bas = _recale(*DOS_BAS)
    contour = [
        *(_recale(*q) for q in DEBUT_CONTOUR),
        (_recale(*CRAN_HAUT)[0], _recale(*ENCOCHE_HAUT)[1]),  # cran, relevé sur la photo
        _recale(*CRAN_HAUT),
        dos_bas,
        _tangente(dos_bas, PIVOT, rayon, +1),  # dos, tangent au bossage
        _tangente(ARETE, PIVOT, rayon, -1),  # pan supérieur, tangent au bossage
        ARETE,
        PIED_FACE,  # face avant, où débouchent les vis
    ]
    with BuildPart() as detente:
        with BuildSketch():
            with BuildLine():
                Polyline(*contour)
                Spline(*(_recale(*q) for q in LAME))
                Polyline(*(_recale(*q) for q in CONTOUR_PIED))
            make_face()
        extrude(amount=EPAISSEUR)

        with Locations((*PIVOT, 0)):
            Cylinder(rayon, EPAISSEUR + SAILLIE_BOSSAGE, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # Téton : cylindre d'axe X, tiré depuis son bout vers l'intérieur du corps.
        bord_x, teton_y = _recale(BORD_ENCOCHE_X, TETON_Y_PHOTO)
        plan_teton = Plane(origin=(bord_x - TETON_SAILLIE, teton_y, EPAISSEUR / 2), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
        with BuildSketch(plan_teton):
            Circle(TETON_DIAMETRE / 2)
        extrude(amount=TETON_SAILLIE + 0.5)

        # Fente : tout ce qui est derrière le plan de fond, au-dessus du dessous de la plaque.
        bas = _sur_fond(_recale(*CRAN_HAUT)[1])
        haut = _sur_fond(PIVOT[1] + DIAMETRE_BOSSAGE)
        z_fente = (EPAISSEUR - LARGEUR_FENTE) / 2
        with BuildSketch(Plane.XY.offset(z_fente)):
            Polygon((-5.0, bas[1]), bas, haut, (-5.0, haut[1]), align=None)
        extrude(amount=LARGEUR_FENTE, mode=Mode.SUBTRACT)

        with Locations((*PIVOT, 0)):
            Cylinder(DIAMETRE_ALESAGE / 2, 3 * EPAISSEUR, mode=Mode.SUBTRACT)

        # Taraudages M3, perpendiculaires à la face avant, jusqu'à 1 mm au-delà du fond.
        fx, fy = _sur_fond(0.0)
        profondeur = (ARETE[0] - fx) * NORMALE[0] + (ARETE[1] - fy) * NORMALE[1]
        for le_long in (ARETE_VIS + DIAMETRE_TROU_ORIGINE / 2, ARETE_VIS + DIAMETRE_TROU_ORIGINE / 2 + ENTRAXE_VIS):
            x = ARETE[0] - le_long * DIRECTION[0] + 2.0 * NORMALE[0]
            y = ARETE[1] - le_long * DIRECTION[1] + 2.0 * NORMALE[1]
            plan_vis = Plane(origin=(x, y, EPAISSEUR / 2), x_dir=(0, 0, 1), z_dir=(-NORMALE[0], -NORMALE[1], 0))
            with BuildSketch(plan_vis):
                Circle(DIAMETRE_TARAUDAGE / 2)
            extrude(amount=2.0 + profondeur + 1.0, mode=Mode.SUBTRACT)
    return detente.part
