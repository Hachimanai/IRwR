# IRwR — atelier de pièces 3D

Pièces imprimables écrites en Python pour Bambu Studio et une Bambu Lab X2D, par deux filières :

- **build123d** (`pieces/<nom>/piece.py`) : pièces cotées, ajustements, perçages. Courbes exactes,
  export STEP et STL.
- **Blender** (`pieces/<nom>/scene.py`) : formes libres, sculptées, organiques. Maillage, export
  STL et `.blend`. Demande Blender 4.2 ou plus (`sudo pacman -S blender`, ou la variable `BLENDER`).

```sh
git clone https://github.com/Hachimanai/IRwR.git && cd IRwR
sh init.sh                        # outils (uv, Blender), environnement, tests
uv run generer                    # menu : flèches, frappe pour filtrer, Entrée
uv run generer eprouvette_jeux    # → out/eprouvette_jeux/ : STEP, STL, sept vues PNG
uv run generer vase_torsade       # → out/vase_torsade/ : STL, .blend, sept vues PNG
```

## Filière Blender

`scene.py` expose `construire()`, qui rend l'objet Blender maillé (type MESH) à imprimer.
Mêmes règles que `piece.py` : 1 unité Blender = 1 mm, Z vers le haut, pièce posée sur Z = 0,
un seul solide, cotes en constantes, pas d'effet de bord à l'import. Seuls `bpy`, `bmesh`,
`mathutils` et la bibliothèque standard sont disponibles (Python de Blender, pas celui de uv) ;
`commun/imprimante.py` et `commun/jeux.py` s'importent, `commun/visserie.py` non (build123d).

`generer` lance Blender en arrière-plan sur une scène vide, appelle `construire()`, applique
les modificateurs de l'objet rendu, puis contrôle le maillage : étanche (aucune arête non
manifold), normales cohérentes et tournées vers l'extérieur (volume positif), un seul morceau,
tenue dans la X2D. Les vues sont des rendus ombrés posés dans le même cadre gradué que les vues
build123d : seule la silhouette est tracée, ni arêtes cachées ni arêtes vives internes (un
ressaut vu de face ne se lit qu'à l'ombrage, ouvrir `iso` ou le `.blend` en cas de doute).
Limites des contrôles : une pièce creuse (cavité fermée) compte comme deux parties et
échoue ; les auto-intersections ne sont pas détectées. Les autres objets de la scène (outils de booléen) ne sont ni
exportés ni rendus. Un `construire()` qui dépasse 600 s est arrêté. Mêmes codes de sortie ;
Blender introuvable donne 2.

Ouvrir `out/<nom>/<nom>.stl` dans Bambu Studio ; le `.blend` sert à inspecter ou retoucher la
pièce dans Blender (la retouche se reporte ensuite dans `scene.py`).

Écrire une pièce (l'une ou l'autre filière), conventions et réglages de l'imprimante : voir
`CLAUDE.md`, qui renvoie au détail dans `docs/`.
