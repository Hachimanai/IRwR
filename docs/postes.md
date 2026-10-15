# Deux postes

Sur un poste neuf : cloner, puis `sh init.sh` (demande `uv` ; n'installe rien au niveau
système). Blender s'installe à part (`sudo pacman -S blender`) ; sans lui, seule la filière
build123d fonctionne et `init.sh` le signale. Ensuite `git pull` avant de travailler ; relancer
`sh init.sh` si `uv.lock` a changé.

`uv sync --locked` refuse un `uv.lock` qui ne correspond plus à `pyproject.toml` : après un
changement de dépendance, `uv lock` puis committer les deux fichiers ensemble.
