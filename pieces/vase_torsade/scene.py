"""Vase torsadé : une coque à lobes qui tourne en montant, épaissie par un modificateur.

Forme libre, le cas où Blender sert mieux que build123d. La coque (fond fermé, col ouvert)
est construite face à face avec bmesh, puis un modificateur Solidify lui donne son épaisseur
vers l'intérieur : le pied reste sur Z = 0.
"""

import math

import bmesh
import bpy

HAUTEUR = 150.0
RAYON_PIED = 35.0
RAYON_VENTRE = 50.0
RAYON_COL = 30.0
LOBES = 7
PROFONDEUR_LOBE = 4.0
TORSION = math.radians(120)  # rotation des lobes entre le pied et le col
EPAISSEUR = 2.0  # deux largeurs de buse de 0,4 mm, et de la marge
COUCHES = 120
SECTEURS = 168


def _rayon(t: float, angle: float) -> float:
    """Rayon de la coque à la hauteur relative `t` (0 pied, 1 col) et à l'angle `angle`."""
    droit = RAYON_PIED * (1 - t) + RAYON_COL * t
    ventre = (RAYON_VENTRE - (RAYON_PIED + RAYON_COL) / 2) * 4 * t * (1 - t)
    lobe = PROFONDEUR_LOBE * math.cos(LOBES * (angle - TORSION * t))
    return droit + ventre + lobe


def construire():
    coque = bmesh.new()
    anneaux = []
    for couche in range(COUCHES + 1):
        t = couche / COUCHES
        anneau = []
        for secteur in range(SECTEURS):
            angle = 2 * math.pi * secteur / SECTEURS
            r = _rayon(t, angle)
            anneau.append(coque.verts.new((r * math.cos(angle), r * math.sin(angle), HAUTEUR * t)))
        anneaux.append(anneau)
    for bas, haut in zip(anneaux, anneaux[1:]):
        for i in range(SECTEURS):
            j = (i + 1) % SECTEURS
            coque.faces.new((bas[i], bas[j], haut[j], haut[i]))
    centre = coque.verts.new((0.0, 0.0, 0.0))
    for i in range(SECTEURS):
        coque.faces.new((anneaux[0][(i + 1) % SECTEURS], anneaux[0][i], centre))
    bmesh.ops.recalc_face_normals(coque, faces=coque.faces)

    maillage = bpy.data.meshes.new("vase_torsade")
    coque.to_mesh(maillage)
    coque.free()
    for polygone in maillage.polygons:
        polygone.use_smooth = True
    vase = bpy.data.objects.new("vase_torsade", maillage)
    bpy.context.scene.collection.objects.link(vase)
    paroi = vase.modifiers.new("paroi", "SOLIDIFY")
    paroi.thickness, paroi.offset = EPAISSEUR, -1.0  # vers l'intérieur
    paroi.use_even_offset = True
    return vase
