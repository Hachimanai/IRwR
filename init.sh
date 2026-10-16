#!/bin/sh
# Remet l'atelier en état sur ce poste : outils, environnement Python, les deux filières de bout
# en bout, puis la suite de tests. Idempotent, sans sudo. Échoue si uv ou Blender manque ;
# Bambu Studio est seulement signalé.
# Usage : sh init.sh
set -eu

cd "$(dirname "$0")"

BLENDER_MINIMUM=4.2

# Tous les outils d'abord, et tous les manques d'un coup, avant les étapes longues.
manque=0

if ! command -v uv >/dev/null 2>&1; then
    echo "init : uv est introuvable. L'installer :" >&2
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh    (ou le paquet « uv » de la distribution)" >&2
    manque=1
fi

# Même recherche que atelier/blender.py : $BLENDER (chemin ou nom), sinon blender dans le PATH.
blender=${BLENDER:-blender}
if ! command -v "$blender" >/dev/null 2>&1; then
    echo "init : Blender est introuvable (BLENDER=${BLENDER:-non défini}). L'installer :" >&2
    echo "  sudo pacman -S blender    (ou désigner son exécutable par la variable BLENDER)" >&2
    manque=1
else
    version=$("$blender" --version 2>/dev/null | sed -n 's/^Blender \([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -n 1)
    if [ -z "$version" ]; then
        echo "init : $blender ne donne pas de version lisible (blender --version)" >&2
        manque=1
    elif [ "$(printf '%s\n%s\n' "$BLENDER_MINIMUM" "$version" | sort -V | head -n 1)" != "$BLENDER_MINIMUM" ]; then
        echo "init : Blender $version trouvé, il faut au moins $BLENDER_MINIMUM" >&2
        manque=1
    else
        echo "init : Blender $version trouvé"
    fi
fi

if [ "$manque" -ne 0 ]; then
    echo "init : ÉCHEC, outil manquant (voir ci-dessus). Installer puis relancer sh init.sh" >&2
    exit 1
fi

echo "init : environnement Python (uv sync --locked)"
uv sync --locked

# controle <piece> <fichier>... : génère la pièce et vérifie que chaque fichier est là et non vide.
controle() {
    piece=$1
    shift
    echo "init : test de fumée (uv run generer $piece)"
    uv run generer "$piece"
    for fichier in "$@"; do
        if [ ! -s "out/$piece/$fichier" ]; then
            echo "init : out/$piece/$fichier est absent ou vide" >&2
            exit 1
        fi
    done
}

controle eprouvette_jeux eprouvette_jeux.step eprouvette_jeux.stl \
    iso.png dessus.png dessous.png face.png arriere.png droite.png gauche.png
controle vase_torsade vase_torsade.stl vase_torsade.blend iso.png face.png

echo "init : suite de tests (uv run pytest)"
uv run pytest -q

# Facultatif : sans lui, l'atelier génère tout ; il ne sert qu'à trancher et imprimer.
if command -v bambu-studio >/dev/null 2>&1 || command -v BambuStudio >/dev/null 2>&1 \
    || { command -v flatpak >/dev/null 2>&1 && flatpak info com.bambulab.BambuStudio >/dev/null 2>&1; }; then
    echo "init : Bambu Studio trouvé"
else
    echo "init : Bambu Studio introuvable (facultatif) : à installer pour trancher et imprimer,"
    echo "  flatpak install flathub com.bambulab.BambuStudio"
fi

echo "init : prêt. Générer une pièce : uv run generer <nom>   (sans nom : menu de sélection)"
