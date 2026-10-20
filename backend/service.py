"""Interface du backend : le frontend n'appelle que ces fonctions."""
import json
from functools import lru_cache

import joblib
import pandas as pd

from backend.config import FICHIER_METRIQUES, FICHIER_MODELE
from backend.data import lire_stations, lire_table_enregistree
from backend.model import VARIABLES_AVEC_BRENT, VARIABLES_PROFIL, profils_stations, segmenter

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


def profils_segments(k: int = 3) -> pd.DataFrame:
    """Profil moyen de chaque segment K-means de stations (table d'analyse entière, descriptif)."""
    profils = segmenter(profils_stations(lire_table_enregistree()), k)
    resume = profils.groupby("segment")[VARIABLES_PROFIL].mean().round(2)
    resume.insert(0, "effectif", profils["segment"].value_counts().sort_index())
    return resume
