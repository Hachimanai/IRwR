# Corbeille de tri

Bac hexagonal ouvert pour apprendre à trier par couleur : une même pièce, imprimée une fois
par couleur, le filament se choisit dans Bambu Studio. Les bacs vides s'emboîtent, et vus de
dessus ils se posent côte à côte en nid d'abeille.

## Cotes

Pas d'interface avec une autre pièce : aucune cote mesurée. Choix de l'utilisateur
(2026-10-19) : taille moyenne (~150 mm, pour Duplo, voitures, balles), forme hexagonale,
bacs gigognes.

- 150 mm entre plats en haut (169 mm entre sommets), 80 mm de haut.
- Dépouille de 8° : en bas, environ 128 mm entre plats.
- Emboîtement : un bac posé dans un autre dépasse d'environ 17,5 mm (contrôlé par
  intersection, nulle à partir de 17,5 mm). Une pile de quatre fait donc environ 133 mm.

## Hypothèses

- PLA.
- Paroi de 2,4 mm (normale à la paroi), fond de 2 mm.
- Coins verticaux arrondis à R12, congé intérieur fond/paroi de R8 (facile à vider), bord
  du haut arrondi à R1,1, chanfrein de 0,8 mm au pied (patte d'éléphant).
- Les parois emboîtées sont parallèles : deux bacs peuvent se coincer légèrement. Si c'est
  gênant, ajouter du jeu (plats en haut un peu plus grands que la cavité ne le demande) ou
  trois petites butées.

## Impression

PLA, ouverture vers le haut, **aucun support**. 120 cm³, soit environ 150 g de PLA par bac.
Un bac par plateau (169 × 150 mm).
`generer` mesure 3,4 cm² de surplomb entre Z 0,3 et 0,5 mm : c'est le chanfrein du pied,
incliné à ≈ 49° par la dépouille, sur 0,8 mm de haut. Il s'imprime sans support.

Projet Bambu Studio relu le 2026-10-19 (`COMPOUND.3mf`, non versionné) :

- profil de départ : 0.20mm High Quality @BBL X2D, plateau Textured PEI ;
- filament : Bambu PLA Pure, extrudeur 1 (buse principale) ; la couleur change à chaque bac ;
- modifié par rapport au profil : **6 parois** (paroi de 2,4 mm pleine), **10 couches de
  fond** (fond de 2 mm plein), `enable_arc_fitting` ;
- le reste par défaut : remplissage gyroïde 15 % (sans objet, tout est plein), bordure auto,
  aucun support.

## Tirages

| Date | Matériau | Buse / couche | Remarques |
| --- | --- | --- | --- |
|  |  |  |  |
