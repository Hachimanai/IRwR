"""Contrôles d'une pièce avant export : solide valide (BREP ou maillage), tenue dans la X2D."""

from dataclasses import dataclass

from build123d import Part

from commun.imprimante import VOLUME_BUSE_PRINCIPALE

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
    return ecarts + _controler_boite((boite.size.X, boite.size.Y, boite.size.Z), boite.min.Z)


def _controler_boite(dimensions, z_min: float) -> list[Ecart]:
    """Tenue dans le volume de la X2D et pose sur le plateau, communes aux deux filières."""
    ecarts = []
    if not _tient_dans(dimensions, VOLUME_BUSE_PRINCIPALE):
        ecarts.append(Ecart(ECHEC, f"{_mm(dimensions)} mm dépasse le volume de la X2D ({_mm(VOLUME_BUSE_PRINCIPALE)} mm)"))
    if abs(z_min) > TOLERANCE_PLATEAU:
        ecarts.append(Ecart(AVERTISSEMENT, f"la pièce n'est pas posée sur le plateau (Z min = {z_min:g} mm)"))
    return ecarts


def controler_maillage(mesures: dict) -> list[Ecart]:
    """Les mêmes contrôles sur les mesures d'un maillage Blender (voir `atelier/blender_scene.py`)."""
    if mesures["type"] != "MESH":
        return [Ecart(ECHEC, f"construire() doit rendre un objet maillé (type MESH), reçu {mesures['type']}")]
    if not mesures["faces"]:
        return [Ecart(ECHEC, "le maillage ne contient aucune face")]
    ecarts = []
    if mesures["parties"] > 1:
        ecarts.append(Ecart(ECHEC, f"{mesures['parties']} parties disjointes : une pièce = un seul solide"))
    if mesures["aretes_non_manifold"]:
        ecarts.append(Ecart(ECHEC, f"maillage non étanche : {mesures['aretes_non_manifold']} arêtes non manifold (trou, face en trop ou arête partagée par plus de deux faces)"))
    if mesures["aretes_normales_opposees"]:
        ecarts.append(Ecart(ECHEC, f"normales incohérentes sur {mesures['aretes_normales_opposees']} arêtes (Maillage > Normales > Recalculer à l'extérieur)"))
    if mesures["volume"] <= 0:
        ecarts.append(Ecart(ECHEC, f"volume nul ou négatif ({mesures['volume']:g} mm³) : maillage plat ou normales tournées vers l'intérieur"))
    if "erreur_export" in mesures:
        ecarts.append(Ecart(ECHEC, f"export STL impossible ({mesures['erreur_export']})"))
    elif mesures["triangles_stl"] != mesures["triangles"]:
        ecarts.append(Ecart(ECHEC, f"le STL exporté a {mesures['triangles_stl']} triangles, le maillage contrôlé {mesures['triangles']}"))
    minimum, maximum = mesures["boite_min"], mesures["boite_max"]
    return ecarts + _controler_boite(tuple(b - a for a, b in zip(minimum, maximum)), minimum[2])
