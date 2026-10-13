"""Vues PNG d'une pièce : arêtes vues en noir, arêtes cachées en gris."""

from pathlib import Path

from build123d import Shape, Vector
from PIL import Image, ImageDraw

# nom → (direction de la caméra depuis le centre, haut de l'image)
VUES = {
    "iso": ((1, -1.3, 1), (0, 0, 1)),
    "dessus": ((0, 0, 1), (0, 1, 0)),
    "face": ((0, -1, 0), (0, 0, 1)),
    "droite": ((1, 0, 0), (0, 0, 1)),
}
LARGEUR_PX = 900
MARGE_PX = 40
SEGMENTS = 24
NOIR, GRIS = (20, 20, 20), (190, 190, 190)


def _polyligne(arete):
    return [(p.X, p.Y) for p in (arete.position_at(i / SEGMENTS) for i in range(SEGMENTS + 1))]


def _dessiner(vues, cachees, fichier: Path) -> None:
    traits = [(_polyligne(a), GRIS, 1) for a in cachees] + [(_polyligne(a), NOIR, 3) for a in vues]
    xs = [x for points, _, _ in traits for x, _ in points]
    ys = [y for points, _, _ in traits for _, y in points]
    if not xs:
        raise ValueError("aucune arête à dessiner")
    etendue = max(max(xs) - min(xs), max(ys) - min(ys)) or 1.0
    echelle = (LARGEUR_PX - 2 * MARGE_PX) / etendue
    largeur = int((max(xs) - min(xs)) * echelle) + 2 * MARGE_PX
    hauteur = int((max(ys) - min(ys)) * echelle) + 2 * MARGE_PX
    image = Image.new("RGB", (largeur, hauteur), "white")
    crayon = ImageDraw.Draw(image)
    for points, couleur, epaisseur in traits:
        crayon.line(
            [((x - min(xs)) * echelle + MARGE_PX, hauteur - ((y - min(ys)) * echelle + MARGE_PX)) for x, y in points],
            fill=couleur,
            width=epaisseur,
        )
    image.save(fichier)


def rendre(piece: Shape, dossier: Path) -> list[Path]:
    boite = piece.bounding_box()
    centre = boite.center()
    recul = max(boite.diagonal, 1.0) * 10
    fichiers = []
    for nom, (direction, haut) in VUES.items():
        camera = centre + Vector(*direction).normalized() * recul
        vues, cachees = piece.project_to_viewport(tuple(camera), viewport_up=haut, look_at=tuple(centre))
        fichier = dossier / f"{nom}.png"
        _dessiner(vues, cachees, fichier)
        fichiers.append(fichier)
    return fichiers
