"""Rafale M (Marine) à 1/72, en vol, train rentré : maquette d'exposition en une pièce.

Les volumes (fuselage, verrière et épine dorsale, entrées d'air, ailes delta, canards, dérive,
tuyères, rails de bout d'aile, perche de ravitaillement, crosse d'appontage) se construisent
par sections lissées, puis se fusionnent par booléens. Les entrées d'air, les tuyères et les
lignes de panneaux sont creusées ; le ventre est aplati pour poser sur le plateau.

Les cotes sont celles de l'avion réel, en mètres, comptées depuis la pointe du nez (x vers
l'arrière, y vers tribord, z vers le haut) : `_p()` les passe à l'échelle et dans le repère de
la pièce (nez vers +X, ventre aplati sur Z = 0). Silhouette approchée, pas un relevé de plans.
"""

import math

import bmesh
import bpy
from mathutils import Vector

ECHELLE = 72
MM = 1000 / ECHELLE  # millimètres de maquette par mètre réel
LONGUEUR = 15.27  # m, nez à tuyères

# Ventre aplati : coupe 1 mm (0,072 m réel) au-dessus du point le plus bas des entrées d'air.
Z_COUPE = -0.71

# Détails à la buse de 0,2 mm : rien de plus fin que deux largeurs de buse.
EPAISSEUR_MIN = 0.45  # mm, bord de fuite des ailes, canards et dérive
GRAVURE_LARGEUR = 0.30  # mm, lignes de panneaux
GRAVURE_PROFONDEUR = 0.15  # mm
JEU_GRAVURE = 0.05  # mm : la lame déborde la peau, pour qu'aucune face ne coïncide

TOUR = 64  # points par section de fuselage
CORDE = 28  # points par extrados (et autant par intrados) d'un profil

# Fuselage : x, demi-largeur, dessus, dessous, exposant de la superellipse (2 rond, 3 carré).
FUSELAGE = [
    (0.00, 0.02, 0.00, -0.06, 2.0),
    (0.15, 0.13, 0.08, -0.16, 2.0),
    (0.50, 0.28, 0.18, -0.30, 2.0),
    (1.20, 0.45, 0.33, -0.45, 2.1),
    (2.20, 0.58, 0.45, -0.58, 2.3),
    (3.20, 0.65, 0.52, -0.66, 2.5),
    (4.50, 0.70, 0.58, -0.70, 2.7),
    (6.00, 0.72, 0.62, -0.70, 2.8),
    (7.50, 0.80, 0.65, -0.72, 3.0),
    (9.00, 0.95, 0.62, -0.75, 3.0),
    (11.00, 1.00, 0.58, -0.72, 3.0),
    (12.50, 0.98, 0.52, -0.66, 3.0),
    (13.80, 0.95, 0.45, -0.55, 3.0),
    (14.60, 0.90, 0.35, -0.45, 3.0),
]

# Verrière puis épine dorsale : x, demi-largeur, dessus (le dessous plonge dans le fuselage).
VERRIERE = [
    (3.00, 0.15, 0.40),
    (3.40, 0.28, 0.58),
    (3.80, 0.45, 0.80),
    (4.50, 0.55, 0.98),
    (5.30, 0.56, 1.02),
    (6.10, 0.52, 0.95),
    (7.00, 0.55, 0.86),
    (8.50, 0.68, 0.78),
    (10.00, 0.74, 0.72),
    (11.50, 0.72, 0.67),
    (13.00, 0.62, 0.59),
    (14.20, 0.45, 0.46),
]
VERRIERE_DESSOUS = 0.15

# Entrées d'air (de chaque côté) : x, centre y, centre z, demi-largeur, demi-hauteur.
ENTREE_AIR = [
    (6.30, 0.92, -0.38, 0.38, 0.40),
    (8.00, 0.90, -0.36, 0.36, 0.38),
    (10.50, 0.75, -0.30, 0.25, 0.30),
    (11.80, 0.62, -0.26, 0.18, 0.22),  # se fond dans le fuselage, sans marche
]
ENTREE_AIR_PROFONDEUR = 1.5  # m, conduit creusé depuis la lèvre
ENTREE_AIR_LEVRE = 0.06  # m, épaisseur de la lèvre

