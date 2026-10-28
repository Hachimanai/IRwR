"""Kit « Yet another Spice Rack V2 » (Johann Arndt, MakerWorld) lu dans son projet Bambu Studio.

Partagé par `range_epice_gauche` et `range_epice_droite` (filière Blender) : ce dossier n'est
pas une pièce, il porte le `.3mf` du créateur (non versionné : `.gitignore`, et la licence
Standard Digital File License interdit d'en redistribuer le maillage) et cette lecture.

Les modules sont des colonnes de pots, repère du créateur : X le long des colonnes, Y de
l'avant (bras, Y < 0) vers le dos (Y > 0), Z le long des rangées. Ils s'emboîtent en X par une
queue d'aronde. Bibliothèque standard seulement : tourne dans le Python de Blender.
"""

import math
import re
import zipfile
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix

PROJET = Path(__file__).with_name("ModularParts.3mf")

# Entraxes d'emboîtement, contact des flancs (mesurés sur les maillages : recouvrement nul,
# et la queue d'aronde accroche dès qu'on écarte de 0,1 mm).
ENTRAXE_GAUCHE_MILIEU = 52.9
ENTRAXE_MILIEU_MILIEU = 52.55
ENTRAXE_MILIEU_DROITE = 54.4
# Recouvrement imposé entre deux modules fusionnés : les flancs se touchent à plat, une union
# de faces coplanaires est fragile ; 0,1 mm d'interpénétration la rend franche.
FUSION = 0.1
PROFONDEUR = 97.0  # Y du kit, bras compris : la hauteur d'impression
PIED = -99.6  # Z du kit sous les modules 4 rangées (le haut est à +99,6)
# Demi-largeurs des modules, du centre au plan de flanc (faces planes relevées sur les maillages)
FLANC_GAUCHE = {"Left": 28.12, "Middle": 24.75, "Right": 26.62}
FLANC_DROIT = {"Left": 28.12, "Middle": 27.75, "Right": 29.62}
# Glissière : rails et rainures suivent la pente des tablettes. Seul chemin libre (relevé sur
# les maillages, ±0,5° cogne déjà) : le module de droite sort vers l'arrière et le bas à 15°,
# ses rails ressortant par le dos et le dessous de la rainure de son voisin de gauche.
SORTIE = math.radians(15.0)
COURSE = 150.0  # longueur balayée par les rails pour sortir du bloc, avec de la marge
JEU_PASSAGE = 0.3  # autour du passage des rails percé dans le fond et le dos
HAUT_RAILS = 88.0  # Z du kit où finit le plus haut rail
# Pilier sous le bout libre du dessus (côté joint, à l'avant) : profondeur en Y, et pied
# au-dessus du rail le plus haut pour ne pas gêner la glissière.
PILIER = 8.0
BAS_PILIER = HAUT_RAILS + 1.0
# Dessous de la tablette du bas, au bord avant (Z du kit, relevé sur les trois modules) : la
# plaque avant du bas monte jusque-là et ferme l'interstice entre le fond et cette tablette.
SOUS_TABLETTE_BAS = -75.5


