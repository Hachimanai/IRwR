"""Jeux d'ajustement par matériau, en mm, au diamètre.

Valeurs de DÉPART usuelles, pas des mesures sur cette X2D : la pièce
`eprouvette_jeux` sert à les valider, et `docs/conception.md` tient le tableau des
valeurs confirmées par un tirage.
"""

JEUX = {
    "PLA": {"serre": 0.10, "glissant": 0.20, "libre": 0.30},
    "PETG": {"serre": 0.15, "glissant": 0.25, "libre": 0.35},
    "ABS": {"serre": 0.15, "glissant": 0.25, "libre": 0.35},
}


def jeu(materiau: str, ajustement: str) -> float:
    return JEUX[materiau][ajustement]
