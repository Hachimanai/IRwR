# Range-épices 4 × 5 — bloc gauche

Range-épices de 4 rangées × 5 colonnes (20 pots de Ø 45 mm), en deux blocs qui s'emboîtent :
ce bloc porte les **3 colonnes de gauche**, `range_epice_droite` les 2 de droite. Le design est
celui du kit « Yet another Spice Rack V2 (Modular & Stackable) » de Johann Arndt (MakerWorld),
pris tel quel : modules `Left_4x1` + 2 × `Middle_4x1` fusionnés (`pieces/range_epice/kit.py`).
Une boîte l'entoure, ouverte seulement sur l'avant (demande du 2026-10-21) : fond, dos, côté
gauche, dessus relevé au-dessus de la rangée du haut, plaque avant sous la rangée du bas.

## Pourquoi deux blocs

Assemblé d'un seul tenant, le 4 × 5 mesure 270 × 97 × 199 mm : couché sur le flanc il dépasse
les 260 mm de haut, debout il ne passe pas en diagonale (259,5 mm pour un plateau de 256).
Choix de l'utilisateur (2026-10-21) : deux blocs fusionnés, une seule glissière, celle du kit.

## Cotes

Aucune mesure : toutes viennent des maillages du créateur (`pieces/range_epice/ModularParts.3mf`,
non versionné, licence Standard Digital File License : usage personnel, pas de
redistribution du maillage). La pièce ne se régénère que sur un poste qui a ce fichier.

- Module 4 rangées : 97 mm de profondeur, 199,2 mm de haut, pas de 54 mm entre rangées.
- Entraxes d'emboîtement relevés sur les maillages (recouvrement nul, la queue d'aronde
  accroche dès 0,1 mm d'écart) : gauche–milieu 52,9 mm, milieu–milieu 52,55 mm.
- Bloc avec sa boîte : 161,1 × 251,6 × 97 mm (en impression), 750 cm³. Assemblé :
  270 × 251,6 × 97 mm (largeur × hauteur × profondeur en usage).

## Boîte

- Parois de 3 mm (`PAROI`), dans l'emprise du kit : fond, dos et côtés n'élargissent rien.
- **Rangée du haut** : le dessus monte à 152 mm au-dessus du centre du kit (`HAUT_BOITE`),
  soit 59 à 62 mm libres à l'aplomb de l'avant de la tablette du haut, contre 50 à 52 mm sous
  la tablette voisine pour les autres rangées : un pot s'y pose et s'y reprend plus facilement
  qu'ailleurs, et derrière, sous le dessus plat, la place grandit encore (la tablette descend
  vers le dos). Plus haut, l'empreinte dépasserait le plateau (251,6 mm sur 256).
- Pas de cloison sous le dessus (plaques retirées à la demande de l'utilisateur, 2026-10-21) :
  à la place, **un pilier** de 3 × 8 mm au bout libre du dessus (côté joint entre blocs, à
  l'avant), du haut du flanc (Z kit 89, au-dessus du rail le plus haut) au dessus, dans
  l'épaisseur du flanc. Le dessus tient donc par le dos, le côté extérieur et ce pilier. En
  impression, le pilier est en haut de la pièce, en pont (voir « Impression »).
- **Plaque avant du bas** (demande du 2026-10-21) : 3 mm d'épaisseur, du plateau au dessous
  de la tablette du bas (Z kit -75,5, relevé sur les trois modules), elle ferme l'interstice
  de ≈ 20 mm entre le fond et cette tablette sans dépasser au-dessus (les pots n'y butent pas).
  Elle referme aussi le coin sous la tablette du bas de chaque colonne : ces coins sont
  remplis (voir plus bas), soit ≈ 100 cm³ de volume en plus, imprimés en remplissage (≈ 20 g
  de PLA à 15 %).
- **Glissière préservée** : le seul chemin de montage du kit (relevé sur les maillages) fait
  glisser le bloc droit vers l'avant et le haut à 15°, en entrant par le dos et le dessous de
  la rainure. Le fond et le dos vont jusqu'au flanc droit (demande du 2026-10-21 : pas de
  trou au joint) et ne sont percés que du passage de chaque rail le long de ce chemin, avec
  0,3 mm de jeu (`passage_rails`). Contrôlé : recouvrement nul tout le long du chemin, et la
  queue d'aronde accroche toujours.
- Les fentes de glissière entre modules fusionnés, refermées par le fond et le dos, sont
  remplies (sinon bulles d'air fermées) : flancs pleins à ces endroits.

## Hypothèses

- Modules fusionnés avec 0,1 mm de recouvrement (`FUSION`) : l'union de flancs coplanaires
  est fragile. Le bloc est 0,2 mm plus étroit que trois modules emboîtés.
- Les rainures de la queue d'aronde restent aux joints fusionnés : petites encoches au dos
  (vue `dessus`, X ≈ 26 et 79), sans effet.
- PLA, comme le recommande le créateur.

## Impression

**Posé sur le dos de la boîte** (demande de l'utilisateur, 2026-10-21), 97 mm de haut, avant
ouvert vers le haut. Le créateur, sans boîte, pose l'avant sur le plateau ; ici le dos serait
alors la dernière couche, en pont sur toute la largeur (407 cm² de surplomb mesurés). Retourné,
le dos est la première couche, les arrondis en U des flancs s'ouvrent vers le haut, fond, côté
et dessus restent des parois verticales. **Aucun support**. Un bloc par plateau (161 × 252 mm).

`generer` mesure 51 cm² de surplomb, du même ordre que le design d'origine (un module seul :
19 à 24 cm²) : butées des tablettes, rails et arrondis. Le pilier, en haut de la pièce, est un
pont de 3 mm de large sur ≈ 55 mm, entre le haut du flanc et le dessus : à regarder au premier
tirage. Parois sous 0,8 mm (2,4 %) : celles du design d'origine (paroi min 0,18 mm sur un
module seul).

Réglages du projet du créateur (relus le 2026-10-21) : couche 0,2 mm, 2 parois, remplissage
15 %, bordure auto. Il insiste sur une imprimante bien calibrée pour la glissière.

Projet Bambu Studio retenu (`pieces/range_epice_droite.3mf`, non versionné, les deux blocs,
un par plateau ; relu le 2026-10-21) :

- profil 0.20mm Standard @BBL X2D, buse 0,4, plaque Textured PEI, Bambu PLA Basic, extrudeur 1 ;
- modifié : **4 parois** (panneaux de 3 mm pleins en parois, dessus rigide), **sans bordure**
  (le dos posé à plat, ≈ 400 cm², suffit ; les blocs arrivent à 2 mm du bord du plateau),
  arc fitting désactivé ;
- par défaut : remplissage grille 15 %, aucun support, 5 couches dessus / 3 dessous.
- Pilier, temps et masse vérifiés dans l'aperçu du tranchage : conformes.

## Tirages

| Date | Matériau | Buse / couche | Remarques |
| --- | --- | --- | --- |
| 2026-10-28 | PLA Basic | 0,4 / 0,2 (Standard, 4 parois) | Imprimé. Le bloc droit, trop serré, a cassé au montage : corrigé sur le bloc droit seul (voir son `NOTES.md`), celui-ci se garde. |
|  |  |  |  |
