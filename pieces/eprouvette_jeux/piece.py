"""Éprouvette de jeux : une plaque percée de trous de jeu croissant, et son pion.

Le pion (Ø 8,00 nominal) est relié à la plaque par une languette à casser. On
l'essaie dans chaque trou : le premier où il entre fixe le jeu « glissant »,
le premier où il tombe seul le jeu « libre ». Le coin chanfreiné repère le
côté du jeu nul. Le dernier trou est un perçage M3 lamé, à essayer avec une vis.
"""

from build123d import Align, Axis, Box, BuildPart, Cylinder, Hole, Locations, Part, chamfer

from commun.visserie import percage_lame

DIAMETRE = 8.0
JEUX = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5)
PAS = 14.0
LARGEUR = 20.0
EPAISSEUR = 6.0
HAUTEUR_PION = 12.0
ECART_PION = 2.0
BAS = (Align.CENTER, Align.CENTER, Align.MIN)


def construire() -> Part:
    longueur = PAS * (len(JEUX) + 1)
    with BuildPart() as eprouvette:
        with Locations((longueur / 2, 0, 0)):
            Box(longueur, LARGEUR, EPAISSEUR, align=BAS)
        for rang, jeu in enumerate(JEUX):
            with Locations((PAS / 2 + rang * PAS, 0, EPAISSEUR)):
                Hole(radius=(DIAMETRE + jeu) / 2)
        with Locations((PAS / 2 + len(JEUX) * PAS, 0, EPAISSEUR)):
            percage_lame("M3")
        coin = eprouvette.edges().filter_by(Axis.Z).sort_by(lambda a: a.center().X + a.center().Y)[0]
        chamfer(coin, 4)
        y_pion = -(LARGEUR / 2 + ECART_PION + DIAMETRE / 2)
        with Locations((PAS / 2, y_pion, 0)):
            Cylinder(DIAMETRE / 2, HAUTEUR_PION, align=BAS)
        with Locations((PAS / 2, -(LARGEUR / 2 + ECART_PION / 2), 0)):
            Box(1.2, ECART_PION + 1.0, 0.6, align=BAS)
    return eprouvette.part
