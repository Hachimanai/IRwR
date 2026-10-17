# Détente (gachette)

Reproduction d'une détente en plastique moulé, fissurée au pied de sa chape (la fissure suit
le fond de la fente, du pivot vers le bas de la plaque). Filière build123d (`piece.py`).
Mesuré par `generer` : 50,2 × 44,3 × 8,5 mm, 4,52 cm³.

## S'assemble avec

- **Axe de pivot** : traverse le bossage et les deux joues de la chape. Trou de 3,5 mm comme
  l'original ; l'axe est un peu plus petit et tourne sans forcer (indication de l'utilisateur,
  2026-10-17).
- **Gâchette**, épaisseur 3,4 : se loge dans la fente de la chape (plan médian, ouverte sur le
  dos de la plaque et autour du pivot). Fente à 3,65 (jeu glissant ; 3,5 sur l'original).
- **2 vis M3 métal** de réglage : vissées depuis la face avant (côté lame), elles débouchent
  au fond de la fente et appuient sur la gâchette. Elles sont perpendiculaires à la face
  avant et au fond de la fente, parallèles entre eux (indication de l'utilisateur). Taraudage direct Ø 2,5 mm dans le PETG.
- **`gachette_rondelle`** : remplace le bossage côté plateau, à enfiler sur l'axe sous la
  détente (choix du 2026-10-17 : la détente pose ainsi à plat ; sur la tranche, les couches
  croiseraient l'effort du levier).

## Cotes

Mesurées au pied à coulisse le 2026-10-17, sur l'original fissuré (repères de la planche
`cotes_gachette.png`, non versionnée) :

| N° | Cote | Constante | Mesure | Dans la pièce |
| --- | --- | --- | --- | --- |
| 1 | Ø du trou du pivot | `DIAMETRE_ALESAGE` | 3,5 | 3,5 (l'axe est plus petit) |
| 2 | Épaisseur de la gâchette | `EPAISSEUR_GACHETTE` | 3,4 | |
| 3 | Largeur de la fente | `LARGEUR_FENTE` | 3,5 | 3,65 (gâchette + jeu glissant) |
| 4 | Épaisseur du corps | `EPAISSEUR` | 6,8 | joues de 1,58 |
| 5 | Hors tout aux bossages | `SAILLIE_BOSSAGE` | 10,2 | saillie 1,7 de chaque côté |
| 6 | Ø du bossage | `DIAMETRE_BOSSAGE` | 9,0 | |
| 7 | Ø des trous de vis | `DIAMETRE_TROU_ORIGINE` | 2,4 | taraudage 2,5 (perçage M3) |
| 8 | Arête du haut de la face avant → bord du trou de la vis haute | `ARETE_VIS` | 3,4 | centre à 4,6 le long de la face |
| — | Entraxe des vis | `ENTRAXE_VIS` | 6,0 | |
| 9 | Profondeur de la fente, du dos au fond | `PROFONDEUR_FENTE` | 7,5 (6,2 d'abord, mal lu) | contrôle : 8,1 entre les vis, 7,5 en haut |
| 10 | Téton : Ø, saillie | `TETON_DIAMETRE`, `TETON_SAILLIE` | 3,4 ; 2,6 | |
| 11 | Longueur hors tout | `LONGUEUR` | 50,2 | |
| 12 | Hauteur hors tout | `HAUTEUR` | 44,3 | |

Le **contour** reste relevé point par point sur la photo à plat `PXL_20261017_080437419.jpg`
(mètre ruban dans le plan, ±0,5 mm), puis recalé par `ECHELLE_X` = 0,967 et `ECHELLE_Y` =
0,952 pour tomber sur les cotes 11 et 12 : la photo le sortait 3 à 5 % trop grand.

**Géométrie imposée** (indications de l'utilisateur, 2026-10-17) : le bossage est tangent au
dos de la plaque et au pan supérieur, sans déport ; le fond de la fente est parallèle à la
face avant et descend jusqu'à l'arête du cran (sous la plaque), où il débouche.

Le fond n'est pas exactement parallèle au dos (4° d'écart) : la profondeur passe de 8,4 au
pied à 7,5 en haut de la fente, ce qui recoupe la mesure 9.

## Hypothèses

- Contour en segments droits et faces planes, sauf la lame (une courbe), le pivot, le téton
  et les vis (indication de l'utilisateur, 2026-10-17). Coins vifs, y compris celui de la
  plaque qui paraissait arrondi sur la photo.
- Épaisseur uniforme de 6,8 mm, crochet compris.
- Fente centrée dans l'épaisseur.
- Face du cran verticale, à la position relevée sur la photo.
- Vis perpendiculaires à X (horizontales), taraudages jusqu'à 1 mm dans la fente.
- Téton cylindrique (section ronde) centré dans l'épaisseur, à la hauteur relevée sur la photo.
- Taraudages et téton ronds, pas en goutte (demande du 2026-10-17) : le haut des trous et
  le dessous du téton peuvent s'affaisser d'un rien, sans gêne à ces diamètres.
- Marques d'éjecteur non reproduites. Pas de chanfrein au plateau (retiré à la demande de
  l'utilisateur, 2026-10-17) : surveiller la patte d'éléphant, compensable dans Bambu Studio.
- Le fond de chape reste vif, comme l'original : si la nouvelle pièce casse au même endroit,
  arrondir ce fond ou épaissir les joues (1,58 mm, contre 1,65 sur l'original).

## Impression

- PETG, posée à plat sur le flanc sans bossage (Z = 0), bossage vers le haut.
- **Support à peindre dans la fente** de la chape : le plafond de la fente (joue du dessus)
  est en porte-à-faux sur ≈ 6 mm, ouvert sur trois côtés. Support normal, peint uniquement
  dans la fente ; il se retire par le flanc arrière. Rien ailleurs : taraudages et téton, de
  petit diamètre, s'impriment sans.
- Tarauder les M3 à la main (ou visser doucement, la vis forme son filet dans le PETG).

## Tirages

| Date | Matériau | Buse / couche | Remarques |
| --- | --- | --- | --- |
| 2026-10-17 | PETG | | Pièce déclarée terminée par l'utilisateur ; détails du tirage non relevés |

## Photos

Les 11 photos de l'original (à plat avec mètre ruban, de bout, de face) sont archivées dans
`photos.tar`, réduites à 3000 px (`docs/images.md`). Pour les relire :
`tar -xf pieces/gachette/photos.tar -C pieces/gachette`.
