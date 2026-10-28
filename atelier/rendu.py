"""Vues PNG d'une pièce : arêtes vues en trait plein, cachées en tirets, cadre gradué en mm.

Une pièce Blender arrive déjà rendue en image : `composer` la pose dans le même cadre.
"""

import math
from itertools import pairwise
from pathlib import Path

from build123d import Shape, Vector
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_AbscissaPoint
from PIL import Image, ImageDraw, ImageFont

# nom → (direction de la caméra depuis le centre, haut de l'image, axes lus sur l'image)
# axes : (axe horizontal, sens, axe vertical) ; sens -1 = l'axe horizontal décroît vers la
# droite (vue miroir). L'axe vertical croît toujours vers le haut.
# None : vue axonométrique, ses trois axes sont raccourcis différemment, aucune graduation
# n'y serait juste. Les quatre `iso_*` regardent d'en haut depuis chaque coin ; l'avant est
# le côté -Y, celui de `face`, la droite le côté +X, celui de `droite` (côtés de la pièce,
# pas de l'observateur), et chacune montre davantage la face avant ou arrière.
VUES = {
    "iso_avant_droite": ((1, -1.3, 1), (0, 0, 1), None),
    "iso_avant_gauche": ((-1, -1.3, 1), (0, 0, 1), None),
    "iso_arriere_droite": ((1, 1.3, 1), (0, 0, 1), None),
    "iso_arriere_gauche": ((-1, 1.3, 1), (0, 0, 1), None),
    "dessus": ((0, 0, 1), (0, 1, 0), ("X", 1, "Y")),
    "dessous": ((0, 0, -1), (0, 1, 0), ("X", -1, "Y")),
    "face": ((0, -1, 0), (0, 0, 1), ("X", 1, "Z")),
    "arriere": ((0, 1, 0), (0, 0, 1), ("X", -1, "Z")),
    "droite": ((1, 0, 0), (0, 0, 1), ("Y", 1, "Z")),
    "gauche": ((-1, 0, 0), (0, 0, 1), ("Y", -1, "Z")),
}
# Plus grand côté de l'image, marges minimales comprises. Au-delà, un lecteur qui réduit
# l'image n'y gagne rien.
COTE_PX = 1500
# Marges minimales : la gauche et la droite s'élargissent pour un libellé ou un titre plus long.
MARGE_GAUCHE, MARGE_DROITE, MARGE_HAUT, MARGE_BAS = 100, 40, 60, 70
# Dessin à SUR fois la taille puis réduction : c'est l'anticrénelage.
SUR = 3
TRAIT_VU, TRAIT_CACHE, TRAIT_CADRE = 2, 1, 2
TIRET_PLEIN, TIRET_VIDE = 9, 6
PX_PAR_SEGMENT = 4
SEGMENTS_MIN, SEGMENTS_MAX = 8, 400
# Une arête est droite quand sa longueur ne dépasse sa corde que de cette fraction.
DROITE = 1e-7
# Le cadre gradué se tient à ECART_CADRE de la zone de dessin, ses tirets font TIRET.
ECART_CADRE, TIRET = 14, 10
ECART_LIBELLE_BAS, ECART_LIBELLE_GAUCHE = 4, 6
ECART_GRADUATIONS = 60
CORPS, CORPS_TITRE = 20, 24
# Le titre tient dans MARGE_HAUT : son ordonnée plus CORPS_TITRE restent en dessous.
ORIGINE_TITRE = (12, 14)
BORD = 8
NOIR, GRIS, GRILLE, BLANC = (20, 20, 20), (150, 150, 150), (225, 232, 240), (255, 255, 255)


def _pas(minimum: float) -> float:
    """Plus petit pas rond (1, 2 ou 5 × 10ⁿ) au moins égal à `minimum`."""
    decade = 10.0 ** math.floor(math.log10(minimum))
    return next(m * decade for m in (1, 2, 5, 10) if m * decade >= minimum * (1 - 1e-9))


def _graduations(debut: float, fin: float, pas: float) -> list[float]:
    return [k * pas for k in range(math.ceil(debut / pas - 1e-6), math.floor(fin / pas + 1e-6) + 1)]


