"""Interface du backend : le frontend n'appelle que ces fonctions."""
import json
from functools import lru_cache

import joblib
import pandas as pd

from backend.config import FICHIER_METRIQUES, FICHIER_MODELE
from backend.data import lire_table_analyse
from backend.model import VARIABLES, VARIABLES_SEGMENTATION, segmenter, seuil_optimal


@lru_cache(maxsize=1)
def _modele():
    if not FICHIER_MODELE.exists():
        raise FileNotFoundError("Modèle absent. Lancer d'abord : python -m backend.train")
    # joblib = pickle : ne charger que le modèle produit par notre propre backend.train.
    return joblib.load(FICHIER_MODELE)


def lister_demandes() -> pd.DataFrame:
    return lire_table_analyse()


def scorer(demande: dict) -> dict:
    """Probabilité de défaut et décision pour une demande (dict variable -> valeur)."""
    manquantes = set(VARIABLES) - set(demande)
    if manquantes:
        raise ValueError(f"Variables manquantes : {sorted(manquantes)}")
    proba = float(_modele().predict_proba(pd.DataFrame([demande])[VARIABLES])[0, 1])
    seuil = seuil_optimal()
    return {"proba_defaut": proba, "seuil": seuil, "decision": "refuser" if proba > seuil else "accorder"}


def metriques() -> dict:
    return json.loads(FICHIER_METRIQUES.read_text(encoding="utf-8"))


def profils_segments(k: int = 3) -> pd.DataFrame:
    """Profil moyen et taux de défaut de chaque segment K-means."""
    table = segmenter(lister_demandes(), k)
    profils = table.groupby("segment")[VARIABLES_SEGMENTATION + ["defaut"]].mean().round(2)
    profils.insert(0, "effectif", table["segment"].value_counts().sort_index())
    return profils.rename(columns={"defaut": "taux_defaut"})
