# Deux postes

Sur un poste neuf : installer `uv` et Blender 4.2 ou plus (`sudo pacman -S blender`, ou
désigner l'exécutable par la variable `BLENDER`), cloner, puis `sh init.sh`. Le script n'installe
rien au niveau système et échoue en listant tout outil manquant ; sinon il synchronise
l'environnement, génère `eprouvette_jeux` (build123d) et `vase_torsade` (Blender), puis lance
`uv run pytest`. Bambu Studio est facultatif (seulement pour trancher et imprimer :
`flatpak install flathub com.bambulab.BambuStudio`) ; `init.sh` signale s'il manque.
Ensuite `git pull` avant de travailler ; relancer `sh init.sh` dès que `pyproject.toml`,
`uv.lock` ou `init.sh` a changé.

`uv sync --locked` refuse un `uv.lock` qui ne correspond plus à `pyproject.toml` : après un
changement de dépendance, `uv lock` puis committer les deux fichiers ensemble.
