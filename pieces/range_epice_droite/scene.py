"""Range-épices 4 × 5, bloc droit : 2 colonnes de 4 pots, d'un seul tenant, dans sa boîte.

Le design du kit « Yet another Spice Rack V2 » tel quel (voir `pieces/range_epice/kit.py`) :
module milieu + module droit fusionnés. Le flanc gauche garde la queue d'aronde du kit et se
glisse dans `range_epice_gauche`. Boîte ouverte sur l'avant : fond, dos, côté droit, dessus.
"""

from pieces.range_epice.kit import (
    ENTRAXE_MILIEU_DROITE,
    FLANC_DROIT,
    FLANC_GAUCHE,
    FUSION,
    bloc,
    boite,
    rails_amincis,
)
from pieces.range_epice_gauche.scene import HAUT_BOITE, PAROI

RANGEES = 4
# Amincissement des rails de la glissière, par face. Le kit ne laisse que 0,08 mm (queue
# d'aronde) à 0,1 mm (côtés) : premier tirage (2026-10-28) trop serré, la pièce a cassé au
# montage forcé. Avec 0,2 de plus, ≈ 0,3 mm par face.
JEU_RAILS = 0.2


def construire():
    droite = ENTRAXE_MILIEU_DROITE - FUSION
    x = (-FLANC_GAUCHE["Middle"], droite + FLANC_DROIT["Right"])
    retrait, rails = rails_amincis(f"Middle_{RANGEES}x1", 0.0, JEU_RAILS)
    return bloc(
        "range_epice_droite",
        [(f"Middle_{RANGEES}x1", 0.0), (f"Right_{RANGEES}x1", droite)],
        boite(x, fermer_gauche=False, fermer_droite=True, haut=HAUT_BOITE, paroi=PAROI) + rails,
        retraits=(retrait,),
    )
