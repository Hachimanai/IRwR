# Concevoir pour l'impression

- Orienter la pièce pour que les efforts tirent le long des couches, pas entre elles.
- Surplombs au-delà de 45° : chanfrein à la place d'un congé sous une face, ou changer
  l'orientation. Le support, faute de seconde buse (`docs/imprimante.md`), sort dans la matière
  de la pièce : à éviter, il marque les faces et se retire mal dans les creux.
- Le support se génère dans Bambu Studio, jamais dans le code : modélisé, il ferait partie du
  solide, sans l'écart en Z ni l'interface qui le rendent détachable. Le code l'évite
  (orientation, chanfreins, couche sacrificielle sur un trou ou un lamage, toit en goutte) ;
  le `NOTES.md` dit si la pièce en demande et où, à activer ou peindre dans Bambu Studio.
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
