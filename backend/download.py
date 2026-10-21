"""Téléchargement des sources de données : flux quotidien data.gouv.fr, archives XML annuelles,
Brent (FRED) et EUR/USD (BCE).

Usage : python -m backend.download [--annees 2025 2026] [--forcer]

Les archives vont dans data/raw/historique_xml/, les CSV (flux quotidien, Brent, taux) dans
data/raw/, et ne sont jamais modifiés ensuite. Chaque téléchargement est noté dans
data/raw/manifest.json (URL, date, taille, SHA-256). Un fichier déjà présent n'est pas
retéléchargé, sauf avec --forcer (utile pour rafraîchir le flux quotidien et l'année en
cours, mis à jour chaque jour par les sources).
"""
import argparse
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

from backend.config import (
    ANNEES,
    DELAI_TELECHARGEMENT_S,
    DOSSIER_HISTORIQUE,
    FICHIER_BRENT,
    FICHIER_FLUX_QUOTIDIEN,
    FICHIER_MANIFESTE,
    FICHIER_TAUX,
    URL_ARCHIVE_ANNUELLE,
    URL_BRENT,
    URL_FLUX_QUOTIDIEN,
    URL_PAGE_SOURCE,
    URL_TAUX,
)


def url_archive(annee: int) -> str:
    return URL_ARCHIVE_ANNUELLE.format(annee=annee)


def chemin_archive(annee: int, dossier: Path) -> Path:
    return dossier / f"PrixCarburants_annuel_{annee}.zip"


def empreinte_sha256(chemin: Path) -> str:
    empreinte = hashlib.sha256()
    with chemin.open("rb") as flux:
        for bloc in iter(lambda: flux.read(1024 * 1024), b""):
            empreinte.update(bloc)
    return empreinte.hexdigest()


def ouvrir_distant(url: str, delai: int):
    # User-Agent par défaut de urllib : FRED laisse sans réponse les User-Agent personnalisés.
    return urlopen(url, timeout=delai)


def _entree_manifeste(cible: Path, url: str, source: str, **extra) -> dict:
    return {
        "file": cible.name,
        "url": url,
        "source_page": source,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "size_bytes": cible.stat().st_size,
        "sha256": empreinte_sha256(cible),
        **extra,
    }


def telecharger_archive(annee: int, dossier: Path = DOSSIER_HISTORIQUE, forcer: bool = False,
                        ouvrir_url=ouvrir_distant) -> dict | None:
    """Télécharge l'archive d'une année. Renvoie l'entrée du manifeste, ou None si déjà présente."""
    cible = chemin_archive(annee, dossier)
    if cible.exists() and not forcer:
        return None

    dossier.mkdir(parents=True, exist_ok=True)
    url = url_archive(annee)
    partiel = cible.with_name(cible.name + ".part")
    try:
        with ouvrir_url(url, DELAI_TELECHARGEMENT_S) as reponse, partiel.open("wb") as sortie:
            shutil.copyfileobj(reponse, sortie)
        if not zipfile.is_zipfile(partiel):
            raise ValueError(f"Le fichier reçu pour {annee} n'est pas une archive ZIP : {url}")
        with zipfile.ZipFile(partiel) as archive:
            membre_casse = archive.testzip()
        if membre_casse is not None:
            raise ValueError(f"Archive {annee} corrompue (membre {membre_casse}) : {url}")
    except BaseException:
        partiel.unlink(missing_ok=True)
        raise

    partiel.replace(cible)
    return _entree_manifeste(cible, url, URL_PAGE_SOURCE, year=annee)


def telecharger_csv(url: str, cible: Path, entete_attendue: str, forcer: bool = False,
                    ouvrir_url=ouvrir_distant) -> dict | None:
    """Télécharge un CSV. Renvoie l'entrée du manifeste, ou None si déjà présent.

    Le fichier est rejeté (ValueError) si sa première ligne ne commence pas par entete_attendue.
    """
    if cible.exists() and not forcer:
        return None

    cible.parent.mkdir(parents=True, exist_ok=True)
    partiel = cible.with_name(cible.name + ".part")
    try:
        with ouvrir_url(url, DELAI_TELECHARGEMENT_S) as reponse, partiel.open("wb") as sortie:
            shutil.copyfileobj(reponse, sortie)
        premiere_ligne = partiel.read_bytes().decode("utf-8-sig", errors="replace").splitlines()[:1]
        if not premiere_ligne or not premiere_ligne[0].startswith(entete_attendue):
            raise ValueError(f"En-tête inattendu (attendu : {entete_attendue}) : {url}")
    except BaseException:
        partiel.unlink(missing_ok=True)
        raise

    partiel.replace(cible)
    return _entree_manifeste(cible, url, url)


def mettre_a_jour_manifeste(entrees: list[dict], manifeste: Path = FICHIER_MANIFESTE) -> None:
    """Ajoute ou remplace les entrées du manifeste, indexées par nom de fichier."""
    contenu = {}
    if manifeste.exists():
        contenu = json.loads(manifeste.read_text(encoding="utf-8"))
    for entree in entrees:
        contenu[entree["file"]] = entree
    manifeste.parent.mkdir(parents=True, exist_ok=True)
    manifeste.write_text(json.dumps(contenu, indent=2, ensure_ascii=False, sort_keys=True),
                         encoding="utf-8")


def telecharger_tout(forcer: bool = False, annees=ANNEES) -> list[dict]:
    """Télécharge flux quotidien, archives, Brent et taux. Met à jour le manifeste."""
    entrees = []
    for annee in annees:
        entree = telecharger_archive(annee, forcer=forcer)
        if entree is None:
            print(f"{annee} : déjà présent, ignoré ({chemin_archive(annee, DOSSIER_HISTORIQUE)})")
            continue
        print(f"{annee} : {entree['size_bytes']:,} octets, sha256 {entree['sha256'][:12]}…")
        entrees.append(entree)
    for url, cible, entete in ((URL_FLUX_QUOTIDIEN, FICHIER_FLUX_QUOTIDIEN, "id;"),
                               (URL_BRENT, FICHIER_BRENT, "observation_date"),
                               (URL_TAUX, FICHIER_TAUX, "KEY")):
        entree = telecharger_csv(url, cible, entete, forcer=forcer)
        if entree is None:
            print(f"{cible.name} : déjà présent, ignoré ({cible})")
            continue
        print(f"{cible.name} : {entree['size_bytes']:,} octets, sha256 {entree['sha256'][:12]}…")
        entrees.append(entree)
    if entrees:
        mettre_a_jour_manifeste(entrees)
    return entrees


def main(argv: list[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analyseur.add_argument("--annees", type=int, nargs="+", default=list(ANNEES))
    analyseur.add_argument("--forcer", action="store_true",
                           help="retélécharge même si le fichier existe")
    args = analyseur.parse_args(argv)
    telecharger_tout(forcer=args.forcer, annees=args.annees)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
