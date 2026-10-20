from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
FICHIER_BRUT = RACINE / "data" / "raw" / "german.data"
BASE = RACINE / "data" / "credit.db"
FICHIER_MODELE = RACINE / "models" / "modele.joblib"
FICHIER_METRIQUES = RACINE / "models" / "metriques.json"

SEED = 42

# Matrice de coûts fournie avec le dataset (UCI) :
# accorder un crédit à un client qui fera défaut coûte 5, refuser un bon client coûte 1.
COUT_DEFAUT_ACCEPTE = 5
COUT_BON_CLIENT_REFUSE = 1
