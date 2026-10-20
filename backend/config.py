"""Réglages du projet : chemins, sources de données, seed."""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data" / "raw"
HISTORY_DIR = RAW_DIR / "historique_xml"
MANIFEST_FILE = HISTORY_DIR / "manifest.json"

# Source : https://www.prix-carburants.gouv.fr/rubrique/opendata/ (vérifiée le 2026-10-20).
# Archives annuelles XML zippées, Licence Ouverte. L'année en cours est mise à jour chaque jour.
SOURCE_PAGE_URL = "https://www.prix-carburants.gouv.fr/rubrique/opendata/"
ANNUAL_ARCHIVE_URL = "https://donnees.roulez-eco.fr/opendata/annee/{year}"
YEARS = (2025, 2026)
DOWNLOAD_TIMEOUT_SECONDS = 120

SEED = 42
