# Contrat d'une pièce

## Les deux filières

- `piece.py` expose `construire() -> Part` (build123d) ; `scene.py` expose `construire()` qui
  rend l'objet Blender maillé (type MESH) à imprimer. Sans effet de bord à l'import.
- Unités en mm (Blender : 1 unité = 1 mm), Z vers le haut, pièce posée sur Z = 0 dans son
  orientation d'impression.
- Une pièce = un seul solide. Un assemblage s'écrit en plusieurs pièces.
- `<nom>` : minuscules, chiffres et `_`, en commençant par une lettre.
- Les cotes se nomment en constantes en tête de fichier, jamais en dur dans la géométrie.
- Les briques communes viennent de `commun/` : `visserie` (perçages M2 à M5, passage et
  lamage), `jeux` (ajustements par matériau), `imprimante` (volumes).
- `pieces/<nom>/NOTES.md` accompagne chaque pièce : cotes mesurées et leur origine, ce avec
  quoi la pièce s'assemble, hypothèses, supports (aucun, ou où les activer ou peindre dans
  Bambu Studio) et le tableau « Tirages » (résultat de chaque impression).

## Propre à `scene.py` (Blender)

- Il tourne dans le Python de Blender (4.2 au moins), lancé en arrière-plan sur une scène
  vide : seuls `bpy`, `bmesh`, `mathutils` et la bibliothèque standard. `commun.jeux` et
  `commun.imprimante` s'importent, `commun.visserie` non (il dépend de build123d).
- Les modificateurs de l'objet rendu sont appliqués avant contrôle et export. Les autres objets
  de la scène (outils de booléen) ne sont ni exportés ni rendus.
- Blender est cherché par la variable `BLENDER`, sinon `blender` dans le PATH. Exemple :
  `pieces/vase_torsade`.
