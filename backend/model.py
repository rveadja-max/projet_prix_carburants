"""Modèles : forêt aléatoire (supervisée), coûts de décision et K-means (profils de stations)."""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from backend.config import (
    CONSO_L_100KM, COUT_HORAIRE_EUROS, DATE_FIN_ENTRAINEMENT, FACTEUR_ROUTE, JOURS_MIN_PROFIL, LITRES_PAR_PLEIN,
    NB_ALTERNATIVES, PLEINS_PAR_AN, PURGE_JOURS, RAYON_KM, SEED, VITESSE_KMH,
)

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
    entrainement = table[jours <= fin].sort_values(["jour", "station"])
    test = table[jours > fin + pd.Timedelta(days=purge_jours)].sort_values(["jour", "station"])
    return entrainement.copy(), test.copy()


def plis_temporels(
    jours: pd.Series, n_plis: int = 3, purge_jours: int = PURGE_JOURS,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Plis de validation croisée par jours entiers, fenêtre croissante. Les jours uniques triés sont
    coupés en n_plis + 1 blocs consécutifs ; le pli k valide sur le bloc k + 1 et s'entraîne sur les
    jours <= premier jour de validation - purge_jours - 1, pour que les cibles (J + horizon) de
    l'entraînement ne recouvrent pas la validation. Renvoie des positions (utilisables comme `cv=`)."""
    dates = pd.to_datetime(pd.Series(np.asarray(jours))).reset_index(drop=True)
    blocs = np.array_split(np.sort(dates.unique()), n_plis + 1)
    plis = []
    for bloc in blocs[1:]:
        limite = bloc[0] - pd.Timedelta(days=purge_jours + 1)
        plis.append((np.flatnonzero((dates <= limite).to_numpy()), np.flatnonzero(dates.isin(bloc).to_numpy())))
    return plis


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


# --- Choix de la station : top-N des stations moins chères à proximité, net du coût du détour ---

RAYON_TERRE_KM = 6371.0


def distance_km(lat1, lon1, lat2, lon2):
    """Distance à vol d'oiseau (formule de haversine), en km. Accepte des scalaires ou des tableaux."""
    lat1, lon1, lat2, lon2 = (np.radians(np.asarray(v, dtype=float)) for v in (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * RAYON_TERRE_KM * np.arcsin(np.sqrt(a))


def cout_detour_euros(distance: float, prix_litre: float) -> float:
    """Coût d'un aller-retour vers une station à `distance` km à vol d'oiseau : carburant + temps du chauffeur."""
    km_route = 2 * distance * FACTEUR_ROUTE
    return km_route * (CONSO_L_100KM / 100 * prix_litre + COUT_HORAIRE_EUROS / VITESSE_KMH)


def alternatives_station(
    stations: pd.DataFrame, ecarts: pd.Series, station, prix_litre: float,
    rayon_km: float = RAYON_KM, n: int = NB_ALTERNATIVES, avec_detour: bool = True,
) -> pd.DataFrame:
    """Les n stations à moins de `rayon_km` de `station` qui font gagner le plus par plein, net du détour.

    `stations` : station, latitude, longitude. `ecarts` : écart moyen au prix médian du département
    (c€/L) par station, appris sur l'entraînement. Seules les alternatives au gain net positif sont gardées.
    `avec_detour=False` : plafond du levier, la station est sur la tournée et le détour ne coûte rien.
    Colonnes : station, distance_km, gain_c_l, gain_plein_euros (triées par gain_plein_euros décroissant)."""
    colonnes = ["station", "distance_km", "gain_c_l", "gain_plein_euros"]
    positions = stations.dropna(subset=["latitude", "longitude"]).set_index("station")
    if station not in positions.index or station not in ecarts.index:
        return pd.DataFrame(columns=colonnes)
    autres = positions.drop(index=station)
    autres = autres[autres.index.isin(ecarts.index)]
    origine = positions.loc[station]
    candidats = pd.DataFrame({
        "station": autres.index,
        "distance_km": distance_km(origine["latitude"], origine["longitude"], autres["latitude"], autres["longitude"]),
        "gain_c_l": (ecarts[station] - ecarts.reindex(autres.index)).to_numpy(),
    })
    detour = cout_detour_euros(candidats["distance_km"], prix_litre) if avec_detour else 0.0
    candidats["gain_plein_euros"] = candidats["gain_c_l"] / 100 * LITRES_PAR_PLEIN - detour
    retenus = candidats[(candidats["distance_km"] <= rayon_km) & (candidats["gain_plein_euros"] > 0)]
    return retenus.sort_values("gain_plein_euros", ascending=False).head(n).reset_index(drop=True)[colonnes]


def evaluer_choix_station(
    stations: pd.DataFrame, ecarts_entrainement: pd.Series, ecarts_test: pd.Series,
    prix_litre: float, rayon_km: float = RAYON_KM, avec_detour: bool = True,
) -> dict:
    """Gain réalisé sur le test si chaque station habituelle est remplacée par sa meilleure alternative,
    choisie sur l'entraînement seulement. Une station sans alternative rentable garde son gain de 0."""
    habituelles = ecarts_entrainement.index.intersection(ecarts_test.index)
    gains_c_l, gains_plein, avec_alternative = [], [], []
    for station in habituelles:
        meilleure = alternatives_station(stations, ecarts_entrainement, station, prix_litre, rayon_km, 1, avec_detour)
        meilleure = meilleure[meilleure["station"].isin(ecarts_test.index)]
        avec_alternative.append(not meilleure.empty)
        if meilleure.empty:
            gains_c_l.append(0.0)
            gains_plein.append(0.0)
            continue
        alternative, distance = meilleure["station"].iloc[0], meilleure["distance_km"].iloc[0]
        gain = float(ecarts_test[station] - ecarts_test[alternative])
        gains_c_l.append(gain)
        detour = float(cout_detour_euros(distance, prix_litre)) if avec_detour else 0.0
        gains_plein.append(gain / 100 * LITRES_PAR_PLEIN - detour)
    gain_plein = float(np.mean(gains_plein)) if gains_plein else 0.0
    return {
        "nb_stations": int(len(habituelles)),
        "part_avec_alternative": float(np.mean(avec_alternative)) if avec_alternative else 0.0,
        "gain_moyen_c_l": float(np.mean(gains_c_l)) if gains_c_l else 0.0,
        "gain_moyen_plein_euros": gain_plein,
        "economie_annuelle_euros": gain_plein * PLEINS_PAR_AN,
    }


def intervalle_gain(
    jours, regret_reference, regret_strategie, taille_bloc_jours: int = 7, n_tirages: int = 2000,
    seed: int = SEED,
) -> dict:
    """Gain moyen (c€/L) d'une stratégie sur une référence, avec un intervalle de confiance à 95 %.

    Bootstrap par blocs de `taille_bloc_jours` jours consécutifs : toutes les stations d'un même jour,
    et les jours proches, bougent ensemble ; tirer des lignes isolées donnerait un intervalle trop étroit."""
    ecart = np.asarray(regret_reference, dtype=float) - np.asarray(regret_strategie, dtype=float)
    dates = pd.to_datetime(pd.Series(np.asarray(jours)))
    blocs = ((dates - dates.min()).dt.days // taille_bloc_jours).to_numpy()
    sommes, comptes = np.bincount(blocs, weights=ecart), np.bincount(blocs)
    sommes, comptes = sommes[comptes > 0], comptes[comptes > 0]
    tirages = np.random.default_rng(seed).integers(0, len(comptes), size=(n_tirages, len(comptes)))
    gains = sommes[tirages].sum(axis=1) / comptes[tirages].sum(axis=1)
    bas, haut = np.percentile(gains, [2.5, 97.5])
    return {"moyenne": float(ecart.mean()), "bas": float(bas), "haut": float(haut)}


def regret_par_mois(jours, regrets: dict) -> list[dict]:
    """Regret moyen (c€/L) de chaque stratégie, mois par mois. `regrets` : {nom: regret de chaque ligne}."""
    table = pd.DataFrame({nom: np.asarray(valeurs, dtype=float) for nom, valeurs in regrets.items()})
    table["mois"] = pd.Series(np.asarray(jours)).str[:7]
    moyennes = table.groupby("mois").mean()
    effectifs = table.groupby("mois").size()
    return [
        {"mois": mois, "nb_lignes": int(effectifs[mois]), **{nom: float(moyennes.loc[mois, nom]) for nom in regrets}}
        for mois in moyennes.index
    ]
