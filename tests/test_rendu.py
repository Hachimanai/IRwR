import pytest
from build123d import Align, Box, BuildPart, Cylinder, Helix, Locations, Mode
from PIL import Image, ImageDraw

from atelier import rendu
from atelier.rendu import COTE_PX, VUES, rendre

COIN = (Align.MIN, Align.MIN, Align.MIN)
SOMBRE = 100


def piece(*boites):
    with BuildPart() as assemblage:
        for position, dimensions in boites:
            with Locations(position):
                Box(*dimensions, align=COIN)
    return assemblage.part


@pytest.fixture(scope="module")
def vues(tmp_path_factory):
    """Une boîte X 0..43, Y 0..20, Z 0..10 et un plot vers le coin +X +Y +Z.

    Le plot dépasse en Y et en Z : dans chaque vue orthogonale, il est seul tout en haut de l'image.
    """
    solide = piece(((0, 0, 0), (43, 20, 10)), ((30, 14, 10), (10, 8, 6)))
    dossier = tmp_path_factory.mktemp("vues")
    return {fichier.stem: Image.open(fichier).convert("L") for fichier in rendre(solide, dossier)}


def position_du_sommet(image):
    """Où tombe, de 0 (gauche) à 1 (droite), ce qui est dessiné tout en haut de la zone de dessin."""
    zone = image.crop((rendu.MARGE_GAUCHE, rendu.MARGE_HAUT, image.width - rendu.MARGE_DROITE, image.height - rendu.MARGE_BAS))
    sommet = zone.crop((0, 0, zone.width, zone.height // 20))
    colonnes = [x for x in range(sommet.width) for y in range(sommet.height) if sommet.getpixel((x, y)) < SOMBRE]
    assert colonnes
    return sum(colonnes) / len(colonnes) / sommet.width


def sombre(image, points):
    return any(image.getpixel(point) < SOMBRE for point in points)


@pytest.fixture
def textes(monkeypatch):
    """Ce que `rendre` écrit dans l'image : (position, texte, ancre) de chaque appel."""
    ecrits = []
    ecrire = ImageDraw.ImageDraw.text

    def espion(self, xy, text, *args, **kwargs):
        ecrits.append((xy, text, kwargs.get("anchor")))
        return ecrire(self, xy, text, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", espion)
    return ecrits


def test_noms_des_vues():
    assert list(VUES) == [
        "iso_avant_droite",
        "iso_avant_gauche",
        "iso_arriere_droite",
        "iso_arriere_gauche",
        "dessus",
        "dessous",
        "face",
        "arriere",
        "droite",
        "gauche",
    ]


@pytest.mark.parametrize(
    ("vue", "plot_a_droite"),
    [
        ("dessus", True),
        ("dessous", False),
        ("face", True),
        ("arriere", False),
        ("droite", True),
        ("gauche", False),
    ],
)
def test_orientation(vues, vue, plot_a_droite):
    # Image retournée de haut en bas : le sommet montre le dessous de la boîte, centré, et les deux cas échouent.
    position = position_du_sommet(vues[vue])
    assert position > 0.65 if plot_a_droite else position < 0.35


@pytest.mark.parametrize(
    ("vue", "coin"),
    [
        ("iso_avant_droite", (36, 36)),
        ("iso_avant_gauche", (36, 0)),
        ("iso_arriere_droite", (0, 36)),
        ("iso_arriere_gauche", (0, 0)),
    ],
)
def test_orientation_iso(tmp_path, monkeypatch, vue, coin):
    """Un mât à un coin d'une plaque : dans chaque vue iso, un seul coin tombe tout à droite.

    Les deux coins voisins tombent près du milieu ou à gauche : deux vues échangées échouent.
    """
    monkeypatch.setattr(rendu, "VUES", {vue: rendu.VUES[vue]})
    rendre(piece(((0, 0, 0), (40, 40, 2)), ((*coin, 2), (4, 4, 40))), tmp_path)
    assert position_du_sommet(Image.open(tmp_path / f"{vue}.png").convert("L")) > 0.65


@pytest.mark.parametrize(("vue", "bord_du_zero"), [("dessus", "gauche"), ("dessous", "droite")])
def test_graduation_en_coordonnees_de_la_piece(vues, vue, bord_du_zero):
    """Pas de 2 mm sur 43 mm : un tiret tombe sur le bord X = 0, aucun sur le bord X = 43."""
    image = vues[vue]
    y = image.height - rendu.MARGE_BAS + rendu.ECART_CADRE + rendu.TIRET // 2
    bords = {"gauche": rendu.MARGE_GAUCHE, "droite": image.width - rendu.MARGE_DROITE}
    tirets = {bord: any(image.getpixel((x + dx, y)) < SOMBRE for dx in range(-3, 4)) for bord, x in bords.items()}
    assert tirets == {bord: bord == bord_du_zero for bord in bords}


def test_plus_grand_cote(vues, tmp_path):
    assert vues["dessus"].width == COTE_PX
    rendre(piece(((0, 0, 0), (10, 10, 40))), tmp_path)
    assert Image.open(tmp_path / "face.png").height == COTE_PX


@pytest.mark.parametrize(
    ("minimum", "attendu"),
    [(0.033, 0.05), (0.9, 1), (1, 1), (2.1, 5), (6.5, 10), (17, 20), (51, 100)],
)
def test_pas_rond(minimum, attendu):
    assert rendu._pas(minimum) == pytest.approx(attendu)


@pytest.mark.parametrize(
    ("valeur", "pas", "attendu"),
    [(3 * 0.05, 0.05, "0,15"), (-0.0, 5, "0"), (-20, 2, "-20"), (2.5, 0.5, "2,5")],
)
def test_libelle(valeur, pas, attendu):
    assert rendu._libelle(valeur, pas) == attendu


@pytest.fixture(scope="module")
def vues_hors_pas(tmp_path_factory):
    """43 × 27 × 17 : aucune étendue n'est multiple du pas de 2 mm, seul le bord 0 de chaque axe porte un tiret."""
    dossier = tmp_path_factory.mktemp("hors_pas")
    return {f.stem: Image.open(f).convert("L") for f in rendre(piece(((0, 0, 0), (43, 27, 17))), dossier)}


@pytest.mark.parametrize(
    ("vue", "bord_du_zero"),
    [
        ("dessus", "gauche"),
        ("dessous", "droite"),
        ("face", "gauche"),
        ("arriere", "droite"),
        ("droite", "gauche"),
        ("gauche", "droite"),
    ],
)
def test_graduations_de_chaque_vue(vues_hors_pas, vue, bord_du_zero):
    image = vues_hors_pas[vue]
    y = image.height - rendu.MARGE_BAS + rendu.ECART_CADRE + rendu.TIRET // 2
    bords = {"gauche": rendu.MARGE_GAUCHE, "droite": image.width - rendu.MARGE_DROITE}
    tirets = {bord: sombre(image, [(x + dx, y) for dx in range(-3, 4)]) for bord, x in bords.items()}
    assert tirets == {bord: bord == bord_du_zero for bord in bords}
    # Axe vertical, toujours vers le haut : un tiret au bord bas (coordonnée 0), aucun au bord haut.
    x = rendu.MARGE_GAUCHE - rendu.ECART_CADRE - rendu.TIRET // 2
    assert sombre(image, [(x, image.height - rendu.MARGE_BAS + dy) for dy in range(-3, 4)])
    assert not sombre(image, [(x, rendu.MARGE_HAUT + dy) for dy in range(-3, 4)])


X, Y, Z = (-30, 12), (100, 126), (200, 216)


@pytest.mark.parametrize(
    ("vue", "horizontal", "vertical"),
    [
        ("dessus", X, Y),
        ("dessous", X[::-1], Y),
        ("face", X, Z),
        ("arriere", X[::-1], Z),
        ("droite", Y, Z),
        ("gauche", Y[::-1], Z),
    ],
)
def test_libelles_suivent_les_axes(tmp_path, monkeypatch, textes, vue, horizontal, vertical):
    """Pièce X -30..13, Y 100..127, Z 200..217, pas de 2 mm : les chiffres disent l'axe et son sens.

    `horizontal` se lit de gauche à droite, `vertical` de bas en haut.
    """
    monkeypatch.setattr(rendu, "VUES", {vue: rendu.VUES[vue]})
    rendre(piece(((-30, 100, 200), (43, 27, 17))), tmp_path)
    lus_h = [int(texte) for _, texte, _ in sorted(t for t in textes if t[2] == "ma")]
    lus_v = [int(texte) for (_, y), texte, _ in sorted((t for t in textes if t[2] == "rm"), key=lambda t: -t[0][1])]
    for lus, (premier, dernier) in ((lus_h, horizontal), (lus_v, vertical)):
        assert lus == list(range(premier, dernier + (2 if dernier > premier else -2), 2 if dernier > premier else -2))


def test_cercle_trace(tmp_path):
    """Un cylindre vu de dessus : le trait passe par le point du cercle à 45°, loin de toute corde."""
    with BuildPart() as cylindre:
        Cylinder(20, 10, align=COIN)
    rendre(cylindre.part, tmp_path)
    image = Image.open(tmp_path / "dessus.png").convert("L")
    cote = image.width - rendu.MARGE_GAUCHE - rendu.MARGE_DROITE
    decalage = cote / 2 * (1 + 2**-0.5)
    x, y = round(rendu.MARGE_GAUCHE + decalage), round(rendu.MARGE_HAUT + cote - decalage)
    assert sombre(image, [(x + dx, y + dy) for dx in range(-3, 4) for dy in range(-3, 4)])


def test_titre_entier_sur_une_piece_etroite(tmp_path):
    rendre(piece(((0, 0, 0), (10, 10, 40))), tmp_path)
    image = Image.open(tmp_path / "gauche.png").convert("L")
    bord = image.crop((image.width - 6, 0, image.width, rendu.MARGE_HAUT - 15))
    assert not sombre(bord, [(x, y) for x in range(bord.width) for y in range(bord.height)])


def test_axe_trop_court_donne_ses_extremites(tmp_path, monkeypatch, textes):
    """Une plaque de 0,2 mm vue de face : l'axe Z n'a pas la place de deux graduations."""
    monkeypatch.setattr(rendu, "VUES", {"face": rendu.VUES["face"]})
    rendre(piece(((0, 0, 0), (250, 250, 0.2))), tmp_path)
    assert [texte for _, texte, ancre in textes if ancre == "rm"] == ["0,000 .. 0,200"]


def test_libelle_large_entier(tmp_path, monkeypatch, textes):
    """Une pièce à Y = -1000 : les libellés de l'axe vertical ne touchent pas le bord gauche de l'image."""
    monkeypatch.setattr(rendu, "VUES", {"dessus": rendu.VUES["dessus"]})
    rendre(piece(((0, -1000.5, 0), (0.5, 0.5, 0.5))), tmp_path)
    assert "-1000,25" in [texte for _, texte, _ in textes]
    image = Image.open(tmp_path / "dessus.png").convert("L")
    assert not sombre(image, [(x, y) for x in range(3) for y in range(rendu.MARGE_HAUT, image.height - rendu.MARGE_BAS)])


@pytest.mark.parametrize(
    ("debut", "fin", "pas", "attendu"),
    [(0, 43, 20, [0, 20, 40]), (-21.5, 21.5, 10, [-20, -10, 0, 10, 20]), (-4, 4, 2, [-4, -2, 0, 2, 4]), (0.3, 0.9, 1, [])],
)
def test_graduations(debut, fin, pas, attendu):
    assert rendu._graduations(debut, fin, pas) == pytest.approx(attendu)


def test_aretes_cachees_superposees_restent_en_tirets(tmp_path):
    """Le fond d'un trou borgne, vu de face : trois arêtes cachées superposées, et pourtant des vides."""
    with BuildPart() as bloc:
        Box(20, 20, 6, align=COIN)
        with Locations((6, 6, 1)):
            Cylinder(4, 5, align=COIN, mode=Mode.SUBTRACT)
    rendre(bloc.part, tmp_path)
    image = Image.open(tmp_path / "face.png").convert("L")
    echelle = (image.width - rendu.MARGE_GAUCHE - rendu.MARGE_DROITE) / 20
    y = round(image.height - rendu.MARGE_BAS - 1 * echelle)
    fond = [image.getpixel((x, y)) for x in range(round(rendu.MARGE_GAUCHE + 7 * echelle), round(rendu.MARGE_GAUCHE + 13 * echelle))]
    traces = sum(1 for pixel in fond if pixel < 220) / len(fond)
    assert 0.3 < traces < 0.85


def test_helice_vue_de_cote(tmp_path):
    """Quatre spires vues de côté : les points d'une ébauche grossière s'alignent, la courbe non."""
    rendre(Helix(pitch=5, height=20, radius=10), tmp_path)
    image = Image.open(tmp_path / "droite.png").convert("L")
    zone = image.crop((rendu.MARGE_GAUCHE, rendu.MARGE_HAUT, image.width - rendu.MARGE_DROITE, image.height - rendu.MARGE_BAS))
    assert zone.width > 500
    tiers = zone.width // 3
    for debut in (0, zone.width - tiers):
        bande = zone.crop((debut, 0, debut + tiers, zone.height))
        assert sum(bande.histogram()[:SOMBRE]) > 0
