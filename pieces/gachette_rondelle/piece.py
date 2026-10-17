"""Rondelle du pivot de la détente : remplace le bossage côté plateau de `gachette`.

Le bossage d'origine dépasse des deux flancs ; imprimée à plat, la détente ne garde que celui
du dessus, et cette rondelle, enfilée sur l'axe côté dessous, rend l'encombrement d'origine.
Cotes reprises de `pieces/gachette/piece.py` : les changer ensemble.
"""

from build123d import Align, BuildPart, Cylinder, Mode, Part

MATERIAU = "PETG"
DIAMETRE_EXTERIEUR = 9.0  # = DIAMETRE_BOSSAGE de gachette
EPAISSEUR = 1.7  # = SAILLIE_BOSSAGE de gachette
DIAMETRE_INTERIEUR = 3.5  # = DIAMETRE_ALESAGE de gachette, trou de l'original


def construire() -> Part:
    bas = (Align.CENTER, Align.CENTER, Align.MIN)
    with BuildPart() as rondelle:
        Cylinder(DIAMETRE_EXTERIEUR / 2, EPAISSEUR, align=bas)
        Cylinder(DIAMETRE_INTERIEUR / 2, EPAISSEUR, align=bas, mode=Mode.SUBTRACT)
    return rondelle.part