# Aile delta : bord d'attaque à 48°, bord de fuite droit.
AILE_Z = -0.30
AILE_EMPLANTURE = 0.30  # y de la section d'emplanture, noyée dans le fuselage
AILE_FLANC = 0.90  # y où le bord d'attaque sort du fuselage
AILE_ATTAQUE = 7.60  # x du bord d'attaque au flanc
AILE_FUITE = 14.30
AILE_FLECHE = math.radians(48)
AILE_DEMI_ENVERGURE = 5.30
AILE_EPAISSEUR = (0.045, 0.035)  # épaisseur relative, emplanture puis saumon

# Canards : plans canard proches, posés sur les entrées d'air.
CANARD_Z = 0.05
CANARD_FLANC = 0.85
CANARD_ATTAQUE = 6.30
CANARD_FUITE = 8.00
CANARD_FLECHE = math.radians(50)
CANARD_FLECHE_FUITE = 0.30  # recul du bord de fuite par mètre d'envergure
CANARD_DEMI_ENVERGURE = 2.15
CANARD_EPAISSEUR = 0.05

# Dérive.
DERIVE_PIED = 0.40  # z de la section de pied, noyée dans l'épine
DERIVE_BASE = 0.60
DERIVE_SOMMET = 2.65
DERIVE_ATTAQUE = 10.60
DERIVE_FUITE = 14.40
DERIVE_FLECHE = math.radians(52)
DERIVE_EPAISSEUR = (0.055, 0.040)

# Tuyères : deux, côte à côte.
TUYERE_Y = 0.50
TUYERE_Z = -0.12
TUYERE = [(13.90, 0.47), (LONGUEUR, 0.42)]  # x, rayon
TUYERE_CREUX = (0.34, 0.65)  # rayon, profondeur

# Rails lance-missiles de bout d'aile.
RAIL_Y = 5.33
RAIL_RAYON = 0.075
RAIL = (11.40, 14.50)

# Perche de ravitaillement fixe, à tribord devant le pare-brise.
PERCHE = [(2.30, 0.02, 0.50), (2.40, 0.08, 0.49), (2.60, 0.06, 0.48), (4.80, 0.06, 0.40)]  # x, rayon, z
PERCHE_Y = 0.50

# Crosse d'appontage, plaquée sous l'arrière du fuselage.
CROSSE = (12.40, 14.70, 0.06, -0.82, -0.62)  # x début, x fin, demi-largeur, z bas, z haut

# Lignes de panneaux (gravées) : stations en x pour les anneaux du fuselage et de la verrière.
ANNEAUX_FUSELAGE = (2.60, 9.00, 11.50, 13.20)  # 2,60 : jonction du radôme
ANNEAUX_VERRIERE = (4.00, 6.45)  # arceau du pare-brise, arrière de la verrière
GOUVERNE_AILE = 13.45  # x de la charnière des élevons
SEPARATION_ELEVONS = 3.10  # y, entre élevon intérieur et extérieur
ELEVONS_RETRAIT_FUITE = 0.20  # m : la séparation s'arrête avant le bord de fuite, trop mince
BEC = 0.55  # m en arrière du bord d'attaque : ligne des becs
BEC_ENVERGURE = (1.30, 5.00)  # y de début et de fin de la ligne des becs
GOUVERNE_DERIVE = 13.60  # x de la charnière de la gouverne de direction


def _p(x: float, y: float, z: float) -> Vector:
    """Coordonnées avion (m) vers coordonnées pièce (mm) : rotation de 180° autour de Z."""
    return Vector(((LONGUEUR / 2 - x) * MM, -y * MM, (z - Z_COUPE) * MM))


