"""`uv run generer <nom>` : contrôle une pièce, la rend en PNG, l'exporte en STEP et STL."""

import importlib.util
import re
import shutil
import sys
import traceback
from pathlib import Path

from build123d import Shape, export_step, export_stl

from atelier.controles import ECHEC, controler
from atelier.rendu import rendre

RACINE = Path(__file__).resolve().parents[1]
NOM = re.compile(r"[a-z][a-z0-9_]*")
USAGE, ECHEC_PIECE = 2, 1


def pieces_disponibles(racine: Path) -> list[str]:
    return sorted(p.parent.name for p in (racine / "pieces").glob("*/piece.py"))


def _erreur(message: str) -> int:
    print(f"generer : {message}", file=sys.stderr)
    return USAGE


def _charger(chemin: Path):
    spec = importlib.util.spec_from_file_location(f"piece_{chemin.parent.name}", chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "construire", None)


def main(argv: list[str] | None = None, racine: Path = RACINE, sortie: Path | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    disponibles = pieces_disponibles(racine)
    if not args:
        print("Pièces disponibles :", ", ".join(disponibles) or "aucune")
        return 0
    if len(args) > 1:
        return _erreur("une seule pièce à la fois — usage : uv run generer <nom>")
    nom = args[0]
    if not NOM.fullmatch(nom):
        return _erreur(f"nom de pièce invalide « {nom} » (attendu : minuscules, chiffres, _)")
    chemin = racine / "pieces" / nom / "piece.py"
    if not chemin.is_file():
        return _erreur(f"pièce inconnue « {nom} » — disponibles : {', '.join(disponibles) or 'aucune'}")

    # Vidé d'abord : après un échec, aucun export d'un run précédent ne doit rester.
    dossier = (sortie or racine / "out") / nom
    if dossier.exists():
        shutil.rmtree(dossier)
    dossier.mkdir(parents=True)

    try:
        construire = _charger(chemin)
        if not callable(construire):
            return _erreur(f"{chemin} doit exposer une fonction construire() qui rend un Part")
        piece = construire()
    except Exception:
        traceback.print_exc()
        print(f"generer : {ECHEC} — {chemin} a levé une exception", file=sys.stderr)
        return ECHEC_PIECE

    ecarts = controler(piece)
    echec = any(e.niveau == ECHEC for e in ecarts)
    ecrits = []
    if isinstance(piece, Shape):
        try:
            ecrits += rendre(piece, dossier)
        except Exception as erreur:
            print(f"generer : rendu impossible ({type(erreur).__name__} : {erreur})", file=sys.stderr)
        boite = piece.bounding_box()
        print(f"{nom} : {boite.size.X:.2f} × {boite.size.Y:.2f} × {boite.size.Z:.2f} mm, {piece.volume / 1000:.2f} cm³")
    for ecart in ecarts:
        print(f"  {ecart.niveau} : {ecart.message}")
    if not echec:
        step, stl = dossier / f"{nom}.step", dossier / f"{nom}.stl"
        export_step(piece, step)
        export_stl(piece, stl)
        ecrits += [step, stl]
    for fichier in ecrits:
        print(f"  écrit : {fichier}")
    if echec:
        print(f"generer : {ECHEC} — ni STEP ni STL exportés", file=sys.stderr)
        return ECHEC_PIECE
    return 0


if __name__ == "__main__":
    sys.exit(main())
