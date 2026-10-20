"""Accès aux données : fichiers bruts (XML, CSV) -> SQLite -> table d'analyse (SQL puis pandas)."""
import sqlite3
import xml.etree.ElementTree as ET
import zipfile
from contextlib import closing
from pathlib import Path

import pandas as pd

from backend.config import (
    ANNEES, BASE, CARBURANT, DATE_FIN_DONNEES, DEPARTEMENTS, DOSSIER_HISTORIQUE, FICHIER_BRENT,
    FICHIER_TAUX, HEURE_DECISION, HORIZON_JOURS, PRIX_MAX, PRIX_MIN, REPORT_MAX_JOURS,
    RETARD_BRENT_JOURS, RETARD_BRENT_REALISTE_JOURS, RETARD_TAUX_JOURS, TYPES_ZONE,
)
from backend.download import chemin_archive

REQUETE_ANALYSE = Path(__file__).parent / "sql" / "table_analyse.sql"
VARIABLES = [
    "var_prix_1j", "var_prix_3j", "var_prix_7j", "ecart_mediane_dep", "var_mediane_dep_7j",
    "jours_depuis_changement", "age_prix_jours", "var_brent_7j", "var_brent_realiste_7j", "var_taux_7j",
    "jour_semaine",
]
MESSAGE_RELANCE = "Lancer d'abord : python -m backend.train"

SCHEMA = """
drop table if exists stations;
drop table if exists prix;
drop table if exists brent;
drop table if exists taux_change;
drop table if exists calendrier;
create table stations (station TEXT PRIMARY KEY, cp TEXT, departement TEXT, zone TEXT, ville TEXT, adresse TEXT);
create table prix (station TEXT, maj TEXT, valeur REAL);
create table brent (jour TEXT, dollars_baril REAL);
create table taux_change (jour TEXT, dollars_par_euro REAL);
create table calendrier (jour TEXT);
"""


def lire_archive(archive: Path, date_fin: str, con: sqlite3.Connection) -> int:
    """Lit un XML annuel en flux. Insère stations et prix du carburant. Renvoie le nombre de prix ignorés."""
    ignores = 0
    with zipfile.ZipFile(archive) as zf, zf.open(zf.namelist()[0]) as flux:
        for _, elem in ET.iterparse(flux, events=("end",)):
            if elem.tag != "pdv":
                continue
            station = elem.get("id")
            cp = elem.get("cp") or ""
            con.execute(
                "insert or replace into stations values (?, ?, ?, ?, ?, ?)",
                (station, cp, cp[:2], elem.get("pop"), elem.findtext("ville"), elem.findtext("adresse")),
            )
            lignes = []
            for prix in elem.iter("prix"):
                if prix.get("nom") != CARBURANT:
                    continue
                maj, valeur = prix.get("maj"), float(prix.get("valeur"))
                if not PRIX_MIN <= valeur <= PRIX_MAX or maj[:10] > date_fin:
                    ignores += 1
                    continue
                lignes.append((station, maj, valeur))
            con.executemany("insert into prix values (?, ?, ?)", lignes)
            elem.clear()
    return ignores


def lire_serie_csv(fichier: Path, col_jour: str, col_valeur: str, date_fin: str) -> list[tuple[str, float]]:
    """Lit un CSV (jour, valeur) : ignore les valeurs manquantes (`.`) et les jours après `date_fin`."""
    table = pd.read_csv(fichier, usecols=[col_jour, col_valeur], dtype=str)
    table[col_valeur] = pd.to_numeric(table[col_valeur], errors="coerce")
    table = table.dropna()
    table = table[table[col_jour] <= date_fin]
    return list(zip(table[col_jour], table[col_valeur].astype(float)))


def charger_brut_dans_sqlite(
    archives: list[Path] | None = None,
    fichier_brent: Path = FICHIER_BRENT,
    fichier_taux: Path = FICHIER_TAUX,
    base: Path = BASE,
    date_fin: str = DATE_FIN_DONNEES,
) -> dict[str, int]:
    """Charge XML et CSV bruts dans SQLite (tables remplacées). Renvoie le nombre de lignes par table."""
    if archives is None:
        archives = [chemin_archive(annee, DOSSIER_HISTORIQUE) for annee in ANNEES]
    for fichier in [*archives, fichier_brent, fichier_taux]:
        if not Path(fichier).exists():
            raise FileNotFoundError(f"Fichier brut introuvable : {fichier}")
    base.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(base)) as con:
        con.executescript(SCHEMA)
        ignores = sum(lire_archive(archive, date_fin, con) for archive in archives)
        con.execute(
            "delete from prix where rowid not in (select min(rowid) from prix group by station, maj)"
        )
        con.execute("create index idx_prix_station_maj on prix (station, maj)")
        con.executemany(
            "insert into brent values (?, ?)", lire_serie_csv(fichier_brent, "observation_date", "DCOILBRENTEU", date_fin)
        )
        con.executemany(
            "insert into taux_change values (?, ?)", lire_serie_csv(fichier_taux, "TIME_PERIOD", "OBS_VALUE", date_fin)
        )
        premier = con.execute("select min(substr(maj, 1, 10)) from prix").fetchone()[0]
        if premier is not None:
            jours = pd.date_range(premier, date_fin).strftime("%Y-%m-%d")
            con.executemany("insert into calendrier values (?)", [(jour,) for jour in jours])
        con.commit()
        comptes = {
            table: con.execute(f"select count(*) from {table}").fetchone()[0]
            for table in ("stations", "prix", "brent", "taux_change")
        }
    comptes["prix_ignores"] = ignores
    return {cle: comptes[cle] for cle in ("stations", "prix", "prix_ignores", "brent", "taux_change")}


