"""Filière Blender : lance Blender en arrière-plan sur une `scene.py` et rend sa réponse.

Blender garde son propre Python (le `bpy` de PyPI ne suit pas la version du dépôt) : il tourne
en sous-processus et répond par un fichier JSON écrit par `atelier/blender_scene.py`.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

from atelier.imprimabilite import PARAMETRES

SCRIPT = Path(__file__).with_name("blender_scene.py")
DELAI = 600  # secondes : au-delà, construire() est tenu pour bloqué
LIGNES_STDERR = 20


class BlenderIntrouvable(Exception):
    pass


class BlenderEchoue(Exception):
    """Blender n'a pas rendu de réponse : plantage, délai dépassé."""


def executable() -> str:
    """`$BLENDER` s'il est défini (chemin ou nom), sinon `blender` trouvé dans le PATH."""
    demande = os.environ.get("BLENDER")
    chemin = shutil.which(demande or "blender")
    if chemin:
        return chemin
    if demande:
        raise BlenderIntrouvable(f"BLENDER={demande} ne désigne pas un exécutable")
    raise BlenderIntrouvable(
        "Blender est introuvable : l'installer (sudo pacman -S blender), "
        "ou désigner son exécutable par la variable BLENDER"
    )


def executer(blender: str, scene: Path, vues: dict, travail: Path, delai: float = DELAI) -> dict:
    """Construit, mesure, exporte et rend `scene` dans `travail`. Rend la réponse de Blender."""
    demande = {
        "scene": str(scene.resolve()),
        "stl": str(travail / "piece.stl"),
        "blend": str(travail / "piece.blend"),
        "rendus": str(travail),
        "vues": vues,
        "imprimabilite": PARAMETRES,
        "reponse": str(travail / "reponse.json"),
    }
    fichier = travail / "demande.json"
    fichier.write_text(json.dumps(demande), encoding="utf-8")
    commande = [blender, "--background", "--factory-startup", "--python-exit-code", "1",
                "--python", str(SCRIPT), "--", str(fichier)]
    try:
        fini = subprocess.run(commande, capture_output=True, text=True, timeout=delai, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        raise BlenderEchoue(f"Blender n'a pas fini en {delai:g} s (construire() bloqué ?)") from None
    except OSError as erreur:
        raise BlenderEchoue(f"Blender ne se lance pas ({erreur})") from None
    reponse = Path(demande["reponse"])
    if not reponse.is_file():
        fin = "\n".join((fini.stderr or fini.stdout).strip().splitlines()[-LIGNES_STDERR:])
        raise BlenderEchoue(f"Blender s'est arrêté sans réponse (code {fini.returncode})\n{fin}")
    return json.loads(reponse.read_text(encoding="utf-8"))
