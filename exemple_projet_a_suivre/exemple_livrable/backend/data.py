"""Accès aux données : fichier brut -> SQLite -> table d'analyse (en SQL)."""
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

from backend.config import BASE, FICHIER_BRUT

COLONNES_BRUTES = [
    "statut_compte", "duree_mois", "historique_credit", "objet", "montant", "epargne",
    "anciennete_emploi", "taux_effort", "statut_personnel_sexe", "autres_debiteurs",
    "anciennete_residence", "patrimoine", "age", "autres_credits", "logement",
    "nb_credits", "emploi", "nb_personnes_charge", "telephone", "travailleur_etranger",
    "cible",
]
REQUETE_ANALYSE = Path(__file__).parent / "sql" / "table_analyse.sql"


def charger_brut_dans_sqlite(fichier: Path = FICHIER_BRUT, base: Path = BASE) -> int:
    """Charge le fichier UCI dans la table `demandes`. Renvoie le nombre de lignes."""
    if not fichier.exists():
        raise FileNotFoundError(f"Fichier brut introuvable : {fichier}")
    brut = pd.read_csv(fichier, sep=" ", header=None, names=COLONNES_BRUTES)
    brut.insert(0, "client_id", range(1, len(brut) + 1))
    base.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(base)) as con:
        brut.to_sql("demandes", con, if_exists="replace", index=False)
    return len(brut)


def lire_table_analyse(base: Path = BASE) -> pd.DataFrame:
    """Construit la table d'analyse avec la requête SQL versionnée dans backend/sql/."""
    if not base.exists():
        raise FileNotFoundError(f"Base introuvable : {base}. Lancer d'abord : python -m backend.train")
    with closing(sqlite3.connect(base)) as con:
        return pd.read_sql(REQUETE_ANALYSE.read_text(encoding="utf-8"), con)
