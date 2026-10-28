# Détente (gachette)

Reproduction d'une détente en plastique moulé, fissurée au pied de sa chape (la fissure suit
le fond de la fente, du pivot vers le bas de la plaque). Filière build123d (`piece.py`).
Mesuré par `generer` : 51,9 × 46,5 × 9,15 mm, 5,74 cm³.

## S'assemble avec

- **Axe de pivot** : traverse le bossage et les deux joues de la chape. Ø supposé 4 mm,
  alésage à 4,25 mm (jeu glissant PETG).
- **Gâchette** : se loge dans la fente de la chape (plan médian, ouverte sur le flanc arrière
  et autour du pivot).
- **2 vis M3 métal** de réglage : vissées depuis la face avant (côté lame), elles débouchent
  dans la fente et appuient sur la gâchette. Taraudage direct Ø 2,5 mm dans le PETG.
- **`gachette_rondelle`** : remplace le bossage côté plateau, à enfiler sur l'axe sous la
  détente (choix du 2026-10-17 : la détente pose ainsi à plat ; sur la tranche, les couches
  croiseraient l'effort du levier). Une rondelle métal M4 DIN 125 (Ø 9 × 0,8) peut la
  remplacer si 0,35 mm de jeu latéral en plus est acceptable.

## Cotes

**Aucune cote n'est mesurée au pied à coulisse** (2026-10-17) : tout vient des photos
`Photos-1-001 (1)/` avec un mètre ruban posé dans le plan (34,3 px/mm sur la photo à plat
`…080437419.jpg`), à ±0,5 mm au mieux. La face du dessus, plus haute que le ruban, ressort
de 1 à 3 % trop grande sur la photo : non corrigé. À reprendre dès qu'un pied à coulisse est
là, dans cet ordre (les premières sont des interfaces) :

| Cote                        | Constante                             | Valeur actuelle                   | D'où                                                                                           | À mesurer                                                                |
| --------------------------- | ------------------------------------- | --------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| Ø de l'axe de pivot         | `DIAMETRE_AXE`                        | 4,0                               | alésage ≈ 3,9-4,0 sur photo                                                                    | l'axe lui-même                                                           |
| Largeur de la fente         | `LARGEUR_FENTE`                       | 3,2                               | vue de bout, ratio sur l'épaisseur                                                             | fente, et épaisseur de la gâchette                                       |
| Épaisseur du corps          | `EPAISSEUR`                           | 8,0                               | photo de tranche avec ruban                                                                    | flanc à flanc, hors bossage                                              |
| Saillie du bossage          | `SAILLIE_BOSSAGE`                     | 1,15                              | idem (10,3 hors tout)                                                                          | hors tout aux bossages − épaisseur, ÷ 2                                  |
| Ø du bossage                | `DIAMETRE_BOSSAGE`                    | 9,3                               | photo à plat                                                                                   |                                                                          |
| Entraxe des vis             | `ENTRAXE_VIS`                         | 6,0                               | mesuré par l'utilisateur, centre à centre (2026-10-17)                                         | —                                                                        |
| Hauteur de la vis basse (Y) | `Y_VIS_BAS`                           | 27,0                              | choisie : la photo (28,6) mettait la vis haute dans l'arête de la face avant ; paroi de 1,5 mm | distance du centre de la vis haute à l'arête supérieure de la face avant |
| Fond de chape               | `FENTE_FOND`, `FENTE_BAS`             | ligne (12,5 ; 24,4) → (19,5 ; 47) | tracé de la fissure                                                                            | profondeur de la fente depuis le flanc arrière                           |
| Téton                       | `TETON_*`                             | Ø 3,3, saillie 2,8                | photo à plat                                                                                   |                                                                          |
| Contour                     | `CONTOUR_DOS`, `LAME`, `CONTOUR_PIED` | relevé point par point            | photo à plat quadrillée                                                                        | longueur hors tout ≈ 51,9, hauteur ≈ 46,5                                |

## Hypothèses

- Contour en segments droits et faces planes, sauf la lame (une courbe), le pivot, le téton
  et les vis (indication de l'utilisateur, 2026-10-17). Coins vifs, y compris celui de la
  plaque qui paraissait arrondi sur la photo.
- Épaisseur uniforme de 8 mm, crochet compris (il paraît plus mince, ≈ 6,5 mm, sur la photo
  de tranche).
- Joues de la chape de 2,4 mm chacune, fente centrée.
- Vis perpendiculaires à X (horizontales), taraudages jusqu'à 1 mm dans la fente.
- Téton cylindrique (section ronde) centré dans l'épaisseur.
- Taraudages et téton ronds, pas en goutte (demande du 2026-10-17) : le haut des trous et
  le dessous du téton peuvent s'affaisser d'un rien, sans gêne à ces diamètres.
- Marques d'éjecteur non reproduites. Pas de chanfrein au plateau (retiré à la demande de
  l'utilisateur, 2026-10-17) : surveiller la patte d'éléphant, compensable dans Bambu Studio.
- Le fond de chape reste vif, comme l'original : si la nouvelle pièce casse au même endroit,
  arrondir ce fond ou épaissir les joues.

## Impression

- PETG, posée à plat sur le flanc sans bossage (Z = 0), bossage vers le haut.
- **Support à peindre dans la fente** de la chape : le plafond de la fente (joue du dessus)
  est en porte-à-faux sur ≈ 10 mm, ouvert sur trois côtés. Support normal, peint uniquement
  dans la fente ; il se retire par le flanc arrière. Rien ailleurs : taraudages et téton, de
  petit diamètre, s'impriment sans.
- Tarauder les M3 à la main (ou visser doucement, la vis forme son filet dans le PETG).

## Tirages

| Date | Matériau | Buse / couche | Remarques |
| --- | --- | --- | --- |
|  |  |  |  |
