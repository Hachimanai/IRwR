"""Contrôles d'une pièce avant export : solide valide, tenue dans la X2D."""

from dataclasses import dataclass

from build123d import Part

from commun.imprimante import VOLUME_BUSE_AUXILIAIRE, VOLUME_BUSE_PRINCIPALE

ECHEC = "ÉCHEC"
AVERTISSEMENT = "AVERTISSEMENT"
TOLERANCE = 0.001
TOLERANCE_PLATEAU = 0.01


@dataclass(frozen=True)
class Ecart:
    niveau: str
    message: str


def _tient_dans(dimensions, volume) -> bool:
    # La pièce peut tourner de 90° sur le plateau : X et Y se comparent triés.
    x, y = sorted(dimensions[:2])
    vx, vy = sorted(volume[:2])
    return x <= vx + TOLERANCE and y <= vy + TOLERANCE and dimensions[2] <= volume[2] + TOLERANCE


def _mm(valeurs) -> str:
    return " × ".join(f"{v:g}" for v in valeurs)


def controler(piece) -> list[Ecart]:
    if not isinstance(piece, Part):
        return [Ecart(ECHEC, f"construire() doit rendre un Part build123d, reçu {type(piece).__name__}")]
    solides = piece.solids()
    if not solides:
        return [Ecart(ECHEC, "la pièce ne contient aucun solide")]
    ecarts = []
    if len(solides) > 1:
        ecarts.append(Ecart(ECHEC, f"{len(solides)} solides disjoints : une pièce = un seul solide"))
    if not piece.is_valid:
        ecarts.append(Ecart(ECHEC, "géométrie invalide (is_valid faux)"))
    if piece.volume <= 0:
        ecarts.append(Ecart(ECHEC, f"volume nul ou négatif ({piece.volume:g} mm³)"))
    boite = piece.bounding_box()
    dimensions = (boite.size.X, boite.size.Y, boite.size.Z)
    if not _tient_dans(dimensions, VOLUME_BUSE_PRINCIPALE):
        ecarts.append(Ecart(ECHEC, f"{_mm(dimensions)} mm dépasse le volume de la X2D ({_mm(VOLUME_BUSE_PRINCIPALE)} mm)"))
    elif not _tient_dans(dimensions, VOLUME_BUSE_AUXILIAIRE):
        ecarts.append(Ecart(AVERTISSEMENT, f"{_mm(dimensions)} mm dépasse le volume de la buse auxiliaire ({_mm(VOLUME_BUSE_AUXILIAIRE)} mm) : pas de support par la seconde buse sur toute la pièce"))
    if abs(boite.min.Z) > TOLERANCE_PLATEAU:
        ecarts.append(Ecart(AVERTISSEMENT, f"la pièce n'est pas posée sur le plateau (Z min = {boite.min.Z:g} mm)"))
    return ecarts
