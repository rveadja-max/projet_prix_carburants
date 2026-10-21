"""Interface du backend : le frontend n'appelle que ces fonctions."""
import json
from functools import lru_cache

import joblib
import pandas as pd

from backend.config import DEPARTEMENTS, FICHIER_METRIQUES, FICHIER_MODELE, REPORT_MAX_JOURS, TYPES_ZONE
from backend.data import lire_stations, lire_table_enregistree
from backend.model import MODELES, VARIABLES_PROFIL, alternatives_station, profils_stations, segmenter

DECISION_PLEIN = "faire le plein"
DECISION_ATTENTE = "attendre 3 jours"
NOMS_MODELES = {"prix_seuls": "prix seuls", "prix_et_taux": "prix + taux BCE"}


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


def _variables() -> list[str]:
    return MODELES[metriques()["modele_retenu"]]


@lru_cache(maxsize=1)
def _table_test() -> pd.DataFrame:
    """Lignes de la table d'analyse enregistrée à partir du début de la période de test."""
    table = lire_table_enregistree()
    return table[table["jour"] >= metriques()["debut_test"]].reset_index(drop=True)


@lru_cache(maxsize=1)
def _reseau() -> pd.DataFrame:
    """Stations du périmètre dans le flux quotidien, avec leur état le jour du conseil."""
    stations = lire_stations()
    perimetre = stations[stations["departement"].isin(DEPARTEMENTS) & stations["zone"].isin(TYPES_ZONE)].copy()
    jour = metriques()["qualite"]["jour_conseil"]
    age = (pd.Timestamp(jour) - pd.to_datetime(perimetre["maj_prix_jour"].str[:10])).dt.days
    perimetre["prix_frais"] = perimetre["prix_jour"].notna() & (age <= REPORT_MAX_JOURS)
    return perimetre.reset_index(drop=True)


def _verifier(station: str) -> None:
    if station not in set(lister_stations()["station"]):
        raise ValueError(f"Station inconnue : {station}")


def lister_stations() -> pd.DataFrame:
    """Stations du périmètre présentes dans le flux du jour et dans la période de test :
    station, ville, adresse, cp (triées par ville)."""
    reseau = _reseau()
    presentes = reseau[reseau["station"].isin(_table_test()["station"].unique())]
    colonnes = ["station", "ville", "adresse", "cp"]
    return presentes[colonnes].sort_values(["ville", "adresse"]).reset_index(drop=True)


def etat_station(station: str) -> dict:
    """État de la station dans le flux du jour : prix (€/L), date du prix, fermeture, rupture, automate."""
    _verifier(station)
    ligne = _reseau().set_index("station").loc[station]
    return {
        "jour_conseil": metriques()["qualite"]["jour_conseil"],
        "prix_jour": None if pd.isna(ligne["prix_jour"]) else float(ligne["prix_jour"]),
        "maj_prix_jour": None if pd.isna(ligne["maj_prix_jour"]) else str(ligne["maj_prix_jour"]),
        "prix_frais": bool(ligne["prix_frais"]),
        "fermee": bool(ligne["fermee"]),
        "rupture": bool(ligne["rupture"]),
        "automate_24_24": bool(ligne["automate_24_24"]),
    }


def _decision(lignes: pd.DataFrame, station: str, jour: str) -> dict:
    proba = float(_modele().predict_proba(lignes.iloc[[0]][_variables()])[0, 1])
    seuil = float(metriques()["seuil"])
    return {
        "station": str(station),
        "jour": str(jour),
        "prix": float(lignes["prix"].iloc[0]),
        "taux": float(lignes["taux"].iloc[0]),
        "proba_hausse": proba,
        "seuil": seuil,
        "decision": DECISION_PLEIN if proba > seuil else DECISION_ATTENTE,
        "modele": NOMS_MODELES[metriques()["modele_retenu"]],
    }


def conseil_du_jour(station: str) -> dict:
    """Conseil pour le jour du conseil (lendemain du dernier flux), à partir des prix connus à midi."""
    _verifier(station)
    jour = metriques()["qualite"]["jour_conseil"]
    table = lire_table_enregistree(nom="table_jour")
    lignes = table[table["station"] == station]
    if lignes.empty:
        raise ValueError(
            f"Pas de conseil le {jour} pour cette station : historique de prix incomplet "
            f"(aucun prix depuis plus de {REPORT_MAX_JOURS} jours, ou série trop courte)."
        )
    return _decision(lignes, station, jour)