def _libelle(valeur: float, pas: float) -> str:
    decimales = max(0, -math.floor(math.log10(pas)))
    return f"{round(valeur, decimales) + 0.0:.{decimales}f}".replace(".", ",")


def _reperes(sens: int, origine: float, debut: float, fin: float, pas: float) -> list[tuple[float, str, bool]]:
    """Les repères d'un axe : (coordonnée projetée, libellé, tiret ?).

    Une coordonnée projetée se compte depuis le centre de la pièce : `origine` l'y rajoute.
    Un axe trop court pour deux graduations porte ses deux extrémités et un seul libellé.
    """
    valeurs = _graduations(*sorted((origine + sens * debut, origine + sens * fin)), pas)
    if len(valeurs) >= 2:
        return [((valeur - origine) * sens, _libelle(valeur, pas), True) for valeur in valeurs]
    fin_pas = _pas(max(fin - debut, 1e-9) / 100)
    extremites = " .. ".join(_libelle(origine + sens * bord, fin_pas) for bord in (debut, fin))
    return [(debut, "", True), (fin, "", True), ((debut + fin) / 2, extremites, False)]


def _points(courbe: BRepAdaptor_Curve, segments: int) -> list[tuple[float, float]]:
    # Par paramètre de courbe : `position_at` recalcule la longueur de l'arête à chaque point.
    debut, fin = courbe.FirstParameter(), courbe.LastParameter()
    return [(p.X(), p.Y()) for p in (courbe.Value(debut + (fin - debut) * i / segments) for i in range(segments + 1))]


def _polyligne(courbe: BRepAdaptor_Curve, ebauche: list[tuple[float, float]], echelle: float) -> list[tuple[float, float]]:
    """Une arête à un segment pour PX_PAR_SEGMENT pixels ; deux points si elle est droite.

    La longueur est celle de la courbe, pas de l'ébauche : les points d'une hélice vue de côté
    peuvent s'aligner. Le type de courbe ne dit rien : une arête droite projetée sort en B-spline.
    """
    longueur = GCPnts_AbscissaPoint.Length_s(courbe)
    if longueur <= math.dist(ebauche[0], ebauche[-1]) * (1 + DROITE):
        return [ebauche[0], ebauche[-1]]
    segments = min(SEGMENTS_MAX, max(SEGMENTS_MIN, math.ceil(longueur * echelle / PX_PAR_SEGMENT)))
    return ebauche if segments == SEGMENTS_MIN else _points(courbe, segments)


def _emprise(polylignes) -> tuple[float, float, float, float]:
    xs, ys = zip(*(point for points in polylignes for point in points))
    return min(xs), max(xs), min(ys), max(ys)


def _echelle(x_min: float, x_max: float, y_min: float, y_max: float) -> float:
    return min(
        (COTE_PX - MARGE_GAUCHE - MARGE_DROITE) / max(x_max - x_min, 1e-6),
        (COTE_PX - MARGE_HAUT - MARGE_BAS) / max(y_max - y_min, 1e-6),
    )


def _tirets(points, plein: float, vide: float):
    """Découpe une polyligne en tirets de `plein` séparés de `vide`.

    Le motif se cale sur la position dans l'image, pas sur le début de l'arête : deux arêtes
    superposées, même de sens opposés, posent leurs tirets au même endroit.
    """
    (x0, y0), (x1, y1) = points[0], points[-1]
    if (x1, y1) < (x0, y0):
        points, (x0, y0), (x1, y1) = points[::-1], (x1, y1), (x0, y0)
    corde = math.dist((x0, y0), (x1, y1))
    phase = (x0 * (x1 - x0) + y0 * (y1 - y0)) / corde % (plein + vide) if corde else 0.0
    trace = phase < plein
    tirets, courant, reste = [], [points[0]], (plein if trace else plein + vide) - phase
    for a, b in pairwise(points):
        longueur, parcouru = math.dist(a, b), 0.0
        while longueur - parcouru > reste:
            parcouru += reste
            coupe = (a[0] + (b[0] - a[0]) * parcouru / longueur, a[1] + (b[1] - a[1]) * parcouru / longueur)
            if trace:
                tirets.append([*courant, coupe])
            courant, trace = [coupe], not trace
            reste = plein if trace else vide
        reste -= longueur - parcouru
        if trace:
            courant.append(b)
    if trace and len(courant) > 1:
        tirets.append(courant)
    return tirets


