# Imprimante : Bambu Lab X2D

- **Une seule buse en service (depuis le 2026-10-14) : la buse principale, à gauche.** La buse
  auxiliaire (droite) ne s'utilise pas pour l'instant : ni support dans un matériau dédié, ni
  seconde matière. Une pièce se conçoit donc pour une impression mono-matière.
- Volume buse principale : 256 × 256 × 260 mm, contrôlé par `generer`. Volume buse auxiliaire :
  235,5 × 256 × 256 mm, gardé dans `commun/imprimante.py` mais plus contrôlé.
- Double buse, pour mémoire : la principale (direct drive) porte la matière, l'auxiliaire
  (Bowden) est prévue pour le support. Quand elle reviendra en service, rétablir son
  avertissement de volume dans `atelier/controles.py` et assouplir la règle des surplombs
  (`docs/conception.md`).
- Buses disponibles : 0,2 mm, 0,4 mm (par défaut), 0,6 mm et 0,8 mm. La 0,2 rend les détails
  fins (gravures, arêtes minces, petits filetages) au prix d'un temps d'impression bien plus
  long ; la 0,6 et la 0,8 impriment vite et solide les pièces massives sans détail fin. Le
  diamètre monté se choisit dans le profil d'imprimante de Bambu Studio ; il borne les détails
  et les parois fines (`docs/conception.md`).
- Température maximale de buse : 300 °C ou 350 °C selon les sources, non tranché. À lire sur
  la fiche de la machine avant de viser un matériau technique.

## Bambu Studio

Installé en Flatpak (`com.bambulab.BambuStudio`). Pour ouvrir un export depuis le terminal,
détaché du shell pour que la fenêtre survive à la commande :

```sh
setsid -f flatpak run com.bambulab.BambuStudio "$PWD/out/<nom>/<nom>.step"   # .stl pour Blender
```

Le chemin doit être absolu. Le profil, le filament et le tranchage se font dans Bambu Studio ;
rien n'est envoyé à l'imprimante depuis le dépôt.

Un projet enregistré (`.3mf`) peut se poser dans `pieces/<nom>/` pour être relu : c'est une
archive zip (réglages dans `Metadata/project_settings.config`, ceux changés par rapport au
profil dans sa clé `different_settings_to_system`). Il ne se versionne pas (`.gitignore`) :
il pèse surtout son maillage, qui se régénère. Les réglages retenus se recopient dans le
`NOTES.md` de la pièce.
