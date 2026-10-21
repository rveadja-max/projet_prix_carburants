"""Réglages du projet : chemins, sources de données, périmètre, règles métier, seed."""
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
DOSSIER_BRUT = RACINE / "data" / "raw"
DOSSIER_HISTORIQUE = DOSSIER_BRUT / "historique_xml"
FICHIER_MANIFESTE = DOSSIER_BRUT / "manifest.json"
FICHIER_FLUX = DOSSIER_BRUT / "flux_quotidien.csv"
FICHIER_TAUX = DOSSIER_BRUT / "eurusd.csv"
BASE = RACINE / "data" / "carburants.db"
FICHIER_MODELE = RACINE / "models" / "modele.joblib"
FICHIER_METRIQUES = RACINE / "models" / "metriques.json"

# Sources (consigne du professeur, vérifiées le 2026-10-21), toutes deux sous licence ouverte :
# 1. Flux quotidien du ministère de l'Économie sur data.gouv.fr (lien stable) : une photo du réseau à
#    la veille (stations, coordonnées, services, fermetures, ruptures, dernier prix connu).
# 2. Taux de change de référence EUR/USD de la BCE, quotidien.
# Le flux n'a pas d'historique : l'historique des prix vient des archives annuelles du même producteur,
# que la page data.gouv.fr cite comme source du flux (donnees.roulez-eco.fr).
URL_PAGE_FLUX = (
    "https://explore.data.gouv.fr/fr/datasets/6615d83d7d7c66d5ec00c511/"
    "#/resources/336c34b5-a527-4c35-b84d-18462daa7c51"
)
URL_FLUX = "https://www.data.gouv.fr/api/1/datasets/r/336c34b5-a527-4c35-b84d-18462daa7c51"
URL_PAGE_ARCHIVES = "https://www.prix-carburants.gouv.fr/rubrique/opendata/"
URL_ARCHIVE_ANNUELLE = "https://donnees.roulez-eco.fr/opendata/annee/{annee}"
URL_TAUX = "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?format=csvdata&startPeriod=2024-12-01"
ANNEES = (2025, 2026)
DELAI_TELECHARGEMENT_S = 120

# Périmètre et règles de construction des variables (choix de l'équipe).
# Les métriques (entraînement et test) sont figées : seuls les jours dont le prix à J + HORIZON_JOURS
# est connu au plus tard le DATE_FIN_DONNEES entrent dans la table d'analyse. Le conseil du jour, lui,
# utilise tout l'historique disponible jusqu'au flux le plus récent.
DATE_FIN_DONNEES = "2026-10-19"
CARBURANT = "Gazole"
DEPARTEMENTS = ("59", "62")
TYPES_ZONE = ("R",)
PRIX_MIN, PRIX_MAX = 0.8, 3.5
HEURE_DECISION = 12
HORIZON_JOURS = 3
REPORT_MAX_JOURS = 7
RETARD_TAUX_JOURS = 1  # taux BCE fixé à 14 h 15 : à midi, on ne connaît que celui de la veille

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
PLEINS_PAR_AN = NB_VEHICULES * PLEINS_PAR_SEMAINE * 52

# Choix de la station (top-N) : coût d'un détour vers une station moins chère. Hypothèses fictives.
RAYON_KM = 5.0              # alternatives cherchées à moins de 5 km à vol d'oiseau de la station habituelle
NB_ALTERNATIVES = 3         # nombre de stations proposées
FACTEUR_ROUTE = 1.3         # distance sur route ≈ 1,3 × distance à vol d'oiseau
CONSO_L_100KM = 9.0         # consommation d'un utilitaire diesel
COUT_HORAIRE_EUROS = 30.0   # coût horaire chargé du chauffeur
VITESSE_KMH = 30.0          # vitesse moyenne en agglomération

SEED = 42
