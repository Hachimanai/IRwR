"""`uv run generer <nom>` : contrôle une pièce, la rend en PNG, l'exporte.

Deux filières, selon le fichier du dossier `pieces/<nom>/` : `piece.py` (build123d, export STEP
et STL) ou `scene.py` (Blender, export STL et .blend). Sans nom : menu de sélection dans un
terminal, liste des pièces sinon.
"""

import importlib.util
import re
import shutil
import sys
import tempfile
import termios
import traceback
from pathlib import Path

import questionary
from build123d import Part, Shape, export_step, export_stl
from prompt_toolkit.keys import Keys
from questionary.prompts.common import InquirerControl

from atelier import blender, imprimabilite
from atelier.controles import ECHEC, controler, controler_maillage
from atelier.rendu import VUES, composer, rendre

RACINE = Path(__file__).resolve().parents[1]
NOM = re.compile(r"[a-z][a-z0-9_]*")
USAGE, ECHEC_PIECE, ANNULE = 2, 1, 130
FICHIERS = ("piece.py", "scene.py")  # build123d, Blender


def inventaire(racine: Path) -> tuple[list[str], list[str]]:
    """Les pièces générables, et les dossiers écartés parce que leur nom n'est pas conforme."""
    noms = sorted({p.parent.name for f in FICHIERS for p in (racine / "pieces").glob(f"*/{f}") if p.is_file()})
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
    sources = [racine / "pieces" / nom / f for f in FICHIERS if (racine / "pieces" / nom / f).is_file()]
    if not sources:
        return _erreur(f"pièce inconnue « {nom} » — disponibles : {', '.join(disponibles) or 'aucune'}")
    if len(sources) > 1:
        return _erreur(f"pieces/{nom} a piece.py et scene.py : une pièce = une filière, en garder un")
    chemin = sources[0]
    if chemin.name == "scene.py":
        try:
            executable = blender.executable()
        except blender.BlenderIntrouvable as erreur:
            return _erreur(str(erreur))

    # Vidé d'abord : après un échec, aucun export d'un run précédent ne doit rester.
    dossier = (sortie or racine / "out") / nom
    if dossier.exists():
        shutil.rmtree(dossier)
    dossier.mkdir(parents=True)

    if chemin.name == "scene.py":
        return _generer_blender(nom, chemin, executable, dossier)
    return _generer_build123d(nom, chemin, dossier)


def _conclure(ecarts, ecrits: list[Path], exporter) -> int:
    """Affiche les écarts ; exporte si aucun n'est un ÉCHEC. Commun aux deux filières."""
    echec = any(e.niveau == ECHEC for e in ecarts)
    for ecart in ecarts:
        print(f"  {ecart.niveau} : {ecart.message}")
    if not echec:
        ecrits += exporter()
    for fichier in ecrits:
        print(f"  écrit : {fichier}")
    if echec:
        print(f"generer : {ECHEC} — rien n'est exporté", file=sys.stderr)
        return ECHEC_PIECE
    return 0


def _imprimabilite(mesures: dict) -> list:
    ligne, ecarts = imprimabilite.resumer(mesures)
    print(f"  {ligne}")
    return ecarts


def _generer_build123d(nom: str, chemin: Path, dossier: Path) -> int:
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
    ecrits = []
    if isinstance(piece, Shape):
        try:
            ecrits += rendre(piece, dossier)
        except Exception as erreur:
            print(f"generer : rendu impossible ({type(erreur).__name__} : {erreur})", file=sys.stderr)
        boite = piece.bounding_box()
        print(f"{nom} : {boite.size.X:.2f} × {boite.size.Y:.2f} × {boite.size.Z:.2f} mm, {piece.volume / 1000:.2f} cm³")
    if isinstance(piece, Part) and piece.solids():
        try:
            ecarts += _imprimabilite(imprimabilite.mesurer(piece))
        except Exception as erreur:
            print(f"generer : imprimabilité non mesurée ({type(erreur).__name__} : {erreur})", file=sys.stderr)

    def exporter():
        step, stl = dossier / f"{nom}.step", dossier / f"{nom}.stl"
        export_step(piece, step)
        export_stl(piece, stl)
        return [step, stl]

    return _conclure(ecarts, ecrits, exporter)


def _generer_blender(nom: str, chemin: Path, executable: str, dossier: Path) -> int:
    vues = {vue: [direction, haut] for vue, (direction, haut, _) in VUES.items()}
    with tempfile.TemporaryDirectory(prefix="generer-") as travail:
        travail = Path(travail)
        try:
            reponse = blender.executer(executable, chemin, vues, travail)
        except blender.BlenderEchoue as erreur:
            print(f"generer : {ECHEC} — {erreur}", file=sys.stderr)
            return ECHEC_PIECE
        if "erreur_usage" in reponse:
            return _erreur(reponse["erreur_usage"])
        if "erreur" in reponse:
            print(reponse["erreur"], end="", file=sys.stderr)
            print(f"generer : {ECHEC} — {chemin} a levé une exception", file=sys.stderr)
            return ECHEC_PIECE

        mesures = reponse["mesures"]
        ecarts = controler_maillage(mesures)
        ecrits = []
        if "erreur_imprimabilite" in reponse:
            print(f"generer : imprimabilité non mesurée ({reponse['erreur_imprimabilite']})", file=sys.stderr)
        if "erreur_rendu" in reponse:
            print(f"generer : rendu impossible ({reponse['erreur_rendu']})", file=sys.stderr)
        for vue, rendu in reponse.get("rendus", {}).items():
            try:
                ecrits.append(composer(vue, Path(rendu["fichier"]), rendu["cadrage"], rendu["emprise"],
                                       reponse["centre"], dossier / f"{vue}.png"))
            except Exception as erreur:
                print(f"generer : rendu impossible ({vue} : {type(erreur).__name__} : {erreur})", file=sys.stderr)
        if mesures.get("type") == "MESH" and mesures["faces"]:
            taille = [b - a for a, b in zip(mesures["boite_min"], mesures["boite_max"])]
            print(f"{nom} : {taille[0]:.2f} × {taille[1]:.2f} × {taille[2]:.2f} mm, "
                  f"{mesures['volume'] / 1000:.2f} cm³ (maillage Blender)")
        if "imprimabilite" in mesures:
            ecarts += _imprimabilite(mesures["imprimabilite"])

        def exporter():
            stl, blend = dossier / f"{nom}.stl", dossier / f"{nom}.blend"
            shutil.copyfile(travail / "piece.stl", stl)
            shutil.copyfile(travail / "piece.blend", blend)
            return [stl, blend]

        return _conclure(ecarts, ecrits, exporter)


if __name__ == "__main__":
    sys.exit(main())
