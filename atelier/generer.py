"""`uv run generer <nom>` : contrôle une pièce, la rend en PNG, l'exporte en STEP et STL.

Sans nom : menu de sélection dans un terminal, liste des pièces sinon.
"""

import importlib.util
import re
import shutil
import sys
import termios
import traceback
from pathlib import Path

import questionary
from build123d import Shape, export_step, export_stl
from prompt_toolkit.keys import Keys
from questionary.prompts.common import InquirerControl

from atelier.controles import ECHEC, controler
from atelier.rendu import rendre

RACINE = Path(__file__).resolve().parents[1]
NOM = re.compile(r"[a-z][a-z0-9_]*")
USAGE, ECHEC_PIECE, ANNULE = 2, 1, 130


def inventaire(racine: Path) -> tuple[list[str], list[str]]:
    """Les pièces générables, et les dossiers écartés parce que leur nom n'est pas conforme."""
    noms = sorted(p.parent.name for p in (racine / "pieces").glob("*/piece.py") if p.is_file())
    return [n for n in noms if NOM.fullmatch(n)], [n for n in noms if not NOM.fullmatch(n)]


def _interactif() -> bool:
    return all(flux is not None and flux.isatty() for flux in (sys.stdin, sys.stdout))


def _vider_la_frappe() -> None:
    """Jette les touches tapées avant l'affichage du menu : un Entrée en avance validerait à l'aveugle."""
    try:
        termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
    except (termios.error, OSError, ValueError, AttributeError):
        pass  # pas de terminal derrière l'entrée standard : rien à jeter


COLLAGE = object()
DELAI_ECHAP = 0.1  # secondes


def _preparer(disponibles: list[str]):
    """Le menu de questionary, corrigé : ce qui ne désigne aucune pièce ne peut pas en valider une.

    Tel quel, il garde la liste entière sous un filtre sans résultat, ignore les lettres
    accentuées et les collages, et Entrée rend alors la pièce pointée.
    """
    question = questionary.select("Pièce à générer", choices=disponibles, use_search_filter=True, use_jk_keys=False)
    menu = next(c for c in question.application.layout.find_all_controls() if isinstance(c, InquirerControl))
    touches = question.application.key_bindings
    dessiner = menu.text

    def sans_resultat() -> bool:
        menu.filtered_choices  # recalcule found_in_search pour le filtre courant
        return bool(menu.search_filter) and not menu.found_in_search

    def liste():
        return [("class:search_none", "   aucune pièce ne correspond")] if sans_resultat() else dessiner()

    menu.text = liste

    @touches.add(Keys.Any)
    def _(evenement):
        # questionary ne filtre que sur l'ASCII : le reste entre aussi dans le filtre, où il se voit.
        if not evenement.data.isascii():
            menu.add_search_character(evenement.data)

    @touches.add(Keys.ControlM, eager=True)
    def _(evenement):
        if not sans_resultat():
            menu.is_answered = True
            evenement.app.exit(result=menu.get_pointed_at().value)

    @touches.add(Keys.BracketedPaste)
    def _(evenement):
        evenement.app.exit(result=COLLAGE)

    # Pas de `eager` : Échap ouvre aussi la séquence des flèches. Le délai court évite d'attendre
    # une seconde la suite d'une combinaison avant de quitter.
    @touches.add(Keys.Escape)
    def _(evenement):
        evenement.app.exit(exception=KeyboardInterrupt, style="class:aborting")

    question.application.timeoutlen = DELAI_ECHAP
    question.application.ttimeoutlen = DELAI_ECHAP

    return question, menu


def _choisir(disponibles: list[str]) -> str | None:
    """Menu aux flèches, filtré à la frappe. `None` si rien n'est choisi."""
    question, _ = _preparer(disponibles)
    _vider_la_frappe()
    choix = question.ask(kbi_msg="Annulé.")
    if choix is COLLAGE:
        print("generer : le menu n'accepte pas le collage : taper le nom, ou le passer en argument", file=sys.stderr)
        return None
    if choix == "":  # Échap puis Entrée : prompt_toolkit rend une chaîne vide
        print("Annulé.")
        return None
    return choix


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
    disponibles, ecartes = inventaire(racine)
    for nom in ecartes:
        print(f"generer : pieces/{nom!r} ignoré (nom attendu : minuscules, chiffres, _)", file=sys.stderr)
    if len(args) > 1:
        return _erreur("une seule pièce à la fois — usage : uv run generer <nom>")
    if args:
        nom = args[0]
    elif disponibles and _interactif():
        nom = _choisir(disponibles)
        if nom is None:
            return ANNULE
    else:
        # Hors terminal (script, tuyau), un menu attendrait une saisie qui ne viendra pas.
        print("Pièces disponibles :", ", ".join(disponibles) or "aucune")
        return 0
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
