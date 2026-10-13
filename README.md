# IRwR — atelier de pièces 3D

Pièces imprimables écrites en Python ([build123d](https://build123d.readthedocs.io)),
exportées en STEP et STL pour Bambu Studio et une Bambu Lab X2D.

```sh
git clone https://github.com/Hachimanai/IRwR.git && cd IRwR
sh init.sh                        # environnement + test de fumée (demande uv)
uv run generer                    # liste des pièces
uv run generer eprouvette_jeux    # → out/eprouvette_jeux/ : STEP, STL, quatre vues PNG
```

Écrire une pièce, conventions et réglages de l'imprimante : voir `CLAUDE.md`.
