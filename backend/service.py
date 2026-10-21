"""Interface du backend : le frontend n'appelle que ces fonctions."""
import json
from functools import lru_cache

import joblib
import pandas as pd

from backend.config import DATE_FIN_ENTRAINEMENT, FICHIER_METRIQUES, FICHIER_MODELE
from backend.data import lire_stations, lire_table_enregistree
from backend.model import (
    VARIABLES_AVEC_BRENT, VARIABLES_PROFIL, alternatives_station, profils_stations, segmenter,
)

DECISION_PLEIN = "faire le plein"
DECISION_ATTENTE = "attendre 3 jours"


@lru_cache(maxsize=1)
def _modele():
    if not FICHIER_MODELE.exists():
        raise FileNotFoundError("Modèle absent. Lancer d'abord : python -m backend.train")
    # joblib = pickle : ne charger que le modèle produit par notre propre backend.train.
    return joblib.load(FICHIER_MODELE)


def metriques() -> dict:
    if not FICHIER_METRIQUES.exists():
        raise FileNotFoundError("Métriques absentes. Lancer d'abord : python -m backend.train")
    return json.loads(FICHIER_METRIQUES.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _table_test() -> pd.DataFrame:
    """Lignes de la table d'analyse enregistrée à partir du début de la période de test."""
    table = lire_table_enregistree()
    return table[table["jour"] >= metriques()["debut_test"]].reset_index(drop=True)


def lister_stations() -> pd.DataFrame:
    """Stations présentes dans la période de test : station, ville, adresse, cp (triées par ville)."""
    stations = lire_stations()
    presentes = stations[stations["station"].isin(_table_test()["station"].unique())]
    colonnes = ["station", "ville", "adresse", "cp"]
    return presentes[colonnes].sort_values(["ville", "adresse"]).reset_index(drop=True)


def jours_disponibles(station: str) -> list[str]:
    """Jours de la période de test où la station a une ligne, du plus ancien au plus récent."""
    table = _table_test()
    return sorted(table.loc[table["station"] == station, "jour"])


def historique_prix(station: str) -> pd.DataFrame:
    """Prix (€/L) de la station sur la période de test : colonnes jour, prix."""
    table = _table_test()
    return table.loc[table["station"] == station, ["jour", "prix"]].sort_values("jour").reset_index(drop=True)


def conseiller(station: str, jour: str) -> dict:
    """Probabilité de hausse à 3 jours et décision pour une station et un jour de la période de test."""
    table = _table_test()
    if station not in set(table["station"]):
        raise ValueError(f"Station inconnue : {station}")
    lignes = table[(table["station"] == station) & (table["jour"] == jour)]
    if lignes.empty:
        m = metriques()
        raise ValueError(
            f"Pas de donnée pour {station} le {jour} (période de test : {m['debut_test']} à {m['fin_test']})"
        )
    ligne = lignes.iloc[0]
    proba = float(_modele().predict_proba(lignes.iloc[[0]][VARIABLES_AVEC_BRENT])[0, 1])
    seuil = float(metriques()["seuil"])
    return {
        "station": str(station),
        "jour": str(jour),
        "prix": float(ligne["prix"]),
        "proba_hausse": proba,
        "seuil": seuil,
        "decision": DECISION_PLEIN if proba > seuil else DECISION_ATTENTE,
        "brent_eur": float(ligne["brent_eur"]),
    }


@lru_cache(maxsize=1)
def _ecarts_entrainement() -> pd.Series:
    """Écart moyen au prix médian du département (c€/L) sur l'entraînement, pour les stations encore
    présentes dans la période de test : on ne propose pas une station disparue."""
    table = lire_table_enregistree()
    ecarts = profils_stations(table[table["jour"] <= DATE_FIN_ENTRAINEMENT])["prix_relatif"]
    return ecarts[ecarts.index.isin(_table_test()["station"].unique())]


def alternatives(station: str) -> pd.DataFrame:
    """Top-N des stations proches moins chères que `station`, au gain par plein positif une fois le
    détour payé. Colonnes : station, ville, adresse, distance_km, gain_c_l, gain_plein_euros."""
    if station not in set(_table_test()["station"]):
        raise ValueError(f"Station inconnue : {station}")
    stations = lire_stations()
    prix_litre = float(metriques()["choix_station"]["prix_litre"])
    top = alternatives_station(stations, _ecarts_entrainement(), station, prix_litre)
    top = top.merge(stations[["station", "ville", "adresse"]], on="station", how="left")
    colonnes = ["station", "ville", "adresse", "distance_km", "gain_c_l", "gain_plein_euros"]
    return top[colonnes].round({"distance_km": 1, "gain_c_l": 2, "gain_plein_euros": 2})


def profils_segments(k: int = 3) -> pd.DataFrame:
    """Profil moyen de chaque segment K-means de stations (table d'analyse entière, descriptif)."""
    profils = segmenter(profils_stations(lire_table_enregistree()), k)
    resume = profils.groupby("segment")[VARIABLES_PROFIL].mean().round(2)
    resume.insert(0, "effectif", profils["segment"].value_counts().sort_index())
    return resume
