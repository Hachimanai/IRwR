# IRwR — atelier de pièces 3D en code-CAD

Des pièces fonctionnelles écrites en Python avec build123d, exportées en STEP et STL, tranchées
dans Bambu Studio et imprimées sur une Bambu Lab X2D. La pièce est son code : `out/` se
régénère et ne se versionne pas.

## Imprimante : Bambu Lab X2D

- Volume buse principale : 256 × 256 × 260 mm. Volume buse auxiliaire : 235,5 × 256 × 256 mm.
  Les deux sont dans `commun/imprimante.py`, et `generer` les contrôle.
- Double buse : la principale (direct drive) porte la matière, l'auxiliaire (Bowden) est
  prévue pour le support. Un support dans un matériau dédié autorise des surplombs plus libres.
- Température maximale de buse : 300 °C ou 350 °C selon les sources, non tranché. À lire sur
  la fiche de la machine avant de viser un matériau technique.

## Flux de travail

1. Écrire `pieces/<nom>/piece.py` (contrat ci-dessous) et `pieces/<nom>/NOTES.md` (cotes
   mesurées, ce avec quoi la pièce s'assemble, résultat de chaque tirage).
2. `uv run generer <nom>` : contrôles, quatre vues PNG, puis STEP et STL dans `out/<nom>/`.
3. **Lire les PNG** (`iso`, `dessus`, `face`, `droite` : arêtes vues en noir, cachées en gris)
   avant d'annoncer qu'une pièce est prête. Les contrôles ne voient pas une erreur de forme.
4. Ouvrir `out/<nom>/<nom>.step` dans Bambu Studio (le STEP garde les courbes exactes ; le STL
   est là en secours).

`uv run generer` sans nom liste les pièces. Codes de sortie : 0 exporté, 1 la pièce échoue
(contrôle en ÉCHEC ou exception dans `construire()`), 2 erreur d'usage (nom inconnu ou
invalide, `construire()` absent). `out/<nom>/` est vidé à chaque run : après un échec il ne
contient que les PNG, jamais un STEP ou un STL d'une version précédente.

## Contrat d'une pièce

- `piece.py` expose `construire() -> Part` (build123d), sans effet de bord à l'import.
- Unités en mm, Z vers le haut, pièce posée sur Z = 0 dans son orientation d'impression.
- Une pièce = un seul solide. Un assemblage s'écrit en plusieurs pièces.
- `<nom>` : minuscules, chiffres et `_`, en commençant par une lettre.
- Les cotes se nomment en constantes en tête de fichier, jamais en dur dans la géométrie.
- Les briques communes viennent de `commun/` : `visserie` (perçages M2 à M5, passage et
  lamage), `jeux` (ajustements par matériau), `imprimante` (volumes).

## Contrôles de `generer`

ÉCHEC (pas d'export) : pas un `Part`, aucun solide, plusieurs solides, géométrie invalide,
volume nul, dépassement du volume de la buse principale. AVERTISSEMENT (export quand même) :
dépassement du volume de la buse auxiliaire, pièce non posée sur Z = 0. X et Y se comparent
triés : la pièce peut tourner de 90° sur le plateau.

## Concevoir pour l'impression

- Orienter la pièce pour que les efforts tirent le long des couches, pas entre elles.
- Surplombs au-delà de 45° : support, ou chanfrein à la place d'un congé sous une face.
- Paroi : au moins deux largeurs de buse. Un trou vertical sort plus petit que sa cote :
  appliquer le jeu du tableau.
- Arêtes posées sur le plateau : chanfrein plutôt que congé (patte d'éléphant).

## Jeux d'ajustement (au diamètre, mm)

Valeurs de DÉPART, pas des mesures sur cette X2D. Une ligne ne se tient pour acquise qu'avec
sa date de validation, obtenue en imprimant `eprouvette_jeux` (voir son `NOTES.md`). Garder ce
tableau et `commun/jeux.py` identiques.

| Matériau | Serré | Glissant | Libre | Validé le |
| --- | --- | --- | --- | --- |
| PLA | 0,10 | 0,20 | 0,30 | — |
| PETG | 0,15 | 0,25 | 0,35 | — |
| ABS | 0,15 | 0,25 | 0,35 | — |

## Vérifier avant de conclure

- `uv run pytest` : toute la suite.
- `uv run generer <nom>` sur chaque pièce touchée, puis lecture de ses PNG.
- `sh init.sh` après toute modification de `pyproject.toml`, `uv.lock` ou `init.sh`.

## Deux postes

Sur un poste neuf : cloner, puis `sh init.sh` (demande `uv` ; n'installe rien au niveau
système). Ensuite `git pull` avant de travailler ; relancer `sh init.sh` si `uv.lock` a changé.
`uv sync --locked` refuse un `uv.lock` qui ne correspond plus à `pyproject.toml` : après un
changement de dépendance, `uv lock` puis committer les deux fichiers ensemble.