def _sommets_triangles(xml: str) -> tuple[list, list]:
    sommets = [tuple(map(float, m)) for m in re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', xml)]
    triangles = [tuple(map(int, m)) for m in re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', xml)]
    return sommets, triangles


def _chemins_par_nom(archive: zipfile.ZipFile) -> dict[str, str]:
    """`Middle_4x1` → `3D/Objects/object_8.model`, par les réglages puis le modèle racine."""
    reglages = archive.read("Metadata/model_settings.config").decode()
    noms = {
        ident: nom.removesuffix(".stl")
        for ident, nom in re.findall(r'<object id="(\d+)">\s*<metadata key="name" value="([^"]+)"', reglages)
    }
    racine = archive.read("3D/3dmodel.model").decode()
    chemins = re.findall(r'<object id="(\d+)"[^>]*>\s*<components>\s*<component p:path="/([^"]+)"', racine)
    return {noms[ident]: chemin for ident, chemin in chemins if ident in noms}


def _maillage(nom: str) -> tuple[list, list]:
    if not PROJET.is_file():
        raise FileNotFoundError(f"{PROJET} manque : le projet du créateur n'est pas versionné, le poser là")
    with zipfile.ZipFile(PROJET) as archive:
        return _sommets_triangles(archive.read(_chemins_par_nom(archive)[nom]).decode())


def module(nom: str, decalage_x: float) -> bpy.types.Object:
    """Le module `nom` du kit (`Left_4x1`, `Middle_4x1`…), décalé de `decalage_x` le long des colonnes."""
    sommets, triangles = _maillage(nom)
    maillage = bmesh.new()
    verts = [maillage.verts.new((x + decalage_x, y, z)) for x, y, z in sommets]
    for a, b, c in triangles:
        maillage.faces.new((verts[a], verts[b], verts[c]))
    donnees = bpy.data.meshes.new(nom)
    maillage.to_mesh(donnees)
    maillage.free()
    objet = bpy.data.objects.new(nom, donnees)
    bpy.context.scene.collection.objects.link(objet)
    return objet


def pave(nom: str, x: tuple[float, float], y: tuple[float, float], z: tuple[float, float]) -> bpy.types.Object:
    """Un pavé plein entre les bornes données, dans le repère du kit."""
    maillage = bmesh.new()
    bmesh.ops.create_cube(maillage, size=1.0)
    for v in maillage.verts:
        v.co = [(b0 + b1) / 2 + c * (b1 - b0) for c, (b0, b1) in zip(v.co, (x, y, z))]
    donnees = bpy.data.meshes.new(nom)
    maillage.to_mesh(donnees)
    maillage.free()
    objet = bpy.data.objects.new(nom, donnees)
    bpy.context.scene.collection.objects.link(objet)
    return objet


def _rails(nom: str) -> tuple[float, list[list[tuple]]]:
    """Le plan du flanc gauche du module `nom` et les sommets de chacun de ses rails, qui en dépassent."""
    plan = -FLANC_GAUCHE[nom.split("_")[0]]
    rails = sorted((p for p in _maillage(nom)[0] if p[0] < plan - 0.05), key=lambda p: p[2])
    groupes = [[rails[0]]]
    for precedent, p in zip(rails, rails[1:]):
        if p[2] - precedent[2] > 3.0:  # rails superposés : plusieurs mm de vide entre deux
            groupes.append([])
        groupes[-1].append(p)
    return plan, groupes


def _enveloppe(nom: str, points: list[tuple]) -> bpy.types.Object:
    """L'enveloppe convexe des points, en outil de booléen caché."""
    maillage = bmesh.new()
    for p in points:
        maillage.verts.new(p)
    enveloppe = bmesh.ops.convex_hull(maillage, input=maillage.verts)
    bmesh.ops.delete(maillage, geom=list(set(enveloppe["geom_interior"] + enveloppe["geom_unused"])), context="VERTS")
    donnees = bpy.data.meshes.new(nom)
    maillage.to_mesh(donnees)
    maillage.free()
    objet = bpy.data.objects.new(nom, donnees)
    bpy.context.scene.collection.objects.link(objet)
    objet.hide_render = objet.hide_viewport = True
    return objet


def passage_rails(nom: str, decalage_x: float) -> tuple[bpy.types.Object, ...]:
    """Le volume balayé par chaque rail du flanc gauche du module `nom` sur le chemin de sortie.

    Un pavé par rail : l'enveloppe convexe du rail (élargie de `JEU_PASSAGE`, et au-delà du plan
    de flanc) et de sa copie décalée de `COURSE` vers l'arrière et le bas. Retranché du fond et
    du dos du bloc voisin, il y laisse passer les rails sans ouvrir toute la bande de la rainure.
    """
    plan, groupes = _rails(nom)
    sortie = (0.0, COURSE * math.cos(SORTIE), -COURSE * math.sin(SORTIE))
    j = JEU_PASSAGE
    return tuple(
        _enveloppe(
            f"passage_rail_{i}",
            [
                (px + decalage_x + d[0], y + dy + d[1], z + dz + d[2])
                for x, y, z in groupe
                for px in (x - j, plan + 0.5)
                for dy in (-j, j)
                for dz in (-j, j)
                for d in ((0.0, 0.0, 0.0), sortie)
            ],
        )
        for i, groupe in enumerate(groupes)
    )


def _tranches_rails(nom: str, groupes: list[list[tuple]], plan: float, decalage_x: float, semelle: float):
    """Un pavé par rail, orienté le long du chemin de glissement : le rail et une semelle de flanc.

    Symétrique autour du milieu du rail, pour qu'on puisse retourner le rail bout pour bout sans
    que sa semelle sorte de la zone où elle était.
    """
    d = (math.cos(SORTIE), -math.sin(SORTIE))  # le long du chemin, dans (Y, Z)
    q = (math.sin(SORTIE), math.cos(SORTIE))  # en travers, dans le plan du flanc
    maillage = bmesh.new()
    for groupe in groupes:
        a = [y * d[0] + z * d[1] for _, y, z in groupe]
        b = [y * q[0] + z * q[1] for _, y, z in groupe]
        ca, cb = (min(a) + max(a)) / 2, (min(b) + max(b)) / 2
        la, lb, lx = max(a) - min(a) + 1.2, max(b) - min(b) + 1.6, 5.0 + semelle
        cx = plan + semelle - lx / 2
        centre = (cx + decalage_x, ca * d[0] + cb * q[0], ca * d[1] + cb * q[1])
        matrice = Matrix(
            (
                (lx, 0.0, 0.0, centre[0]),
                (0.0, la * d[0], lb * q[0], centre[1]),
                (0.0, la * d[1], lb * q[1], centre[2]),
                (0.0, 0.0, 0.0, 1.0),
            )
        )
        bmesh.ops.create_cube(maillage, size=1.0, matrix=matrice)
    donnees = bpy.data.meshes.new(nom)
    maillage.to_mesh(donnees)
    maillage.free()
    objet = bpy.data.objects.new(nom, donnees)
    bpy.context.scene.collection.objects.link(objet)
    return objet


def _retourner_rails(objet: bpy.types.Object, plan: float) -> bpy.types.Object:
    """Applique les booléens de `objet`, puis retourne chaque rail bout pour bout le long du chemin.

    Symétrie par le plan ⟂ au chemin qui passe au milieu du rail (repéré sur ce qui dépasse du
    flanc) : la section est symétrique, seules les extrémités s'échangent.
    """
    objet.hide_viewport = False  # Blender n'évalue pas les modificateurs d'un objet masqué
    evalue = objet.evaluated_get(bpy.context.evaluated_depsgraph_get())
    maillage = bmesh.new()
    maillage.from_mesh(evalue.to_mesh())
    evalue.to_mesh_clear()
    maillage.transform(objet.matrix_world)  # la copie porteuse est décalée de `jeu` en X
    objet.hide_viewport = True
    d = (math.cos(SORTIE), -math.sin(SORTIE))
    restantes = set(maillage.verts)
    while restantes:
        rail, pile = set(), [restantes.pop()]
        while pile:
            v = pile.pop()
            rail.add(v)
            voisins = [arete.other_vert(v) for arete in v.link_edges]
            pile += [w for w in voisins if w in restantes]
            restantes.difference_update(voisins)
        a = [v.co.y * d[0] + v.co.z * d[1] for v in rail if v.co.x < plan - 0.01]
        milieu = (min(a) + max(a)) / 2
        for v in rail:
            ecart = 2 * (milieu - (v.co.y * d[0] + v.co.z * d[1]))
            v.co.y += ecart * d[0]
            v.co.z += ecart * d[1]
    bmesh.ops.reverse_faces(maillage, faces=maillage.faces)  # une symétrie retourne les normales
    donnees = bpy.data.meshes.new(f"{objet.name}_retournes")
    maillage.to_mesh(donnees)
    maillage.free()
    retournes = bpy.data.objects.new(donnees.name, donnees)
    bpy.context.scene.collection.objects.link(retournes)
    retournes.hide_render = retournes.hide_viewport = True
    return retournes


def rails_amincis(nom: str, decalage_x: float, jeu: float) -> tuple[bpy.types.Object, tuple[bpy.types.Object, ...]]:
    """De quoi amincir de `jeu` les rails du flanc gauche du module `nom`, et les retourner : (retrait, rails).

    Le retrait, un pavé à retrancher, ôte les rails d'origine (tout ce qui dépasse du plan de
    flanc). Les rails amincis sont l'intersection de quatre copies des rails d'origine, pris avec
    une semelle de 0,5 mm de flanc, décalées de ±`jeu` en X et de ±`jeu` perpendiculairement au
    chemin de glissement dans le plan du flanc : chaque face recule de `jeu`, y compris le
    dessous de la tête de la queue d'aronde (le col est plus étroit que la tête, l'enveloppe
    convexe ne convient pas).

    Puis chaque rail est retourné bout pour bout (`_retourner_rails`) : dans le kit, la longue
    pente d'entrée (≈ 3 mm) est au bout arrière-bas et le bout avant-haut n'a qu'un chanfrein de
    0,5 mm, alors que c'est le bout avant-haut qui attaque la rainure sur le seul chemin de
    montage.
    """
    plan_kit, groupes = _rails(nom)
    plan = plan_kit + decalage_x
    semelle = 0.5
    largeur = (0.0, math.sin(SORTIE), math.cos(SORTIE))  # dans le plan du flanc, ⟂ au chemin
    decalages = [(jeu, 0.0, 0.0), (-jeu, 0.0, 0.0), tuple(jeu * c for c in largeur), tuple(-jeu * c for c in largeur)]
    copies = []
    for k, d in enumerate(decalages):
        copie = module(nom, decalage_x)
        copie.name = f"rails_{k}"
        tranche = _tranches_rails(f"tranche_rails_{k}", groupes, plan_kit, decalage_x, semelle)
        commun = copie.modifiers.new(tranche.name, "BOOLEAN")
        commun.operation, commun.solver, commun.object = "INTERSECT", "MANIFOLD", tranche
        for outil in (copie, tranche):
            outil.matrix_world = Matrix.Translation(d)
            outil.hide_render = outil.hide_viewport = True
        copies.append(copie)
    for copie in copies[1:]:
        commun = copies[0].modifiers.new(copie.name, "BOOLEAN")
        commun.operation, commun.solver, commun.object = "INTERSECT", "MANIFOLD", copie
    retrait = pave("rails_origine", (plan - 5.0, plan), (-PROFONDEUR, PROFONDEUR), (2 * PIED, -2 * PIED))
    retrait.hide_render = retrait.hide_viewport = True
    return retrait, (_retourner_rails(copies[0], plan),)


def _boucher_cavites(objet: bpy.types.Object) -> None:
    """Applique les unions puis retire les coques de volume négatif : les cavités fermées deviennent pleines.

    Entre deux modules fusionnés, la fente de la glissière est ouverte au dos et en bas ; le dos
    et le fond de la boîte la referment en une bulle d'air que `generer` compte comme une partie.
    """
    evalue = objet.evaluated_get(bpy.context.evaluated_depsgraph_get())
    maillage = bmesh.new()
    maillage.from_mesh(evalue.to_mesh())
    evalue.to_mesh_clear()
    objet.modifiers.clear()
    restantes = set(maillage.faces)
    while restantes:
        coque, pile = set(), [restantes.pop()]
        while pile:
            face = pile.pop()
            coque.add(face)
            for arete in face.edges:
                pile += [f for f in arete.link_faces if f in restantes]
                restantes.difference_update(arete.link_faces)
        volume = sum(
            f.verts[0].co.dot(a.co.cross(b.co)) for f in coque for a, b in zip(f.verts[1:-1], f.verts[2:])
        )
        if volume < 0:
            bmesh.ops.delete(maillage, geom=list(coque), context="FACES")
    maillage.to_mesh(objet.data)
    maillage.free()


def bloc(
    nom: str,
    modules: list[tuple[str, float]],
    paves: tuple[bpy.types.Object, ...] = (),
    retraits: tuple[bpy.types.Object, ...] = (),
) -> bpy.types.Object:
    """Fusionne les modules (nom, décalage X) et les `paves` en un objet posé sur le dos de sa boîte.

    Les `retraits` sont d'abord retranchés du premier module. Le premier module porte l'objet
    rendu, les autres, les pavés et les retraits sont des outils de booléen (ni exportés ni
    rendus). Rotation de -90° autour de X : le dos (Y = PROFONDEUR/2), fermé par la
    boîte, descend sur Z = 0 et les bras montent vers l'avant ouvert. Le créateur, sans boîte,
    pose l'avant sur le plateau ; ici le dos serait alors imprimé en pont.
    """
    porteur, *outils = (module(n, x) for n, x in modules)
    outils += paves
    porteur.name = porteur.data.name = nom
    for retrait in retraits:
        moins = porteur.modifiers.new(retrait.name, "BOOLEAN")
        moins.operation, moins.solver, moins.object = "DIFFERENCE", "MANIFOLD", retrait
    for outil in outils:
        union = porteur.modifiers.new(outil.name, "BOOLEAN")
        union.operation, union.solver, union.object = "UNION", "MANIFOLD", outil
        outil.hide_render = outil.hide_viewport = True
    _boucher_cavites(porteur)
    pose = Matrix.Translation((0.0, 0.0, PROFONDEUR / 2)) @ Matrix.Rotation(math.radians(-90), 4, "X")
    for objet in (porteur, *outils, *retraits):
        objet.matrix_world = pose
    return porteur


def boite(
    x: tuple[float, float],
    fermer_gauche: bool,
    fermer_droite: bool,
    haut: float,
    paroi: float,
    passages: tuple[bpy.types.Object, ...] = (),
) -> tuple[bpy.types.Object, ...]:
    """Les pavés d'une boîte ouverte sur l'avant autour d'un bloc couvrant `x` (repère du kit).

    Fond, dos et dessus sur toute la largeur, plaque avant sous la tablette du bas ; un côté
    plein sur toute la hauteur là où le bloc finit le range-épices (`fermer_gauche`, `fermer_droite`) ; côté joint entre blocs, un seul
    pilier sous l'avant du dessus, dans l'épaisseur du flanc. Tout tient dans l'emprise du bloc,
    sauf le dessus, qui monte jusqu'à `haut`. Les `passages` (voir `passage_rails`) sont percés
    dans le fond et le dos : les rails du voisin y passent pour s'emboîter.
    """
    (x0, x1), y, z = x, (-PROFONDEUR / 2, PROFONDEUR / 2), (PIED, haut)
    paves = [
        pave("fond", x, y, (PIED, PIED + paroi)),
        pave("dos", x, (y[1] - paroi, y[1]), z),
        pave("dessus", x, y, (haut - paroi, haut)),
        pave("devant_bas", x, (y[0], y[0] + paroi), (PIED, SOUS_TABLETTE_BAS)),
    ]
    for cote, plein, bornes in (("gauche", fermer_gauche, (x0, x0 + paroi)), ("droite", fermer_droite, (x1 - paroi, x1))):
        if plein:
            paves.append(pave(f"cote_{cote}", bornes, y, z))
        else:
            paves.append(pave(f"pilier_{cote}", bornes, (y[0], y[0] + PILIER), (BAS_PILIER, haut)))
    for panneau in paves[:2]:  # fond et dos
        for passage in passages:
            percage = panneau.modifiers.new(passage.name, "BOOLEAN")
            percage.operation, percage.solver, percage.object = "DIFFERENCE", "MANIFOLD", passage
    return tuple(paves)
