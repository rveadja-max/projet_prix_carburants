"""Modèles : Random Forest (supervisé) et K-means (non supervisé)."""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from backend.config import COUT_BON_CLIENT_REFUSE, COUT_DEFAUT_ACCEPTE, SEED

VARIABLES_NUM = [
    "duree_mois", "montant", "taux_effort", "anciennete_residence",
    "age", "nb_credits", "nb_personnes_charge",
]
VARIABLES_CAT = [
    "statut_compte", "historique_credit", "objet", "epargne", "anciennete_emploi",
    "autres_debiteurs", "patrimoine", "autres_credits", "logement", "emploi", "telephone",
]
VARIABLES = VARIABLES_NUM + VARIABLES_CAT
CIBLE = "defaut"
VARIABLES_SEGMENTATION = ["duree_mois", "montant", "age", "taux_effort"]


def creer_pipeline() -> Pipeline:
    preparation = ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore"), VARIABLES_CAT)],
        remainder="passthrough",
    )
    foret = RandomForestClassifier(
        n_estimators=300, min_samples_leaf=3, class_weight="balanced",
        random_state=SEED, n_jobs=-1,
    )
    return Pipeline([("preparation", preparation), ("foret", foret)])


def seuil_optimal() -> float:
    """Refuser dès que le coût attendu d'accepter dépasse celui de refuser :
    p × 5 > (1 − p) × 1  <=>  p > 1/6."""
    return COUT_BON_CLIENT_REFUSE / (COUT_BON_CLIENT_REFUSE + COUT_DEFAUT_ACCEPTE)


def cout_moyen(y_vrai, proba_defaut, seuil: float) -> float:
    """Coût moyen par demande, selon la matrice de coûts."""
    refuse = np.asarray(proba_defaut) > seuil
    y_vrai = np.asarray(y_vrai)
    cout = COUT_DEFAUT_ACCEPTE * ((y_vrai == 1) & ~refuse) + COUT_BON_CLIENT_REFUSE * ((y_vrai == 0) & refuse)
    return float(cout.mean())


def evaluer(pipeline: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    proba = pipeline.predict_proba(X_test)[:, 1]
    seuil = seuil_optimal()
    importances = permutation_importance(
        pipeline, X_test, y_test, scoring="roc_auc", n_repeats=10, random_state=SEED,
    )
    return {
        "roc_auc": float(roc_auc_score(y_test, proba)),
        "seuil": seuil,
        "cout_moyen_modele": cout_moyen(y_test, proba, seuil),
        "cout_moyen_seuil_05": cout_moyen(y_test, proba, 0.5),
        "cout_moyen_tout_accepter": cout_moyen(y_test, np.zeros(len(y_test)), seuil),
        "importance_permutation": dict(
            sorted(zip(X_test.columns, importances.importances_mean.round(4).tolist()),
                   key=lambda paire: -paire[1])
        ),
    }


def segmenter(table: pd.DataFrame, k: int = 3) -> pd.DataFrame:
    """K-means sur variables standardisées. Renvoie la table avec une colonne `segment`."""
    valeurs = StandardScaler().fit_transform(table[VARIABLES_SEGMENTATION])
    segments = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit_predict(valeurs)
    return table.assign(segment=segments)
