"""Réglages du projet : chemins, sources de données, périmètre, règles métier, seed."""
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
DOSSIER_BRUT = RACINE / "data" / "raw"
DOSSIER_HISTORIQUE = DOSSIER_BRUT / "historique_xml"
FICHIER_MANIFESTE = DOSSIER_BRUT / "manifest.json"
FICHIER_BRENT = DOSSIER_BRUT / "brent.csv"
FICHIER_TAUX = DOSSIER_BRUT / "eurusd.csv"
BASE = RACINE / "data" / "carburants.db"
FICHIER_MODELE = RACINE / "models" / "modele.joblib"
FICHIER_METRIQUES = RACINE / "models" / "metriques.json"

# Sources vérifiées le 2026-10-20 : prix-carburants.gouv.fr (Licence Ouverte), FRED (Brent
# DCOILBRENTEU, dollars par baril) et BCE (taux de change de référence EUR/USD).
URL_PAGE_SOURCE = "https://www.prix-carburants.gouv.fr/rubrique/opendata/"
URL_ARCHIVE_ANNUELLE = "https://donnees.roulez-eco.fr/opendata/annee/{annee}"
URL_BRENT = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU&cosd=2024-12-01"
URL_TAUX = "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?format=csvdata&startPeriod=2024-12-01"
ANNEES = (2025, 2026)
DELAI_TELECHARGEMENT_S = 120

# Périmètre et règles de construction des variables (choix de l'équipe, source vérifiée le 2026-10-20).
DATE_FIN_DONNEES = "2026-10-19"
CARBURANT = "Gazole"
DEPARTEMENTS = ("59", "62")
TYPES_ZONE = ("R",)
PRIX_MIN, PRIX_MAX = 0.8, 3.5
HEURE_DECISION = 12
HORIZON_JOURS = 3
REPORT_MAX_JOURS = 7
RETARD_BRENT_JOURS = 1
RETARD_BRENT_REALISTE_JOURS = 8
RETARD_TAUX_JOURS = 1

# Validation temporelle (choix de l'équipe) : entraînement jusqu'à cette date, puis purge.
DATE_FIN_ENTRAINEMENT = "2026-04-30"
PURGE_JOURS = HORIZON_JOURS

# Une station doit avoir au moins ce nombre de jours observés pour avoir un profil.
JOURS_MIN_PROFIL = 30

# Flotte de l'entreprise cliente : hypothèse fictive.
NB_VEHICULES = 40
LITRES_PAR_PLEIN = 60
PLEINS_PAR_SEMAINE = 1
LITRES_PAR_AN = NB_VEHICULES * LITRES_PAR_PLEIN * PLEINS_PAR_SEMAINE * 52

SEED = 42