def _dessiner(nom: str, vues, cachees, axes, centre: Vector, fichier: Path) -> None:
    aretes = [(arete, cachee) for cachee, groupe in ((True, cachees), (False, vues)) for arete in groupe]
    if not aretes:
        raise ValueError("aucune arête à dessiner")
    # L'ébauche donne l'échelle, l'échelle donne le nombre de segments de chaque courbe.
    courbes = [BRepAdaptor_Curve(arete.wrapped) for arete, _ in aretes]
    ebauches = [_points(courbe, SEGMENTS_MIN) for courbe in courbes]
    approchee = _echelle(*_emprise(ebauches))
    traits = [
        (_polyligne(courbe, ebauche, approchee), cachee)
        for courbe, ebauche, (_, cachee) in zip(courbes, ebauches, aretes)
    ]

    def tracer(page: "_Page") -> None:
        for points, cachee in traits:
            pixels = [page.px(x, y) for x, y in points]
            if cachee:
                for tiret in _tirets(pixels, TIRET_PLEIN * SUR, TIRET_VIDE * SUR):
                    page.trait(tiret, GRIS, TRAIT_CACHE)
            else:
                page.trait(pixels, NOIR, TRAIT_VU)

    _mettre_en_page(nom, _emprise(points for points, _ in traits), axes, centre, tracer, fichier)


class _Page:
    """L'image en cours, à SUR fois sa taille finale, et le passage des mm de la vue aux pixels."""

    def __init__(self, image: Image.Image, marge_gauche: float, x_min: float, y_max: float, echelle: float):
        self.image, self.crayon = image, ImageDraw.Draw(image)
        self.marge_gauche, self.x_min, self.y_max, self.echelle = marge_gauche, x_min, y_max, echelle

    def px(self, x: float, y: float) -> tuple[float, float]:
        return (self.marge_gauche + (x - self.x_min) * self.echelle) * SUR, (MARGE_HAUT + (self.y_max - y) * self.echelle) * SUR

    def trait(self, points, couleur, epaisseur: int) -> None:
        self.crayon.line(points, fill=couleur, width=epaisseur * SUR, joint="curve")


