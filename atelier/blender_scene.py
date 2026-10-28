"""Exécuté par Blender, pas par uv : construit une pièce `scene.py`, la mesure, l'exporte et la rend.

Appel : blender --background --factory-startup --python atelier/blender_scene.py -- <demande.json>

Ne dépend que de bpy, bmesh, mathutils et de la bibliothèque standard : le Python de Blender
n'a ni build123d ni Pillow. La demande et la réponse sont des fichiers JSON (voir
`atelier/blender.py`). Toute erreur se rend dans la réponse ; le code de sortie reste 0.
"""

import importlib.util
import json
import random
import sys
import traceback
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

VERSION_MIN = (4, 2, 0)  # wm.stl_export remplace l'ancien add-on STL
# Plus grand côté d'un rendu brut, en pixels : au-dessus de la taille de la zone de dessin finale.
RENDU_PX = 2000
# Le rendu déborde l'emprise de cette fraction de chaque côté : le contour n'y est pas rogné.
DEBORD = 0.005
GRIS_PIECE = (0.72, 0.74, 0.78)


def _vider_la_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    unites = bpy.context.scene.unit_settings
    # 1 unité Blender = 1 mm, ce que l'interface affiche aussi quand on ouvre le .blend.
    unites.system, unites.scale_length, unites.length_unit = "METRIC", 0.001, "MILLIMETERS"


def _charger(chemin: Path):
    racine = str(chemin.resolve().parents[2])
    if racine not in sys.path:
        sys.path.insert(0, racine)  # `from commun.jeux import ...` depuis une scène
    spec = importlib.util.spec_from_file_location(f"scene_{chemin.parent.name}", chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "construire", None)


def _maillage_monde(objet) -> bmesh.types.BMesh:
    """Le maillage tel qu'il s'exporte : modificateurs appliqués, en coordonnées du monde."""
    evalue = objet.evaluated_get(bpy.context.evaluated_depsgraph_get())
    maillage = bmesh.new()
    maillage.from_mesh(evalue.to_mesh())
    evalue.to_mesh_clear()
    maillage.transform(objet.matrix_world)
    if objet.matrix_world.determinant() < 0:
        # Un miroir (échelle négative) retourne les faces ; l'export STL les remet à l'endroit.
        bmesh.ops.reverse_faces(maillage, faces=maillage.faces)
    return maillage


