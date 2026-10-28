# `uv run generer`

`uv run generer <nom>` : contrôles, dix vues PNG, puis les exports dans `out/<nom>/`
(build123d : STEP + STL ; Blender : STL + `.blend`).

`uv run generer` sans nom ouvre un menu dans un terminal (flèches, frappe pour filtrer, Entrée
pour générer, Échap ou Ctrl-C pour annuler) ; hors terminal, il liste les pièces. Quand le filtre ne
correspond à aucune pièce, la liste se vide et Entrée reste sans effet. Un dossier de `pieces/`
au nom non conforme est écarté et signalé.

## Codes de sortie

0 pièce exportée (ou liste affichée), 1 la pièce échoue (contrôle en ÉCHEC ou exception dans
`construire()`, Blender planté ou bloqué plus de 600 s), 2 erreur d'usage (nom inconnu ou
invalide, `construire()` absent, `piece.py` et `scene.py` dans le même dossier, Blender
introuvable ou `BLENDER` invalide), 130 menu quitté sans choix (annulation, collage).

`out/<nom>/` est vidé à chaque run : après un échec il ne contient que les PNG, jamais un
export d'une version précédente.

## Lire les vues PNG

Les PNG se rendent avant l'export, même sur une pièce en ÉCHEC, et c'est voulu : ils servent à
voir pourquoi la génération a échoué. Les lire avant de corriger. Un rendu qui échoue lui-même
ne bloque rien : `generer` écrit « rendu impossible » sur stderr et poursuit.

- build123d : arêtes vues en trait noir, cachées en tirets gris. Blender : rendu ombré, seule
  la silhouette est tracée, un ressaut vu de face ne se lit qu'à l'ombrage (ouvrir les vues
  `iso_*` ou le `.blend` en cas de doute).
- Toujours les quatre vues principales, `iso_avant_droite`, `dessus`, `face`, `droite`. Les
  autres s'ouvrent quand un détail ne se lit pas bien sur les principales : `dessous`,
  `arriere`, `gauche`, ou une des trois autres isométriques, `iso_avant_gauche`,
  `iso_arriere_droite`, `iso_arriere_gauche`, prises d'en haut depuis chaque coin (avant = -Y,
  droite = +X, côtés de la pièce). Aller chercher la ou les vues qui tranchent, pas les dix
  d'office.
- Hors `iso_*`, chaque vue porte un cadre gradué en mm dans les coordonnées de la pièce : une
  position lue sur l'image se compare aux constantes de `piece.py` ou `scene.py`. Le titre
  donne les axes ; `dessous`, `arriere` et `gauche` sont des vues miroir, leur axe horizontal
  décroît vers la droite. Un axe trop court pour deux graduations porte ses deux extrémités,
  écrites `a .. b` dans le sens de l'image.

## Contrôles

ÉCHEC (pas d'export) : pas un `Part`, aucun solide, plusieurs solides, géométrie invalide,
volume nul, dépassement du volume de la buse principale. AVERTISSEMENT (export quand même) :
pièce non posée sur Z = 0. X et Y se comparent triés : la pièce peut tourner de 90° sur le
plateau.

Imprimabilité, les deux filières, jamais bloquante : une ligne `imprimabilité` donne la
surface en surplomb au-delà de 45° de la verticale (faces posées sur le plateau exclues, ponts
compris) et sa plage de Z, puis l'épaisseur de paroi mesurée par 2000 rayons tirés vers
l'intérieur de la surface (minimum, 5e centile, part sous 0,8 mm). AVERTISSEMENT quand plus de
1 % de la surface est sous 0,8 mm (deux largeurs de buse). Le minimum descend souvent à
0,15 mm sur un bord arrondi ou un filet : c'est la part sous 0,8 mm qui compte. Comparer la
ligne au `NOTES.md` : un surplomb mesuré avec « aucun support » écrit doit être un pont ou un
chanfrein voulu, sinon le dire. Paramètres en tête de `atelier/imprimabilite.py`.

Filière Blender, ÉCHEC en plus : pas un objet MESH, aucune face, plusieurs parties disjointes,
maillage non étanche (arêtes non manifold), normales incohérentes, volume nul ou négatif
(normales tournées vers l'intérieur), STL exporté différent du maillage contrôlé. Limites : une
pièce creuse (cavité fermée) compte comme deux parties ; les auto-intersections ne sont pas
détectées.