def _mettre_en_page(nom: str, emprise, axes, centre: Vector, tracer, fichier: Path) -> None:
    """Le cadre gradué, la grille et le titre autour de ce que `tracer(page)` dessine dans l'emprise.

    `emprise` (x_min, x_max, y_min, y_max) est en mm dans le repère de la vue, compté depuis `centre`.
    """
    x_min, x_max, y_min, y_max = emprise
    echelle = _echelle(x_min, x_max, y_min, y_max)

    police = ImageFont.load_default(size=CORPS * SUR)
    police_titre = ImageFont.load_default(size=CORPS_TITRE * SUR)
    titre, horizontaux, verticaux = nom, [], []
    if axes:
        axe_h, sens_h, axe_v = axes
        pas = _pas(ECART_GRADUATIONS / echelle)
        horizontaux = _reperes(sens_h, getattr(centre, axe_h), x_min, x_max, pas)
        verticaux = _reperes(1, getattr(centre, axe_v), y_min, y_max, pas)
        cote = "droite" if sens_h > 0 else "gauche"
        echelle_lue = f"{echelle:.1f}".replace(".", ",")
        titre = f"{nom}  |  {axe_h} vers la {cote}, {axe_v} vers le haut  |  mm, {echelle_lue} px/mm"

    def large(texte: str, avec=police) -> float:
        return avec.getlength(texte) / SUR

    # Les marges s'élargissent pour ne rogner ni un libellé ni le titre.
    marge_gauche = max(
        [MARGE_GAUCHE, *(ECART_CADRE + TIRET + ECART_LIBELLE_GAUCHE + large(t) + BORD for _, t, _ in verticaux)]
    )
    dessin = round((x_max - x_min) * echelle)
    marge_droite = max(
        [
            MARGE_DROITE,
            ORIGINE_TITRE[0] + large(titre, police_titre) + BORD - marge_gauche - dessin,
            *((x - x_max) * echelle + large(t) / 2 + BORD for x, t, _ in horizontaux),
        ]
    )
    largeur = math.ceil(marge_gauche + dessin + marge_droite)
    hauteur = MARGE_HAUT + round((y_max - y_min) * echelle) + MARGE_BAS
    page = _Page(Image.new("RGB", (largeur * SUR, hauteur * SUR), BLANC), marge_gauche, x_min, y_max, echelle)
    crayon, trait = page.crayon, page.trait

    def px_x(x: float) -> float:
        return page.px(x, 0)[0]

    def px_y(y: float) -> float:
        return page.px(0, y)[1]

    if axes:
        gauche, droite, bas, haut = px_x(x_min), px_x(x_max), px_y(y_min), px_y(y_max)
        cadre_x, cadre_y = gauche - ECART_CADRE * SUR, bas + ECART_CADRE * SUR
        for x, _, tiret in horizontaux:
            if tiret:
                trait([(px_x(x), haut), (px_x(x), bas)], GRILLE, 1)
        for y, _, tiret in verticaux:
            if tiret:
                trait([(gauche, px_y(y)), (droite, px_y(y))], GRILLE, 1)
        trait([(cadre_x, haut), (cadre_x, cadre_y), (droite, cadre_y)], NOIR, TRAIT_CADRE)
        for x, libelle, tiret in horizontaux:
            if tiret:
                trait([(px_x(x), cadre_y), (px_x(x), cadre_y + TIRET * SUR)], NOIR, TRAIT_CADRE)
            if libelle:
                ancre = (px_x(x), cadre_y + (TIRET + ECART_LIBELLE_BAS) * SUR)
                crayon.text(ancre, libelle, fill=NOIR, font=police, anchor="ma")
        for y, libelle, tiret in verticaux:
            if tiret:
                trait([(cadre_x - TIRET * SUR, px_y(y)), (cadre_x, px_y(y))], NOIR, TRAIT_CADRE)
            if libelle:
                ancre = (cadre_x - (TIRET + ECART_LIBELLE_GAUCHE) * SUR, px_y(y))
                crayon.text(ancre, libelle, fill=NOIR, font=police, anchor="rm")

    tracer(page)
    crayon.text((ORIGINE_TITRE[0] * SUR, ORIGINE_TITRE[1] * SUR), titre, fill=NOIR, font=police_titre)
    # Réduction par un facteur entier : la moyenne des SUR × SUR pixels, sans filtre à calculer.
    page.image.reduce(SUR).save(fichier)


def composer(nom: str, rendu: Path, cadrage, emprise, centre, fichier: Path) -> Path:
    """Pose une image déjà rendue (Blender) dans le cadre gradué de la vue `nom`.

    `cadrage` est la zone que couvre l'image, `emprise` celle de la pièce, toutes deux
    (x_min, x_max, y_min, y_max) en mm dans le repère de la vue, comptés depuis `centre` (x, y, z).
    """
    with Image.open(rendu) as source:
        image = source.convert("RGBA")

    def tracer(page: _Page) -> None:
        x_min, x_max, y_min, y_max = cadrage
        (gauche, haut), (droite, bas) = page.px(x_min, y_max), page.px(x_max, y_min)
        boite = (round(gauche), round(haut), round(droite), round(bas))
        posee = image.resize((max(1, boite[2] - boite[0]), max(1, boite[3] - boite[1])), Image.LANCZOS)
        page.image.paste(posee, boite[:2], posee)

    _mettre_en_page(nom, emprise, VUES[nom][2], Vector(*centre), tracer, fichier)
    return fichier


def rendre(piece: Shape, dossier: Path) -> list[Path]:
    boite = piece.bounding_box()
    centre = boite.center()
    recul = max(boite.diagonal, 1.0) * 10
    fichiers = []
    for nom, (direction, haut, axes) in VUES.items():
        camera = centre + Vector(*direction).normalized() * recul
        vues, cachees = piece.project_to_viewport(tuple(camera), viewport_up=haut, look_at=tuple(centre))
        fichier = dossier / f"{nom}.png"
        _dessiner(nom, vues, cachees, axes, centre, fichier)
        fichiers.append(fichier)
    return fichiers