def _hermite(table, colonne: int, x: float) -> float:
    """Interpolation cubique lisse d'une colonne de `table` (abscisse en colonne 0)."""
    xs = [ligne[0] for ligne in table]
    vs = [ligne[colonne] for ligne in table]
    i = max(0, min(len(xs) - 2, next((k for k in range(len(xs) - 1) if x <= xs[k + 1]), len(xs) - 2)))

    def pente(k):
        a, b = max(0, k - 1), min(len(xs) - 1, k + 1)
        return (vs[b] - vs[a]) / (xs[b] - xs[a])

    h = xs[i + 1] - xs[i]
    t = (x - xs[i]) / h
    h00, h10, h01, h11 = 2 * t**3 - 3 * t**2 + 1, t**3 - 2 * t**2 + t, -2 * t**3 + 3 * t**2, t**3 - t**2
    return h00 * vs[i] + h10 * h * pente(i) + h01 * vs[i + 1] + h11 * h * pente(i + 1)


def _superellipse(x, yc, zc, demi_largeur, dessus, dessous, exposant, points=TOUR):
    section = []
    for k in range(points):
        t = 2 * math.pi * k / points
        c, s = math.cos(t), math.sin(t)
        y = yc + demi_largeur * math.copysign(abs(c) ** (2 / exposant), c)
        z = zc + (dessus if s >= 0 else dessous) * math.copysign(abs(s) ** (2 / exposant), s)
        section.append((x, y, z))
    return section


def _profil(attaque: float, corde: float, epaisseur_relative: float, retrait: float = 0.0):
    """Profil symétrique NACA 4 chiffres fermé : (abscisse, demi-épaisseur), en m.

    `retrait` (m) amincit le profil de chaque côté : le volume intérieur d'une gravure.
    """
    demi_min = EPAISSEUR_MIN / 2 / MM - retrait
    dessus = []
    for k in range(CORDE + 1):
        u = (1 - math.cos(math.pi * k / CORDE)) / 2
        demi = 5 * epaisseur_relative * corde * (
            0.2969 * math.sqrt(u) - 0.1260 * u - 0.3516 * u**2 + 0.2843 * u**3 - 0.1036 * u**4
        )
        dessus.append((attaque + corde * u, max(demi - retrait, demi_min)))
    return dessus + [(a, -d) for a, d in reversed(dessus)]


def _objet(nom: str, sections) -> bpy.types.Object:
    """Un volume fermé tendu sur des sections de même nombre de points, bouché aux deux bouts."""
    maillage = bmesh.new()
    anneaux = [[maillage.verts.new(_p(*point)) for point in section] for section in sections]
    n = len(anneaux[0])
    for a, b in zip(anneaux, anneaux[1:]):
        for i in range(n):
            j = (i + 1) % n
            maillage.faces.new((a[i], a[j], b[j], b[i]))
    maillage.faces.new(list(reversed(anneaux[0])))
    maillage.faces.new(anneaux[-1])
    bmesh.ops.recalc_face_normals(maillage, faces=maillage.faces)
    donnees = bpy.data.meshes.new(nom)
    maillage.to_mesh(donnees)
    maillage.free()
    for polygone in donnees.polygons:
        polygone.use_smooth = True
    objet = bpy.data.objects.new(nom, donnees)
    bpy.context.scene.collection.objects.link(objet)
    return objet


def _stations(debut: float, fin: float, pas: float) -> list[float]:
    n = max(2, math.ceil((fin - debut) / pas))
    return [debut + (fin - debut) * k / n for k in range(n + 1)]


def _fuselage(retrait: float = 0.0, nom: str = "fuselage"):
    xs = [0.0, 0.03, 0.07, 0.15, 0.3] + _stations(0.5, FUSELAGE[-1][0], 0.15)
    sections = []
    for x in xs:
        largeur, dessus, dessous, exposant = (_hermite(FUSELAGE, c, x) for c in range(1, 5))
        zc, demi = (dessus + dessous) / 2, (dessus - dessous) / 2
        sections.append(_superellipse(x, 0.0, zc, largeur - retrait, demi - retrait, demi - retrait, exposant))
    return _objet(nom, sections)


def _verriere(retrait: float = 0.0, nom: str = "verriere"):
    sections = []
    for x in _stations(VERRIERE[0][0], VERRIERE[-1][0], 0.12):
        largeur, dessus = _hermite(VERRIERE, 1, x), _hermite(VERRIERE, 2, x)
        zc = VERRIERE_DESSOUS
        sections.append(_superellipse(x, 0.0, zc, largeur - retrait, dessus - zc - retrait, dessus - zc - retrait, 2.2, 48))
    return _objet(nom, sections)


