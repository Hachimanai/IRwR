# Range-épices 4 × 5 — bloc droit

Les **2 colonnes de droite** du range-épices 4 × 5 : modules `Middle_4x1` + `Right_4x1` du kit
« Yet another Spice Rack V2 » (Johann Arndt) fusionnés. Il se glisse par son flanc gauche
(queue d'aronde du kit) dans `range_epice_gauche`, en glissant vers l'avant et le haut à 15°
depuis l'arrière et le dessous du bloc gauche. Boîte ouverte sur l'avant comme le bloc gauche
(fond, dos, côté droit, dessus, un pilier à l'avant côté joint, plaque avant sous la
rangée du bas). Pourquoi deux blocs, boîte, source des cotes et
licence : voir `pieces/range_epice_gauche/NOTES.md`.

## Cotes

- Entraxe d'emboîtement milieu–droite relevé sur les maillages : 54,4 mm.
- Bloc avec sa boîte : 111,5 × 251,6 × 97 mm (en impression), 531 cm³.

## Glissière : jeu agrandi (2026-10-28)

Premier tirage : les rails du flanc gauche entraient trop serrés dans les rainures du bloc
gauche, la pièce a cassé au montage forcé. Le kit ne laisse que 0,08 mm (crochet de la queue
d'aronde) à 0,10 mm (côtés du rail) par face, un ajustement glissant que le créateur réserve à
une imprimante très bien calibrée.

Correction sur ce bloc seulement (le bloc gauche imprimé reste bon) : rails amincis de
`JEU_RAILS` = 0,2 mm sur chaque face (`rails_amincis` dans `pieces/range_epice/kit.py`, sur le
vrai maillage : la tête de la queue d'aronde est plus large que son col). Contrôlé en position
assemblée : chevauchement nul, jeu de 0,30 à 0,32 mm par face dans les trois directions, la
queue d'aronde accroche toujours si on écarte les blocs, chemin de glissement à 15° libre.
Si c'est encore dur, monter `JEU_RAILS` ; si ça flotte, le baisser.

**Pentes d'entrée retournées (2026-10-28, remarque de l'utilisateur).** Dans le kit, chaque
rail (23 mm le long de la pente) porte sa longue pente d'entrée (≈ 3 mm, la saillie descend de
3 à 0) au bout arrière-bas, et un simple chanfrein de 0,5 mm au bout avant-haut. Or sur le seul
chemin de montage, le bloc droit arrive par l'arrière et le bas : c'est le bout avant-haut qui
attaque la rainure. Chaque rail aminci est donc retourné bout pour bout (symétrie par le plan
⟂ au chemin, au milieu du rail ; `_retourner_rails` dans `kit.py`) : section, longueur et jeu
inchangés. Contrôlé sur l'export : pente de 2,4 mm au bout d'entrée des 8 rails, chevauchement
nul en position, jeu ≈ 0,3 mm en travers, accroche conservée, chemin à 15° libre (le sens
inverse cogne).

**Arêtes non manifold (2026-10-28).** Bambu Studio en signalait 25 sur ce bloc. Après les
booléens, les sommets à moins de 0,1 µm sont recollés et les arêtes plus courtes dissoutes
(`SOUDURE` dans `kit.py`) : il en reste 13 dans le STL (recollé comme un trancheur), toutes des
pincements de 0,002 à 0,06 mm sur les rails, où l'amincissement réduit à rien les plus petits
arrondis, et une au fond. Trop petites pour le trancheur (résolution 0,012 mm) ; le bloc gauche,
imprimé avec une vingtaine de ces arêtes, est sorti correctement. Fermer les pincements par
union avec des copies décalées de quelques µm a été essayé et écarté (pièce scindée).

## Hypothèses

- Fusion à 0,1 mm de recouvrement (`FUSION`) et boîte (`HAUT_BOITE`, `PAROI` repris du bloc
  gauche), comme le bloc gauche.
- PLA.
- `JEU_RAILS` = 0,2 mm par face, au-delà du jeu « libre » du PLA (`docs/conception.md`,
  0,30 au diamètre) : le jeu glissant du kit a cassé la pièce.

## Impression

Posé sur le dos de la boîte, avant ouvert vers le haut, 97 mm de haut, **aucun support**, un
bloc par plateau. Surplomb de 26 cm² (design d'origine, et le pilier en pont d'≈ 55 mm) et
parois minces (2,2 % sous 0,8 mm, sur les rails) : voir `range_epice_gauche`.

Réglages Bambu Studio : les mêmes que `range_epice_gauche` (même projet).

## Tirages

| Date | Matériau | Buse / couche | Remarques |
| --- | --- | --- | --- |
| 2026-10-28 | PLA Basic | 0,4 / 0,2 (Standard, 4 parois) | Rails trop serrés dans les rainures du bloc gauche : montage forcé, **pièce cassée**. Jeu des rails agrandi de 0,2 mm par face. |
|  |  |  |  |
