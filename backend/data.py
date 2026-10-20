"""Accès aux données : fichiers bruts (XML, CSV) -> SQLite."""
import sqlite3
import xml.etree.ElementTree as ET
import zipfile
from contextlib import closing
from pathlib import Path

import pandas as pd

from backend.config import (
    ANNEES, BASE, CARBURANT, DATE_FIN_DONNEES, DOSSIER_HISTORIQUE, FICHIER_BRENT, FICHIER_TAUX,
    PRIX_MAX, PRIX_MIN,
)
from backend.download import chemin_archive

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