def _cote(cote: int) -> str:
    return "tribord" if cote > 0 else "babord"


def _entree_air(cote: int, retrait: float = 0.0, nom: str = ""):
    sections = []
    for x in _stations(ENTREE_AIR[0][0], ENTREE_AIR[-1][0], 0.15):
        yc, zc, largeur, hauteur = (_hermite(ENTREE_AIR, c, x) for c in range(1, 5))
        sections.append(_superellipse(x, cote * yc, zc, largeur - retrait, hauteur - retrait, hauteur - retrait, 3.0, 40))
    return _objet(nom or f"entree_air_{_cote(cote)}", sections)


def _creux_entree_air(cote: int):
    """Conduit creusé depuis la lèvre, en laissant ENTREE_AIR_LEVRE de paroi."""
    sections = []
    for x in _stations(ENTREE_AIR[0][0] - 0.1, ENTREE_AIR[0][0] + ENTREE_AIR_PROFONDEUR, 0.15):
        xc = max(x, ENTREE_AIR[0][0])
        yc, zc, largeur, hauteur = (_hermite(ENTREE_AIR, c, xc) for c in range(1, 5))
        r = ENTREE_AIR_LEVRE
        sections.append(_superellipse(x, cote * yc, zc, largeur - r, hauteur - r, hauteur - r, 3.0, 40))
    return _objet(f"creux_entree_air_{_cote(cote)}", sections)


def _surface(nom, envergures, attaque, fuite, epaisseur, plan, retrait=0.0):
    """Surface portante : `plan(position, abscisse, demi_epaisseur)` place un point du profil."""
    sections = []
    for i, e in enumerate(envergures):
        t = i / (len(envergures) - 1)
        relative = epaisseur[0] + (epaisseur[1] - epaisseur[0]) * t if isinstance(epaisseur, tuple) else epaisseur
        a, f = attaque(e), fuite(e)
        sections.append([plan(e, x, d) for x, d in _profil(a, f - a, relative, retrait)])
    return _objet(nom, sections)


def _aile(cote: int, retrait: float = 0.0, nom: str = ""):
    def attaque(y):
        return AILE_ATTAQUE + max(0.0, y - AILE_FLANC) * math.tan(AILE_FLECHE)

    envergures = [AILE_EMPLANTURE] + _stations(AILE_FLANC, AILE_DEMI_ENVERGURE, 0.4)
    return _surface(
        nom or f"aile_{_cote(cote)}", envergures, attaque, lambda y: AILE_FUITE,
        AILE_EPAISSEUR, lambda y, x, d: (x, cote * y, AILE_Z + d), retrait,
    )


def _canard(cote: int, retrait: float = 0.0, nom: str = ""):
    def attaque(y):
        return CANARD_ATTAQUE + max(0.0, y - CANARD_FLANC) * math.tan(CANARD_FLECHE)

    def fuite(y):
        return CANARD_FUITE + max(0.0, y - CANARD_FLANC) * CANARD_FLECHE_FUITE

    envergures = [AILE_EMPLANTURE] + _stations(CANARD_FLANC, CANARD_DEMI_ENVERGURE, 0.3)
    return _surface(
        nom or f"canard_{_cote(cote)}", envergures, attaque, fuite,
        CANARD_EPAISSEUR, lambda y, x, d: (x, cote * y, CANARD_Z + d), retrait,
    )


def _derive(retrait: float = 0.0, nom: str = "derive"):
    def attaque(z):
        return DERIVE_ATTAQUE + max(0.0, z - DERIVE_BASE) * math.tan(DERIVE_FLECHE)

    def fuite(z):
        return DERIVE_FUITE - max(0.0, z - DERIVE_BASE) * 0.1

    hauteurs = [DERIVE_PIED] + _stations(DERIVE_BASE, DERIVE_SOMMET, 0.3)
    return _surface(nom, hauteurs, attaque, fuite, DERIVE_EPAISSEUR, lambda z, x, d: (x, d, z), retrait)


