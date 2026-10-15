# IRwR — atelier de pièces 3D en code-CAD

Des pièces écrites en Python, tranchées dans Bambu Studio et imprimées sur une Bambu Lab X2D.
La pièce est son code : `out/` se régénère et ne se versionne pas.

## Deux filières : build123d ou Blender

| | build123d | Blender |
| --- | --- | --- |
| Fichier | `pieces/<nom>/piece.py` | `pieces/<nom>/scene.py` |
| Pour | cotes, ajustements, visserie | formes libres, sculptées, organiques |
| Géométrie | BREP, courbes exactes | maillage (triangles) |
| Exports | STEP + STL | STL + `.blend` |
| Vues PNG | arêtes vues et cachées | rendu ombré, silhouette seule |

**Avant d'écrire une nouvelle pièce, demander à l'utilisateur la filière** (sauf s'il l'a déjà
nommée), en recommandant celle qui convient. Un dossier porte l'une ou l'autre, jamais les deux.
Une nouvelle pièce démarre par la skill `nouvelle-piece`.

## À retenir

- **Une seule buse en service** (la principale, gauche) : impression mono-matière, et le
  support sort dans la matière de la pièce. Volume contrôlé : 256 × 256 × 260 mm.
- Contrat : `construire()` rend un `Part` (build123d) ou un objet MESH (Blender) ; mm, Z vers
  le haut, posé sur Z = 0 dans son orientation d'impression ; un seul solide ; cotes en
  constantes en tête de fichier ; `<nom>` en minuscules, chiffres et `_`.
- Flux : écrire la pièce et son `NOTES.md`, `uv run generer <nom>`, **lire les PNG** (les
  contrôles ne voient pas une erreur de forme), puis ouvrir dans Bambu Studio le `.step`
  (build123d) ou le `.stl` (Blender).

## Où lire le détail

Lire le fichier qui correspond **avant** la tâche concernée :

| Fichier | Quand |
| --- | --- |
| `docs/contrat-piece.md` | écrire ou modifier `piece.py` / `scene.py` ; contraintes du Python de Blender |
| `docs/conception.md` | concevoir une forme : orientation, surplombs, parois ; **jeux d'ajustement** par matériau |
| `docs/generer.md` | lancer `generer`, lire les vues PNG, interpréter un code de sortie ou un contrôle en ÉCHEC |
| `docs/imprimante.md` | volumes, buses, température ; ouvrir un export dans Bambu Studio |
| `docs/postes.md` | installer un poste, changer une dépendance (`uv.lock`) |

## Vérifier avant de conclure

- `uv run pytest` : toute la suite.
- `uv run generer <nom>` sur chaque pièce touchée, puis lecture de ses PNG.
- Les tests qui lancent le vrai Blender sont sautés quand il manque : le dire plutôt que
  conclure sur une suite partielle.
- `sh init.sh` après toute modification de `pyproject.toml`, `uv.lock` ou `init.sh`.
