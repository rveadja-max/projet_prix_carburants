"""Modèles : forêt aléatoire (supervisée), coûts de décision et K-means (profils de stations)."""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from backend.config import DATE_FIN_ENTRAINEMENT, JOURS_MIN_PROFIL, PURGE_JOURS, SEED

VARIABLES_SANS_BRENT = [
    "prix", "var_prix_1j", "var_prix_3j", "var_prix_7j", "ecart_mediane_dep",
    "var_mediane_dep_7j", "jours_depuis_changement", "age_prix_jours", "jour_semaine",
]
VARIABLES_AVEC_BRENT = VARIABLES_SANS_BRENT + ["var_brent_7j", "var_taux_7j"]
VARIABLES_BRENT_REALISTE = VARIABLES_SANS_BRENT + ["var_brent_realiste_7j", "var_taux_7j"]
CIBLE = "hausse"
VARIABLES_PROFIL = ["prix_relatif", "changements_par_semaine", "volatilite"]
TAILLE_ECHANTILLON_PERMUTATION = 20000


def couts_moyens(variation_future, hausse) -> tuple[float, float]:
    """Coûts moyens (H, B) en c€/L, pour une variation future en €/L.

    H : manque à gagner quand on attend et que le prix monte (moyenne de la hausse,
        sur les jours de hausse).
    B : gaspillage quand on fait le plein et que le prix baisse (moyenne de la baisse,
        sur les jours sans hausse, les jours de prix stable comptant pour 0)."""
    variation = np.asarray(variation_future, dtype=float)
    hausse = np.asarray(hausse) == 1
    hausse_moyenne = (variation[hausse] * 100).mean()
    baisse_moyenne = (np.maximum(0, -variation[~hausse]) * 100).mean()
    return float(hausse_moyenne), float(baisse_moyenne)


def seuil_optimal(hausse_moyenne: float, baisse_moyenne: float) -> float:
    """Faire le plein dès que le regret attendu d'attendre dépasse celui de payer maintenant :
    p × H > (1 − p) × B  <=>  p > B / (H + B)."""
    return baisse_moyenne / (hausse_moyenne + baisse_moyenne)


def regret(variation_future, faire_le_plein) -> np.ndarray:
    """Regret par ligne en c€/L. Plein : on perd si le prix baisse. Attendre : on perd s'il monte."""
    variation = np.asarray(variation_future, dtype=float)
    plein = np.asarray(faire_le_plein, dtype=bool)
    return np.where(plein, np.maximum(0, -variation), np.maximum(0, variation)) * 100


def cout_moyen(variation_future, proba_hausse, seuil: float) -> float:
    """Regret moyen en c€/L pour la règle « plein si proba_hausse > seuil »."""
    return float(regret(variation_future, np.asarray(proba_hausse) > seuil).mean())


def couts_references(variation_future) -> dict:
    """Regrets moyens des stratégies de référence : toujours plein, toujours attendre, oracle."""
    variation = np.asarray(variation_future, dtype=float)
    return {
        "toujours_plein": float(regret(variation, np.ones(len(variation), dtype=bool)).mean()),
        "toujours_attendre": float(regret(variation, np.zeros(len(variation), dtype=bool)).mean()),
        "oracle": 0.0,
    }


def decouper_temporel(
    table: pd.DataFrame, fin_entrainement: str = DATE_FIN_ENTRAINEMENT, purge_jours: int = PURGE_JOURS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Entraînement : jour <= fin. Test : jour > fin + purge, pour que la cible du dernier jour
    d'entraînement (J + horizon) ne recouvre pas le test. Les deux sont triés par `jour`."""
    jours = pd.to_datetime(table["jour"])
    fin = pd.Timestamp(fin_entrainement)
    entrainement = table[jours <= fin].sort_values("jour")
    test = table[jours > fin + pd.Timedelta(days=purge_jours)].sort_values("jour")
    return entrainement.copy(), test.copy()


def creer_pipeline() -> Pipeline:
    """Forêt sans pondération des classes, car le seuil issu des coûts exige des probabilités non déformées."""
    foret = RandomForestClassifier(
        n_estimators=200, min_samples_leaf=100, max_samples=0.5,
        random_state=SEED, n_jobs=-1,
    )
    return Pipeline([("foret", foret)])


def evaluer(pipeline: Pipeline, X_test: pd.DataFrame, y_test, variation_future_test, seuil: float) -> dict:
    """`X_test` ne contient que les variables du modèle."""
    y_test = pd.Series(np.asarray(y_test), index=X_test.index)
    proba = pipeline.predict_proba(X_test)[:, 1]
    echantillon = X_test.sample(n=min(TAILLE_ECHANTILLON_PERMUTATION, len(X_test)), random_state=SEED)
    importances = permutation_importance(
        pipeline, echantillon, y_test.loc[echantillon.index],
        scoring="roc_auc", n_repeats=5, random_state=SEED,
    )
    return {
        "roc_auc": float(roc_auc_score(y_test, proba)),
        "cout_moyen_modele": cout_moyen(variation_future_test, proba, seuil),
        "cout_moyen_seuil_05": cout_moyen(variation_future_test, proba, 0.5),
        "importance_permutation": dict(
            sorted(zip(X_test.columns, importances.importances_mean.round(4).tolist()),
                   key=lambda paire: -paire[1])
        ),
    }


def profils_stations(table: pd.DataFrame, jours_min: int = JOURS_MIN_PROFIL) -> pd.DataFrame:
    """Une ligne par station ayant au moins JOURS_MIN_PROFIL lignes : prix relatif (c€/L),
    changements de prix par semaine (valeurs manquantes ignorées), volatilité (c€/L)."""
    groupes = table.groupby("station")
    profils = pd.DataFrame({
        "prix_relatif": groupes["ecart_mediane_dep"].mean() * 100,
        "changements_par_semaine": 7 * groupes["var_prix_1j"].apply(lambda s: (s.dropna() != 0).mean()),
        "volatilite": groupes["var_prix_1j"].std() * 100,
        "nb_jours": groupes.size(),
    })
    return profils[profils["nb_jours"] >= jours_min][VARIABLES_PROFIL]


def segmenter(profils: pd.DataFrame, k: int = 3) -> pd.DataFrame:
    """K-means sur profils standardisés. Renvoie les profils avec une colonne `segment`."""
    valeurs = StandardScaler().fit_transform(profils[VARIABLES_PROFIL])
    segments = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit_predict(valeurs)
    return profils.assign(segment=segments)