def _cercle(x, yc, zc, rayon, points=32):
    return _superellipse(x, yc, zc, rayon, rayon, rayon, 2.0, points)


def _tuyere(cote: int, retrait: float = 0.0, nom: str = ""):
    (x0, r0), (x1, r1) = TUYERE
    sections = [_cercle(x, cote * TUYERE_Y, TUYERE_Z, r0 + (r1 - r0) * (x - x0) / (x1 - x0) - retrait, 48)
                for x in _stations(x0, x1, 0.2)]
    return _objet(nom or f"tuyere_{_cote(cote)}", sections)


def _creux_tuyere(cote: int):
    rayon, profondeur = TUYERE_CREUX
    sections = [_cercle(x, cote * TUYERE_Y, TUYERE_Z, rayon, 48) for x in (LONGUEUR - profondeur, LONGUEUR + 0.2)]
    return _objet(f"creux_tuyere_{_cote(cote)}", sections)


def _rail(cote: int, retrait: float = 0.0, nom: str = ""):
    debut, fin = RAIL
    sections = [_cercle(debut, cote * RAIL_Y, AILE_Z, RAIL_RAYON * 0.3 - retrait, 24)]
    sections += [_cercle(x, cote * RAIL_Y, AILE_Z, RAIL_RAYON - retrait, 24) for x in _stations(debut + 0.3, fin, 0.5)]
    return _objet(nom or f"rail_{_cote(cote)}", sections)


def _perche(retrait: float = 0.0, nom: str = "perche"):
    sections = []
    for x in _stations(PERCHE[0][0], PERCHE[-1][0], 0.1):
        rayon, z = _hermite(PERCHE, 1, x), _hermite(PERCHE, 2, x)
        sections.append(_cercle(x, PERCHE_Y, z, rayon - retrait, 20))
    return _objet(nom, sections)


def _boite(nom, x0, x1, demi_largeur, z0, z1, y=0.0):
    sections = [
        [(x, y - demi_largeur, z0), (x, y + demi_largeur, z0), (x, y + demi_largeur, z1), (x, y - demi_largeur, z1)]
        for x in (x0, x1)
    ]
    return _objet(nom, sections)


def _crosse(retrait: float = 0.0, nom: str = "crosse"):
    x0, x1, demi, z0, z1 = CROSSE
    return _boite(nom, x0 + retrait, x1 - retrait, demi - retrait, z0 + retrait, z1 - retrait)


def _lame(nom, debut, fin, z0, z1):
    """Prisme fin de largeur GRAVURE_LARGEUR, tendu entre deux points (x, y) de l'avion."""
    (xa, ya), (xb, yb) = debut, fin
    longueur = math.hypot(xb - xa, yb - ya)
    nx, ny = -(yb - ya) / longueur, (xb - xa) / longueur
    demi = GRAVURE_LARGEUR / 2 / MM
    sections = [
        [(x - nx * demi, y - ny * demi, z0), (x + nx * demi, y + ny * demi, z0),
         (x + nx * demi, y + ny * demi, z1), (x - nx * demi, y - ny * demi, z1)]
        for x, y in ((xa, ya), (xb, yb))
    ]
    return _objet(nom, sections)


def _booleen(objet, operation, cible):
    modificateur = objet.modifiers.new(f"{operation.lower()}_{cible.name}", "BOOLEAN")
    modificateur.operation, modificateur.solver = operation, "EXACT"
    if isinstance(cible, bpy.types.Collection):
        modificateur.operand_type, modificateur.collection = "COLLECTION", cible
    else:
        modificateur.object = cible


def _collection(nom, objets):
    collection = bpy.data.collections.new(nom)
    for objet in objets:
        collection.objects.link(objet)
    return collection


