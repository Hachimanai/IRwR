"""Perçages pour vis métriques M2 à M5, en mm.

À appeler dans un `BuildPart`, sous un `Locations` posé sur la face percée.
"""

from build123d import CounterBoreHole, Hole

# Trou de passage, série moyenne (ISO 273).
PASSAGE = {"M2": 2.4, "M2.5": 2.9, "M3": 3.4, "M4": 4.5, "M5": 5.5}
# Tête cylindrique à six pans creux (ISO 4762) : (diamètre, hauteur).
TETE = {"M2": (3.8, 2.0), "M2.5": (4.5, 2.5), "M3": (5.5, 3.0), "M4": (7.0, 4.0), "M5": (8.5, 5.0)}
MARGE_TETE = 0.4


def percage_passage(taille: str, profondeur: float | None = None):
    return Hole(radius=PASSAGE[taille] / 2, depth=profondeur)


def percage_lame(taille: str, profondeur: float | None = None):
    """Trou de passage avec lamage noyant la tête cylindrique."""
    diametre, hauteur = TETE[taille]
    return CounterBoreHole(
        radius=PASSAGE[taille] / 2,
        counter_bore_radius=(diametre + MARGE_TETE) / 2,
        counter_bore_depth=hauteur + MARGE_TETE / 2,
        depth=profondeur,
    )
