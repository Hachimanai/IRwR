"""Range-épices 4 × 5, bloc gauche : 3 colonnes de 4 pots, d'un seul tenant, dans sa boîte.

Le design du kit « Yet another Spice Rack V2 » tel quel (voir `pieces/range_epice/kit.py`) :
module gauche + 2 milieux fusionnés. Le flanc droit garde la queue d'aronde du kit et reçoit
`range_epice_droite`. Une boîte ouverte sur l'avant l'entoure : fond, dos, côté gauche et un
dessus relevé au-dessus de la rangée du haut.
"""

from pieces.range_epice.kit import (
    ENTRAXE_GAUCHE_MILIEU,
    ENTRAXE_MILIEU_MILIEU,
    FLANC_DROIT,
    FLANC_GAUCHE,
    FUSION,
    bloc,
    boite,
    passage_rails,
)

RANGEES = 4
# Z du kit sur le dessus de la boîte : 59 à 62 mm libres au-dessus de l'avant de la tablette du
# haut, contre 50 à 52 sous la tablette voisine pour les autres rangées. 251,6 mm d'empreinte
# sur le plateau (256).
HAUT_BOITE = 152.0
PAROI = 3.0


def construire():
    milieu_1 = ENTRAXE_GAUCHE_MILIEU - FUSION
    milieu_2 = milieu_1 + ENTRAXE_MILIEU_MILIEU - FUSION
    x = (-FLANC_GAUCHE["Left"], milieu_2 + FLANC_DROIT["Middle"])
    voisin = milieu_2 + ENTRAXE_MILIEU_MILIEU  # module milieu de range_epice_droite, emboîté
    return bloc(
        "range_epice_gauche",
        [(f"Left_{RANGEES}x1", 0.0), (f"Middle_{RANGEES}x1", milieu_1), (f"Middle_{RANGEES}x1", milieu_2)],
        boite(
            x,
            fermer_gauche=True,
            fermer_droite=False,
            haut=HAUT_BOITE,
            paroi=PAROI,
            passages=passage_rails(f"Middle_{RANGEES}x1", voisin),
        ),
    )
