# Images d'entrée d'une pièce

Les photos, croquis et captures qui servent à modéliser une pièce vivent dans
`pieces/<nom>/photos/` et se versionnent avec elle.

## Compresser avant de pousser

Une photo de téléphone (≈ 8000 px, 4 à 7 Mo) est plus grande que ce que Claude lit : l'outil de
lecture la réduit de toute façon, et le dépôt grossit pour rien. Avant le commit, chaque image
trop grosse se ramène à ce qui suffit au traitement :

- **3000 px sur le grand côté** : assez pour relever une cote à ±0,5 mm sur une photo avec
  règle dans le plan (≈ 12 px/mm pour une pièce de 5 cm qui remplit le tiers du cadre) ;
- **JPEG qualité 85**, orientation EXIF appliquée ;
- **métadonnées retirées** (`-strip`) : les photos de téléphone portent la position GPS.

```sh
for f in pieces/<nom>/photos/*.jpg; do
  magick "$f" -auto-orient -resize '3000x3000>' -quality 85 -strip "$f"
done
```

Une image déjà plus petite que 3000 px n'est pas agrandie (`>`). La compression écrase
l'original : la faire sur une copie si l'utilisateur veut garder la pleine résolution
ailleurs. Noms de fichiers sans espace (`photos/`, pas `Photos-1-001 (1)/`).

Pour une mesure plus fine que ce que donnent 3000 px, Claude recadre la zone utile dans
l'original avant compression, le temps du relevé : le recadrage ne se versionne pas.

## Archiver une fois la pièce terminée

Une pièce est terminée quand un tirage est validé dans le tableau « Tirages » de son
`NOTES.md` et que l'utilisateur le confirme. Les images rejoignent alors une archive unique :

```sh
tar -cf pieces/<nom>/photos.tar -C pieces/<nom> photos && rm -r pieces/<nom>/photos
```

Sans compression : les JPEG le sont déjà. `NOTES.md` dit quelles photos ont servi et que
`photos.tar` les contient. Si la pièce est reprise, on désarchive
(`tar -xf pieces/<nom>/photos.tar -C pieces/<nom>`) avant de lire.
