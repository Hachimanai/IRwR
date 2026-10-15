---
name: nouvelle-piece
description: >-
  Démarre ou reprend une pièce à imprimer dans IRwR, à partir d'une description, d'images
  (photos, croquis, captures, pièce cassée à remplacer) ou d'un tirage raté : relit les entrées,
  pose d'un coup les questions qui manquent, s'arrête en cours de route quand une cote qui compte
  devient ambiguë, puis génère et compare les vues aux images. À utiliser dès que l'utilisateur
  demande de créer, modéliser, dessiner, reproduire ou adapter une pièce (« fais-moi un support »,
  « imprime-moi », « voici une photo de… », « la pièce ne rentre pas »), même sans dire « pièce »
  ni nommer la filière.
---

# Nouvelle pièce

Une cote devinée se paie en heures d'impression et en filament : une question coûte une
minute. Cette skill sert à savoir **ce qui manque avant de modéliser**, et à le redemander
**dès que ça manque en cours de route**, sans pour autant noyer l'utilisateur de questions sur
ce qu'on peut décider seul.

Les règles du dépôt sont dans `CLAUDE.md` et `docs/` : cette skill ne les répète pas, elle
s'appuie dessus. Avant de modéliser, lire `docs/contrat-piece.md` et `docs/conception.md`
(orientation, surplombs, parois, jeux d'ajustement).

## 1. Lire les entrées

**Images.** Une image collée se lit directement ; un chemin donné se lit avec Read. Pour
chacune, dire en deux ou trois lignes ce qu'on y voit : forme, nombre de trous, faces
visibles, ce qui est caché. Cette reformulation fait remonter un malentendu avant qu'il coûte
un tirage.

Ce qu'une image donne et ne donne pas :

- **Sans référence d'échelle** (règle, pied à coulisse, objet de taille connue), une photo
  donne des proportions, jamais une cote. Le dire.
- **En perspective**, les proportions mêmes sont faussées : une photo prise de biais ne se
  mesure pas. Une vue de face, appareil parallèle à la surface, avec une règle posée dans le
  même plan, se mesure à ±1 mm au mieux ; un ajustement (trou, emboîtement) demande le pied à
  coulisse.
- **Un croquis coté** vaut ce que valent ses cotes : relever celles qui y sont, repérer celles
  qui manquent ou se contredisent (somme des cotes partielles ≠ cote totale).
- **Une pièce cassée à reproduire** : demander les cotes sur la pièce, pas sur la photo, et
  ce sur quoi elle se monte (c'est souvent là qu'est la cote critique).
- **Un tirage raté** : chercher sur la photo l'indice (couches décollées, surplomb affaissé,
  trou trop serré, patte d'éléphant) avant de proposer une correction.

## 2. Trier ce qui manque

Classer chaque information manquante :

**Bloquante** — fausse, elle oblige à réimprimer. On la demande, on ne la devine pas :

- les cotes d'interface : tout ce qui touche une autre pièce (diamètre d'un tube, entraxe de
  fixation, épaisseur d'une planche, taille d'une vis) ;
- la filière, si l'utilisateur ne l'a pas nommée (règle de `CLAUDE.md`), avec une
  recommandation ;
- le matériau quand la pièce a un ajustement ou une contrainte (chaleur, extérieur, charge) ;
- le sens de l'effort quand la pièce porte quelque chose : il fixe l'orientation d'impression ;
- une contradiction dans les entrées.

**Secondaire** — on décide seul, avec une valeur raisonnable, et on l'écrit comme hypothèse :
épaisseurs non fonctionnelles, rayons de congé, chanfreins, dimensions purement esthétiques,
nombre de nervures. Une hypothèse se signale à l'utilisateur et se note dans `NOTES.md`
(section « Hypothèses ») : il peut la corriger sans avoir à deviner ce qu'on a choisi.

## 3. Poser les questions d'un coup

Toutes les questions bloquantes partent ensemble, dans un seul message, avant d'écrire du
code. Les poser une à une fait perdre un aller-retour par question.

- Choix discrets (filière, matériau, orientation) : `AskUserQuestion`, recommandation en
  première option.
- Cotes : question ouverte, en disant **où** et **comment** mesurer (« l'entraxe des deux trous,
  centre à centre, au pied à coulisse »). Si une photo de plus aide, dire laquelle (vue de face,
  règle dans le plan).
- Proposer une valeur par défaut quand il y en a une sensée (« sinon je pars sur 3 mm »), pour
  que l'utilisateur puisse répondre « ok ».
- Joindre les hypothèses secondaires déjà prises, en une liste courte : l'utilisateur les voit
  passer et réagit s'il veut.

Rien ne manque de bloquant : ne rien demander, annoncer les hypothèses et construire.

## 4. Construire, et s'arrêter quand il le faut

Écrire `pieces/<nom>/` selon `docs/contrat-piece.md` : cotes en constantes nommées en tête de fichier, et
`NOTES.md` avec les cotes reçues (d'où elles viennent : mesure, croquis, photo), les
hypothèses, ce avec quoi la pièce s'assemble, et les supports à activer ou peindre dans
Bambu Studio (ou « aucun »).

En cours de route, une question nouvelle peut surgir : deux cotes incompatibles (un trou M4 à
2 mm du bord d'une patte de 6 mm), une face que les images ne montrent pas et qui porte une
fonction, un surplomb impossible sans changer une cote fixée par l'utilisateur, un volume qui
dépasse la buse. Si elle est **bloquante** au sens du §2 : s'arrêter, dire ce qui coince,
proposer deux ou trois options chiffrées avec une recommandation, et attendre. Le reste se
tranche seul et rejoint la liste des hypothèses.

## 5. Vérifier contre les images

`uv run generer <nom>`, puis lire les PNG comme le dit `docs/generer.md`. Quand l'utilisateur a
fourni des images, comparer la vue qui leur correspond (photo de face ↔ `face`, croquis vu de
dessus ↔ `dessus`) et citer les écarts : un trou mal placé, une proportion différente. Un
écart voulu (correction d'un défaut, simplification) se dit aussi.

## 6. Conclure

En quelques lignes :

- dimensions et volume mesurés par `generer` ;
- les hypothèses à confirmer, s'il en reste ;
- le fichier à ouvrir ; proposer de l'ouvrir dans Bambu Studio (commande dans
  `docs/imprimante.md`) ;
- après l'impression, demander le résultat pour remplir le tableau « Tirages » de `NOTES.md`.

Rien ne se committe sans demande explicite.