def construire():
    # Chaque volume se construit trois fois : tel quel ; gonflé de JEU_GRAVURE (la lame part
    # de là, au-dessus de la peau) ; aminci de GRAVURE_PROFONDEUR (le fond de la gravure).
    fabriques = {
        "fuselage": _fuselage,
        "verriere": _verriere,
        "derive": _derive,
        "perche": _perche,
        "crosse": _crosse,
    }
    for cote in (1, -1):
        for nom, fabrique in (("aile", _aile), ("entree_air", _entree_air), ("canard", _canard),
                              ("tuyere", _tuyere), ("rail", _rail)):
            fabriques[f"{nom}_{_cote(cote)}"] = lambda r=0.0, n="", f=fabrique, c=cote: f(c, r, n)
    volumes = {nom: fabrique(0.0, nom) for nom, fabrique in fabriques.items()}
    jeu, profondeur = JEU_GRAVURE / MM, GRAVURE_PROFONDEUR / MM
    gonfles = {nom: fabrique(-jeu, f"gonfle_{nom}") for nom, fabrique in fabriques.items()}
    sauf = {}

    def graver(nom, lame):
        """La lame ne creuse que la peau exposée du volume `nom` : la peau est le volume gonflé
        moins son double aminci ; ce qui touche une autre pièce (gonflée) est épargné, sans quoi
        la gravure laisserait un vide enfermé. Aucune face de la lame ne coïncide avec la pièce."""
        if nom not in sauf:
            sauf[nom] = _collection(f"sauf_{nom}", [g for n, g in gonfles.items() if n != nom])
        _booleen(lame, "INTERSECT", gonfles[nom])
        _booleen(lame, "DIFFERENCE", fabriques[nom](profondeur, f"fond_{lame.name}"))
        _booleen(lame, "DIFFERENCE", sauf[nom])
        return lame

    creux = [_creux_entree_air(cote) for cote in (1, -1)] + [_creux_tuyere(cote) for cote in (1, -1)]
    for x in ANNEAUX_FUSELAGE:
        creux.append(graver("fuselage", _lame(f"anneau_{x}", (x, -3.0), (x, 3.0), -3.0, 4.0)))
    for x in ANNEAUX_VERRIERE:
        creux.append(graver("verriere", _lame(f"verriere_{x}", (x, -3.0), (x, 3.0), -3.0, 4.0)))
    creux.append(graver("derive", _lame("gouverne_derive", (GOUVERNE_DERIVE, -1.0), (GOUVERNE_DERIVE, 1.0), 0.0, 4.0)))
    for cote in (1, -1):
        aile = f"aile_{_cote(cote)}"
        creux.append(graver(aile, _lame(f"charniere_{_cote(cote)}", (GOUVERNE_AILE, cote * 1.0), (GOUVERNE_AILE, cote * 5.25), -2.0, 2.0)))
        creux.append(graver(aile, _lame(
            f"elevons_{_cote(cote)}", (GOUVERNE_AILE - 0.1, cote * SEPARATION_ELEVONS),
            (AILE_FUITE - ELEVONS_RETRAIT_FUITE, cote * SEPARATION_ELEVONS), AILE_Z, 2.0)))  # dessus seul : l'aile y est trop mince pour deux gravures
        bec = [(AILE_ATTAQUE + (y - AILE_FLANC) * math.tan(AILE_FLECHE) + BEC, cote * y) for y in BEC_ENVERGURE]
        creux.append(graver(aile, _lame(f"becs_{_cote(cote)}", bec[0], bec[1], -2.0, 2.0)))
    creux.append(_boite("ventre", -1.0, LONGUEUR + 1.0, 8.0, Z_COUPE - 3.0, Z_COUPE))

    fuselage = volumes["fuselage"]
    rafale = bpy.data.objects.new("rafale_m", fuselage.data.copy())
    bpy.context.scene.collection.objects.link(rafale)
    _booleen(rafale, "UNION", _collection("volumes", [v for v in volumes.values() if v is not fuselage]))
    _booleen(rafale, "DIFFERENCE", _collection("creux", creux))
    for objet in bpy.context.scene.objects:
        if objet is rafale:
            continue
        objet.display_type = "WIRE"  # outils de construction, visibles en fil de fer dans le .blend
        if objet in volumes.values():
            continue
        for polygone in objet.data.polygons:
            polygone.use_smooth = False  # parois et fonds de gravure à arêtes vives, pas lissés
    return rafale
