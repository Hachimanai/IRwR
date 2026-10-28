"""Imprimabilité : surplombs et épaisseur de paroi, mesurés avant export.

Ces mesures ne bloquent jamais l'export : un surplomb peut être voulu (support peint, pont),
une paroi mince aussi (sommet d'un filet, bord arrondi). Elles s'affichent pour être
comparées au `NOTES.md` de la pièce ; seule une part notable de paroi mince avertit.

Filière build123d : mesures ici, sur le BREP (rayons exacts) et sa tessellation. Filière
Blender : mêmes mesures dans `atelier/blender_scene.py` (sans numpy ni OCP), avec les
paramètres de `PARAMETRES`, puis le même `resumer`.
"""

from math import radians, sin

import numpy as np
from build123d import Part
from OCP.gp import gp_Dir, gp_Lin, gp_Pnt
from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector

from atelier.controles import AVERTISSEMENT, Ecart

ANGLE_SURPLOMB = 45.0  # degrés depuis la verticale (docs/conception.md)
MARGE_ANGLE = 0.5  # un chanfrein à 45° tout juste n'est pas un surplomb
PAROI_MIN = 0.8  # deux largeurs de buse 0,4 (docs/conception.md)
PART_MINCE_MAX = 0.01  # au-delà de 1 % de la surface sous PAROI_MIN : avertissement
ECHANTILLONS = 2000  # points tirés sur la surface, au prorata de l'aire
ECART_RAYON = 0.15  # mm : ignore l'impact sur sa propre face (écart de tessellation)
TOLERANCE_PLATEAU = 0.01  # une face à moins de ça du bas est posée, pas en surplomb
TOLERANCE_TESSELLATION = 0.05
PARAMETRES = {
    "seuil_normale": -sin(radians(ANGLE_SURPLOMB + MARGE_ANGLE)),
    "echantillons": ECHANTILLONS,
    "ecart_rayon": ECART_RAYON,
    "tolerance_plateau": TOLERANCE_PLATEAU,
}


def mesurer(piece: Part) -> dict:
    """Surplombs et épaisseurs d'un Part : le même dictionnaire que la filière Blender."""
    sommets, triangles = piece.tessellate(TOLERANCE_TESSELLATION, 0.2)
    points = np.array([tuple(v) for v in sommets])
    a, b, c = (points[np.array(triangles)[:, i]] for i in range(3))
    produit = np.cross(b - a, c - a)
    aires = np.linalg.norm(produit, axis=1) / 2
    garde = aires > 1e-12
    a, b, c, produit, aires = a[garde], b[garde], c[garde], produit[garde], aires[garde]
    normales = produit / (2 * aires[:, None])

    bas = points[:, 2].min() + TOLERANCE_PLATEAU
    posee = (a[:, 2] < bas) & (b[:, 2] < bas) & (c[:, 2] < bas)
    surplomb = (normales[:, 2] < PARAMETRES["seuil_normale"]) & ~posee
    hauteurs = (a[surplomb, 2] + b[surplomb, 2] + c[surplomb, 2]) / 3

    tirage = np.random.default_rng(0)
    choisis = tirage.choice(len(aires), ECHANTILLONS, p=aires / aires.sum())
    r1, r2 = np.sqrt(tirage.random(ECHANTILLONS)), tirage.random(ECHANTILLONS)
    departs = ((1 - r1)[:, None] * a[choisis] + (r1 * (1 - r2))[:, None] * b[choisis]
               + (r1 * r2)[:, None] * c[choisis])
    intersection = IntCurvesFace_ShapeIntersector()
    intersection.Load(piece.wrapped, 1e-6)
    epaisseurs = []
    for depart, direction in zip(departs, -normales[choisis]):
        intersection.Perform(gp_Lin(gp_Pnt(*depart), gp_Dir(*direction)), ECART_RAYON, 1e6)
        if intersection.IsDone() and intersection.NbPnt():
            epaisseurs.append(min(intersection.WParameter(i) for i in range(1, intersection.NbPnt() + 1)))

    return {
        "surplomb_mm2": float(aires[surplomb].sum()),
        "surplomb_z": [float(hauteurs.min()), float(hauteurs.max())] if surplomb.any() else None,
        "epaisseurs": epaisseurs,
    }


def resumer(mesures: dict) -> tuple[str, list[Ecart]]:
    """La ligne à afficher et l'avertissement de paroi mince, communs aux deux filières."""
    surface = mesures["surplomb_mm2"]
    if mesures["surplomb_z"]:
        z_bas, z_haut = mesures["surplomb_z"]
        surplomb = f"surplombs > {ANGLE_SURPLOMB:g}° : {surface / 100:.2f} cm², Z {z_bas:.1f} à {z_haut:.1f} mm"
    else:
        surplomb = f"aucun surplomb > {ANGLE_SURPLOMB:g}°"
    epaisseurs = np.array(mesures["epaisseurs"])
    if not epaisseurs.size:
        return f"imprimabilité : {surplomb} ; paroi non mesurée", []
    mince = float((epaisseurs < PAROI_MIN).mean())
    ligne = (f"imprimabilité : {surplomb} ; paroi min {epaisseurs.min():.2f} mm, "
             f"5 % sous {np.percentile(epaisseurs, 5):.2f} mm, {mince:.1%} sous {PAROI_MIN:g} mm")
    ecarts = []
    if mince > PART_MINCE_MAX:
        ecarts.append(Ecart(AVERTISSEMENT, f"parois minces : {mince:.1%} de la surface sous {PAROI_MIN:g} mm "
                                           f"(min {epaisseurs.min():.2f} mm), deux largeurs de buse au moins"))
    return ligne, ecarts