def executer_requete_analyse(base: Path = BASE) -> pd.DataFrame:
    """Exécute la requête SQL versionnée : une ligne par (station, jour), prix et marché sans fuite."""
    if not base.exists():
        raise FileNotFoundError(f"Base introuvable : {base}. {MESSAGE_RELANCE}")
    parametres = {
        "heure_decision": HEURE_DECISION,
        "report_max": REPORT_MAX_JOURS,
        "retard_brent": RETARD_BRENT_JOURS,
        "retard_brent_realiste": RETARD_BRENT_REALISTE_JOURS,
        "retard_taux": RETARD_TAUX_JOURS,
    }
    with closing(sqlite3.connect(base)) as con:
        # Table temporaire : le périmètre reste réglé dans config seulement, la base n'est pas modifiée.
        con.execute("create temp table perimetre (departement TEXT, zone TEXT)")
        con.executemany(
            "insert into perimetre values (?, ?)",
            [(departement, zone) for departement in DEPARTEMENTS for zone in TYPES_ZONE],
        )
        return pd.read_sql(REQUETE_ANALYSE.read_text(encoding="utf-8"), con, params=parametres)


def valeur_decalee(table: pd.DataFrame, colonne: str, jours: int, cle: str = "station") -> pd.Series:
    """Valeur de `colonne` au jour J - `jours` pour la même `cle` (J + |jours| si `jours` < 0), vide sinon."""
    cles = [cle, "date"]
    source = table[[*cles, colonne]].drop_duplicates(cles)
    source = source.assign(date=source["date"] + pd.Timedelta(days=jours))
    return table[cles].merge(source, on=cles, how="left")[colonne].set_axis(table.index)


def ajouter_cible_et_variables(table: pd.DataFrame) -> pd.DataFrame:
    """Ajoute la cible (hausse à J + HORIZON_JOURS) et les variables, calculées sur J et avant seulement.

    Les décalages se font en jours calendaires sur la grille station × jour. Garde les lignes
    complètes (prix, prix à J + HORIZON_JOURS, toutes les variables) : une ligne par (station, jour).
    """
    table = table.reset_index(drop=True)
    table["date"] = pd.to_datetime(table["jour"])

    table["variation_future"] = valeur_decalee(table, "prix", -HORIZON_JOURS) - table["prix"]
    table["hausse"] = (table["variation_future"] > 0).astype(int)

    for jours in (1, 3, 7):
        table[f"var_prix_{jours}j"] = table["prix"] - valeur_decalee(table, "prix", jours)
    table["mediane_dep"] = table.groupby(["departement", "date"])["prix"].transform("median")
    table["ecart_mediane_dep"] = table["prix"] - table["mediane_dep"]
    table["var_mediane_dep_7j"] = table["mediane_dep"] - valeur_decalee(table, "mediane_dep", 7, "departement")

    # Jours depuis le dernier changement de prix, sur les jours où le prix est connu.
    # Le premier jour connu (ou le retour après une période muette) compte comme un changement.
    connus = table.loc[table["prix"].notna(), ["station", "date", "prix"]].sort_values(["station", "date"])
    changement = connus["prix"].ne(connus.groupby("station")["prix"].shift())
    jour_changement = connus["date"].where(changement).groupby(connus["station"]).ffill()
    table["jours_depuis_changement"] = (connus["date"] - jour_changement).dt.days

    table["age_prix_jours"] = (table["date"] - pd.to_datetime(table["date_maj"].str[:10])).dt.days
    table["var_brent_7j"] = table["brent_eur"] - valeur_decalee(table, "brent_eur", 7)
    table["var_brent_realiste_7j"] = table["brent_eur_realiste"] - valeur_decalee(table, "brent_eur_realiste", 7)
    table["var_taux_7j"] = table["taux"] - valeur_decalee(table, "taux", 7)
    table["jour_semaine"] = table["date"].dt.dayofweek

    table = table.dropna(subset=["prix", "variation_future", *VARIABLES])
    table = table.astype({"jours_depuis_changement": int, "age_prix_jours": int})
    return table.drop(columns=["date", "mediane_dep"]).sort_values(["station", "jour"]).reset_index(drop=True)


def lire_table_analyse(base: Path = BASE) -> pd.DataFrame:
    """Construit la table d'analyse : requête SQL de backend/sql/, puis cible et variables en pandas."""
    return ajouter_cible_et_variables(executer_requete_analyse(base))


def enregistrer_table_analyse(table: pd.DataFrame, base: Path = BASE) -> None:
    """Enregistre la table d'analyse dans la table SQLite `table_analyse` (remplacée)."""
    with closing(sqlite3.connect(base)) as con:
        table.to_sql("table_analyse", con, if_exists="replace", index=False)


def lire_table_enregistree(base: Path = BASE) -> pd.DataFrame:
    """Relit la table d'analyse enregistrée par `python -m backend.train`."""
    if not base.exists():
        raise FileNotFoundError(f"Base introuvable : {base}. {MESSAGE_RELANCE}")
    with closing(sqlite3.connect(base)) as con:
        existe = con.execute(
            "select count(*) from sqlite_master where type = 'table' and name = 'table_analyse'"
        ).fetchone()[0]
        if not existe:
            raise FileNotFoundError(f"Table d'analyse absente de {base}. {MESSAGE_RELANCE}")
        return pd.read_sql("select * from table_analyse", con)
