#!/bin/sh
# Remet l'atelier en état sur ce poste : environnement Python, puis une pièce de bout en bout.
# Idempotent, sans sudo. Usage : sh init.sh
set -eu

cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
    echo "init : uv est introuvable. L'installer, puis relancer ce script :" >&2
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh    (ou le paquet « uv » de la distribution)" >&2
    exit 1
fi

echo "init : environnement Python (uv sync --locked)"
uv sync --locked

echo "init : test de fumée (uv run generer eprouvette_jeux)"
uv run generer eprouvette_jeux
for fichier in eprouvette_jeux.step eprouvette_jeux.stl iso.png dessus.png face.png droite.png; do
    if [ ! -s "out/eprouvette_jeux/$fichier" ]; then
        echo "init : out/eprouvette_jeux/$fichier est absent ou vide" >&2
        exit 1
    fi
done

if command -v bambu-studio >/dev/null 2>&1 || command -v BambuStudio >/dev/null 2>&1 \
    || { command -v flatpak >/dev/null 2>&1 && flatpak info com.bambulab.BambuStudio >/dev/null 2>&1; }; then
    echo "init : Bambu Studio trouvé"
else
    echo "init : Bambu Studio introuvable sur ce poste (non bloquant) : à installer pour trancher et imprimer"
fi

echo "init : prêt. Générer une pièce : uv run generer <nom>   (sans nom : liste des pièces)"