def _parties(maillage: bmesh.types.BMesh) -> int:
    """Nombre de morceaux disjoints, comptés sur les sommets portés par des faces."""
    parent = {}

    def racine(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v

    for face in maillage.faces:
        for sommet in face.verts:
            parent.setdefault(sommet.index, sommet.index)
    for arete in maillage.edges:
        if arete.link_faces:
            a, b = (racine(v.index) for v in arete.verts)
            parent[a] = b
    return len({racine(v) for v in parent})


def _mesurer(objet) -> tuple[dict, bmesh.types.BMesh | None]:
    if objet.type != "MESH":
        return {"type": objet.type}, None
    maillage = _maillage_monde(objet)
    maillage.verts.index_update()
    coins = [v.co for v in maillage.verts] or [Vector()]
    mesures = {
        "type": "MESH",
        "faces": len(maillage.faces),
        "triangles": sum(len(f.verts) - 2 for f in maillage.faces),
        "parties": _parties(maillage),
        "aretes_non_manifold": sum(not a.is_manifold for a in maillage.edges),
        "aretes_normales_opposees": sum(a.is_manifold and not a.is_contiguous for a in maillage.edges),
        "volume": maillage.calc_volume(signed=True),
        "boite_min": [min(c[i] for c in coins) for i in range(3)],
        "boite_max": [max(c[i] for c in coins) for i in range(3)],
    }
    return mesures, maillage


def _imprimabilite(maillage: bmesh.types.BMesh, parametres: dict) -> dict:
    """Surplombs et épaisseurs, comme `atelier/imprimabilite.mesurer` (mêmes paramètres)."""
    triangles = [t for t in maillage.calc_loop_triangles()]
    coins = [[boucle.vert.co for boucle in t] for t in triangles]
    normales = [(b - a).cross(c - a) for a, b, c in coins]
    aires = [n.length / 2 for n in normales]
    bas = min(v.co.z for v in maillage.verts) + parametres["tolerance_plateau"]
    surface, hauteurs = 0.0, []
    for points, normale, aire in zip(coins, normales, aires):
        posee = all(p.z < bas for p in points)
        if aire > 1e-12 and not posee and normale.z / (2 * aire) < parametres["seuil_normale"]:
            surface += aire
            hauteurs.append(sum(p.z for p in points) / 3)

    arbre = BVHTree.FromBMesh(maillage)
    tirage = random.Random(0)
    epaisseurs = []
    for i in tirage.choices(range(len(triangles)), weights=aires, k=parametres["echantillons"]):
        a, b, c = coins[i]
        r1, r2 = tirage.random() ** 0.5, tirage.random()
        direction = -normales[i].normalized()
        depart = a * (1 - r1) + b * (r1 * (1 - r2)) + c * (r1 * r2) + direction * parametres["ecart_rayon"]
        impact, _, _, distance = arbre.ray_cast(depart, direction)
        if impact is not None:
            epaisseurs.append(distance + parametres["ecart_rayon"])
    return {
        "surplomb_mm2": surface,
        "surplomb_z": [min(hauteurs), max(hauteurs)] if hauteurs else None,
        "epaisseurs": epaisseurs,
    }


def _exporter(objet, stl: str, blend: str) -> int:
    """Exporte l'objet seul ; rend le nombre de triangles réellement écrits dans le STL."""
    objet.hide_set(False)
    objet.hide_viewport = False  # un objet masqué ne se sélectionne pas, et sortirait vide
    for autre in bpy.context.view_layer.objects:
        autre.select_set(autre == objet)
    bpy.context.view_layer.objects.active = objet
    bpy.ops.wm.stl_export(filepath=stl, export_selected_objects=True, apply_modifiers=True, check_existing=False)
    bpy.ops.wm.save_as_mainfile(filepath=blend, copy=True)
    with open(stl, "rb") as fichier:
        fichier.seek(80)
        return int.from_bytes(fichier.read(4), "little")  # STL binaire : en-tête de 80 octets


def _preparer_le_rendu(objet) -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "Standard"
    ombrage = scene.display.shading
    ombrage.light, ombrage.color_type, ombrage.single_color = "STUDIO", "SINGLE", GRIS_PIECE
    ombrage.show_cavity, ombrage.cavity_type = True, "BOTH"
    ombrage.show_object_outline, ombrage.object_outline_color = True, (0.0, 0.0, 0.0)
    for autre in scene.objects:
        autre.hide_render = autre != objet  # les outils de booléen ne se montrent pas


def _rendre(objet, maillage, vues: dict, dossier: Path) -> tuple[list[float], dict]:
    _preparer_le_rendu(objet)
    scene = bpy.context.scene
    coins = [v.co for v in maillage.verts]
    centre = Vector([(min(c[i] for c in coins) + max(c[i] for c in coins)) / 2 for i in range(3)])
    diagonale = max((max(c[i] for c in coins) - min(c[i] for c in coins)) for i in range(3)) * 2 + 1
    camera = bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = "ORTHO"
    camera.data.clip_start, camera.data.clip_end = 0.1, diagonale * 30
    rendus = {}
    for nom, (direction, haut) in vues.items():
        regard = Vector(direction).normalized()  # du centre vers la caméra
        dessus = (Vector(haut) - regard * Vector(haut).dot(regard)).normalized()
        droite = (-regard).cross(dessus)
        xs = [(c - centre).dot(droite) for c in coins]
        ys = [(c - centre).dot(dessus) for c in coins]
        emprise = [min(xs), max(xs), min(ys), max(ys)]
        largeur, hauteur = max(emprise[1] - emprise[0], 1e-6), max(emprise[3] - emprise[2], 1e-6)
        debord = DEBORD * max(largeur, hauteur)
        cadrage = [emprise[0] - debord, emprise[1] + debord, emprise[2] - debord, emprise[3] + debord]
        largeur, hauteur = cadrage[1] - cadrage[0], cadrage[3] - cadrage[2]
        milieu = centre + droite * (cadrage[0] + cadrage[1]) / 2 + dessus * (cadrage[2] + cadrage[3]) / 2
        camera.matrix_world = Matrix.Translation(milieu + regard * diagonale * 10) @ Matrix(
            [droite, dessus, regard]
        ).transposed().to_4x4()
        camera.data.ortho_scale = max(largeur, hauteur)
        plus_grand = max(largeur, hauteur)
        scene.render.resolution_x = max(1, round(RENDU_PX * largeur / plus_grand))
        scene.render.resolution_y = max(1, round(RENDU_PX * hauteur / plus_grand))
        scene.render.resolution_percentage = 100
        scene.render.filepath = str(dossier / f"{nom}.png")
        bpy.ops.render.render(write_still=True)
        rendus[nom] = {"fichier": scene.render.filepath, "emprise": emprise, "cadrage": cadrage}
    return list(centre), rendus


def traiter(demande: dict) -> dict:
    if bpy.app.version < VERSION_MIN:
        return {"erreur_usage": f"Blender {bpy.app.version_string} trop ancien : {'.'.join(map(str, VERSION_MIN))} au moins"}
    _vider_la_scene()
    chemin = Path(demande["scene"])
    try:
        construire = _charger(chemin)
        if not callable(construire):
            return {"erreur_usage": f"{chemin} doit exposer une fonction construire() qui rend un objet maillé"}
        objet = construire()
    except Exception:
        return {"erreur": traceback.format_exc()}
    if not isinstance(objet, bpy.types.Object):
        return {"mesures": {"type": type(objet).__name__}}
    if objet.name not in bpy.context.scene.objects:
        bpy.context.scene.collection.objects.link(objet)
    mesures, maillage = _mesurer(objet)
    reponse = {"mesures": mesures}
    if maillage is None:
        return reponse
    if maillage.faces and "imprimabilite" in demande:
        try:
            mesures["imprimabilite"] = _imprimabilite(maillage, demande["imprimabilite"])
        except Exception as erreur:
            reponse["erreur_imprimabilite"] = f"{type(erreur).__name__} : {erreur}"
    if maillage.verts:
        # Un rendu impossible (pas d'OpenGL) n'empêche pas la pièce de sortir.
        try:
            reponse["centre"], reponse["rendus"] = _rendre(objet, maillage, demande["vues"], Path(demande["rendus"]))
        except Exception as erreur:
            reponse["erreur_rendu"] = f"{type(erreur).__name__} : {erreur}"
    try:
        mesures["triangles_stl"] = _exporter(objet, demande["stl"], demande["blend"])
    except Exception as erreur:
        mesures["erreur_export"] = f"{type(erreur).__name__} : {erreur}"
    return reponse


def main() -> None:
    demande_json = Path(sys.argv[sys.argv.index("--") + 1])
    demande = json.loads(demande_json.read_text(encoding="utf-8"))
    try:
        reponse = traiter(demande)
    except Exception:
        reponse = {"erreur": traceback.format_exc()}
    Path(demande["reponse"]).write_text(json.dumps(reponse), encoding="utf-8")


if __name__ == "__main__":
    main()