def conseiller(station: str, jour: str) -> dict:
    """Rejoue la décision d'un jour de la période de test (probabilité de hausse à 3 jours et décision)."""
    table = _table_test()
    if station not in set(table["station"]):
        raise ValueError(f"Station inconnue : {station}")
    lignes = table[(table["station"] == station) & (table["jour"] == jour)]
    if lignes.empty:
        m = metriques()
        raise ValueError(
            f"Pas de donnée pour {station} le {jour} (période de test : {m['debut_test']} à {m['fin_test']})"
        )
    return _decision(lignes, station, jour)


def jours_disponibles(station: str) -> list[str]:
    """Jours de la période de test où la station a une ligne, du plus ancien au plus récent."""
    table = _table_test()
    return sorted(table.loc[table["station"] == station, "jour"])


def historique_prix(station: str) -> pd.DataFrame:
    """Prix (€/L) de la station sur la période de test : colonnes jour, prix."""
    table = _table_test()
    return table.loc[table["station"] == station, ["jour", "prix"]].sort_values("jour").reset_index(drop=True)


def alternatives(station: str) -> pd.DataFrame:
    """Top-N des stations proches moins chères aujourd'hui (prix du flux), au gain par plein positif une
    fois le détour payé. Seules les stations ouvertes, sans rupture et au prix frais sont proposées.
    Colonnes : station, ville, adresse, prix_jour, distance_km, gain_c_l, gain_plein_euros."""
    _verifier(station)
    reseau = _reseau()
    colonnes = ["station", "ville", "adresse", "prix_jour", "distance_km", "gain_c_l", "gain_plein_euros"]
    origine = reseau[reseau["station"] == station]
    if not origine["prix_frais"].iloc[0]:
        return pd.DataFrame(columns=colonnes)
    candidates = reseau[reseau["prix_frais"] & (reseau["fermee"] == 0) & (reseau["rupture"] == 0)]
    positions = pd.concat([origine, candidates[candidates["station"] != station]])
    # Écart en c€/L entre deux prix du jour : le prix lui-même, en centimes.
    prix_c = positions.set_index("station")["prix_jour"] * 100
    top = alternatives_station(positions, prix_c, station, float(origine["prix_jour"].iloc[0]))
    top = top.merge(reseau[["station", "ville", "adresse", "prix_jour"]], on="station", how="left")
    return top[colonnes].round({"distance_km": 1, "gain_c_l": 1, "gain_plein_euros": 2})


def carte_reseau() -> pd.DataFrame:
    """Stations du périmètre avec position, prix du jour et état : pour la carte de l'exploration."""
    reseau = _reseau().dropna(subset=["latitude", "longitude"])
    etat = pd.Series("ouverte", index=reseau.index)
    etat[~reseau["prix_frais"]] = "prix absent ou périmé"
    etat[reseau["rupture"] == 1] = "rupture de gazole"
    etat[reseau["fermee"] == 1] = "fermée"
    colonnes = ["station", "ville", "adresse", "latitude", "longitude", "prix_jour"]
    return reseau[colonnes].assign(etat=etat.to_numpy()).reset_index(drop=True)


def qualite() -> dict:
    """Diagnostic du réseau et de l'historique calculé par backend.train."""
    return metriques()["qualite"]


def serie_marche() -> pd.DataFrame:
    """Croisement des deux sources, jour par jour : prix médian du gazole du périmètre et taux EUR/USD de
    la BCE (celui connu à midi), en indice 100 au premier jour. Colonnes : jour, gazole, euro_dollar."""
    table = lire_table_enregistree()
    jours = table.groupby("jour").agg(gazole=("prix", "median"), euro_dollar=("taux", "first"))
    return (100 * jours / jours.iloc[0]).round(2).reset_index()


def profils_segments(k: int = 3) -> pd.DataFrame:
    """Profil moyen de chaque segment K-means de stations (table d'analyse entière, descriptif)."""
    profils = segmenter(profils_stations(lire_table_enregistree()), k)
    resume = profils.groupby("segment")[VARIABLES_PROFIL].mean().round(2)
    resume.insert(0, "effectif", profils["segment"].value_counts().sort_index())
    return resume
