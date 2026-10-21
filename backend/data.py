"""Accès aux données : fichiers bruts (CSV du flux quotidien, XML des archives, CSV BCE) -> SQLite
-> table d'analyse (SQL puis pandas)."""
import json
import sqlite3
import xml.etree.ElementTree as ET
import zipfile
from contextlib import closing
from pathlib import Path

import pandas as pd

from backend.config import (
    ANNEES, BASE, CARBURANT, DATE_FIN_DONNEES, DEPARTEMENTS, DOSSIER_HISTORIQUE, FICHIER_FLUX,
    FICHIER_TAUX, HEURE_DECISION, HORIZON_JOURS, PRIX_MAX, PRIX_MIN, REPORT_MAX_JOURS,
    RETARD_TAUX_JOURS, TYPES_ZONE,
)
from backend.download import chemin_archive

DOSSIER_SQL = Path(__file__).parent / "sql"
REQUETE_SCHEMA = DOSSIER_SQL / "schema.sql"
REQUETE_ANALYSE = DOSSIER_SQL / "table_analyse.sql"
VARIABLES = [
    "var_prix_1j", "var_prix_3j", "var_prix_7j", "ecart_mediane_dep", "var_mediane_dep_7j",
    "jours_depuis_changement", "age_prix_jours", "var_taux_1j", "var_taux_3j", "var_taux_7j",
    "jour_semaine",
]
MESSAGE_RELANCE = "Lancer d'abord : python -m backend.train"
COLONNES_FLUX = {
    "id": "station", "Code postal": "cp", "pop": "zone", "ville": "ville", "adresse": "adresse",
    "geom": "geom", "Automate 24-24 (oui/non)": "automate", "fermeture": "fermeture",
    "Carburant": "carburant", "Prix": "prix", "Mise à jour des prix": "maj",
    "Carburant en rupture": "rupture_nom", "Fin rupture": "rupture_fin",
}


def heure_locale(horodatage: str | None) -> str | None:
    """« 2026-10-20T07:31:00+00:00 » -> « 2026-10-20T07:31:00 ». Le suffixe +00:00 du flux est trompeur :
    les mêmes prix portent la même heure dans les archives, qui sont en heure locale."""
    if not isinstance(horodatage, str) or not horodatage:
        return None
    return horodatage[:19]


def fermee_le(fermeture: str | None, jour: str) -> bool:
    """Vrai si une fermeture (temporaire ou définitive) couvre `jour`. Le champ du flux est un objet
    JSON {"@type", "@debut", "@fin"} ou une liste de tels objets ; une fin vide = pas de réouverture."""
    if not isinstance(fermeture, str) or not fermeture:
        return False
    periodes = json.loads(fermeture)
    for periode in periodes if isinstance(periodes, list) else [periodes]:
        debut, fin = (periode.get("@debut") or "")[:10], (periode.get("@fin") or "")[:10]
        if debut and debut <= jour and (not fin or fin >= jour):
            return True
    return False


def lire_flux(fichier: Path, date_fin: str | None = None) -> tuple[pd.DataFrame, str]:
    """Lit le flux quotidien. Renvoie (stations, jour du conseil).

    Le flux a une ligne par station, carburant et rupture (lignes répétées) : on le ramène à une ligne
    par station. Jour du conseil = lendemain du dernier prix publié (le flux contient les données de la
    veille), ou lendemain de `date_fin` si elle est donnée. Prix hors bornes ou après `date_fin` : vides."""
    flux = pd.read_csv(fichier, sep=";", dtype=str, encoding="utf-8-sig", usecols=list(COLONNES_FLUX))
    flux = flux.rename(columns=COLONNES_FLUX)
    flux["maj"] = flux["maj"].map(heure_locale)
    flux["prix"] = pd.to_numeric(flux["prix"], errors="coerce")
    carburant = flux[flux["carburant"] == CARBURANT]
    if date_fin is None:
        date_fin = carburant["maj"].dropna().str[:10].max()
    jour = (pd.Timestamp(date_fin) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    stations = flux.drop_duplicates("station").set_index("station")
    position = stations["geom"].str.extract(r"^\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*$").astype(float)
    prix = carburant.drop_duplicates("station").set_index("station")
    valide = prix["prix"].between(PRIX_MIN, PRIX_MAX) & (prix["maj"].str[:10] <= date_fin)
    ruptures = flux[(flux["rupture_nom"] == CARBURANT)
                    & (flux["rupture_fin"].isna() | (flux["rupture_fin"].fillna("").str[:10] >= jour))]
    table = pd.DataFrame({
        "station": stations.index,
        "cp": stations["cp"].to_numpy(),
        "departement": stations["cp"].str[:2].to_numpy(),
        "zone": stations["zone"].to_numpy(),
        "ville": stations["ville"].to_numpy(),
        "adresse": stations["adresse"].to_numpy(),
        "latitude": position[0].to_numpy(),
        "longitude": position[1].to_numpy(),
        "automate_24_24": (stations["automate"] == "Oui").astype(int).to_numpy(),
        "fermee": stations["fermeture"].map(lambda f: int(fermee_le(f, jour))).to_numpy(),
        "rupture": stations.index.isin(ruptures["station"]).astype(int),
        "prix_jour": prix["prix"].where(valide).reindex(stations.index).to_numpy(),
        "maj_prix_jour": prix["maj"].where(valide).reindex(stations.index).to_numpy(),
    })
    return table, jour


def lire_archive(archive: Path, date_fin: str, con: sqlite3.Connection) -> int:
    """Lit un XML annuel en flux. Insère les stations et les prix du carburant. Renvoie le nombre de prix
    ignorés (hors bornes ou après `date_fin`). Les coordonnées des archives ne sont pas lues : le flux
    quotidien donne des positions propres (celles des archives ont des inversions et des trous)."""
    ignores = 0
    with zipfile.ZipFile(archive) as zf, zf.open(zf.namelist()[0]) as flux:
        for _, elem in ET.iterparse(flux, events=("end",)):
            if elem.tag != "pdv":
                continue
            station = elem.get("id")
            cp = elem.get("cp") or ""
            con.execute(
                "insert or replace into stations_historique values (?, ?, ?, ?)",
                (station, cp, cp[:2], elem.get("pop")),
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
    """Lit un CSV (jour, valeur) : ignore les valeurs manquantes et les jours après `date_fin`."""
    table = pd.read_csv(fichier, usecols=[col_jour, col_valeur], dtype=str)
    table[col_valeur] = pd.to_numeric(table[col_valeur], errors="coerce")
    table = table.dropna()
    table = table[table[col_jour] <= date_fin]
    return list(zip(table[col_jour], table[col_valeur].astype(float)))


def charger_brut_dans_sqlite(
    archives: list[Path] | None = None,
    fichier_flux: Path = FICHIER_FLUX,
    fichier_taux: Path = FICHIER_TAUX,
    base: Path = BASE,
    date_fin: str | None = None,
) -> dict:
    """Charge flux, archives et taux dans SQLite (tables remplacées, schéma de backend/sql/schema.sql).

    `date_fin` : dernier jour de prix chargé ; par défaut, le dernier jour du flux. Le calendrier va du
    premier prix au jour du conseil (`date_fin` + 1). Renvoie les comptes par table et le jour du conseil."""
    if archives is None:
        archives = [chemin_archive(annee, DOSSIER_HISTORIQUE) for annee in ANNEES]
    for fichier in [*archives, fichier_flux, fichier_taux]:
        if not Path(fichier).exists():
            raise FileNotFoundError(f"Fichier brut introuvable : {fichier}")
    stations, jour_conseil = lire_flux(fichier_flux, date_fin)
    date_fin = (pd.Timestamp(jour_conseil) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    base.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(base)) as con:
        con.executescript(REQUETE_SCHEMA.read_text(encoding="utf-8"))
        stations.to_sql("stations", con, if_exists="append", index=False)
        ignores = sum(lire_archive(archive, date_fin, con) for archive in archives)
        # Le dernier prix du flux complète l'historique (doublon exact quand l'archive l'a déjà). Un prix plus
        # ancien que les archives (le flux en garde depuis 2009) n'y entre pas : il étendrait le calendrier.
        debut_archives = con.execute("select min(maj) from prix").fetchone()[0] or ""
        prix_flux = stations.dropna(subset=["prix_jour"])
        prix_flux = prix_flux[prix_flux["maj_prix_jour"] >= debut_archives]
        con.executemany("insert into prix values (?, ?, ?)",
                        zip(prix_flux["station"], prix_flux["maj_prix_jour"], prix_flux["prix_jour"]))
        con.execute(
            "delete from prix where rowid not in (select min(rowid) from prix group by station, maj)"
        )
        con.execute("create index idx_prix_station_maj on prix (station, maj)")
        con.executemany(
            "insert into taux_change values (?, ?)", lire_serie_csv(fichier_taux, "TIME_PERIOD", "OBS_VALUE", date_fin)
        )
        premier = con.execute("select min(substr(maj, 1, 10)) from prix").fetchone()[0]
        if premier is not None:
            jours = pd.date_range(premier, jour_conseil).strftime("%Y-%m-%d")
            con.executemany("insert into calendrier values (?)", [(jour,) for jour in jours])
        con.commit()
        comptes = {
            table: con.execute(f"select count(*) from {table}").fetchone()[0]
            for table in ("stations", "stations_historique", "prix", "taux_change")
        }
    return {**comptes, "prix_ignores": ignores, "jour_conseil": jour_conseil}


def executer_requete_analyse(base: Path = BASE) -> pd.DataFrame:
    """Exécute la requête SQL versionnée : une ligne par (station, jour), prix et marché sans fuite."""
    if not base.exists():
        raise FileNotFoundError(f"Base introuvable : {base}. {MESSAGE_RELANCE}")
    parametres = {
        "heure_decision": HEURE_DECISION,
        "report_max": REPORT_MAX_JOURS,
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


def calculer_variables(table: pd.DataFrame) -> pd.DataFrame:
    """Ajoute à la sortie SQL la variation future, la cible et les variables, calculées sur J et avant.

    Garde toutes les lignes, même incomplètes : `ajouter_cible_et_variables` en tire la table d'analyse,
    `lignes_du_jour` les lignes du conseil du jour (dont l'avenir est inconnu). Les décalages se font en
    jours calendaires sur la grille station × jour."""
    table = table.reset_index(drop=True)
    table["date"] = pd.to_datetime(table["jour"])

    table["variation_future"] = valeur_decalee(table, "prix", -HORIZON_JOURS) - table["prix"]

    for jours in (1, 3, 7):
        table[f"var_prix_{jours}j"] = table["prix"] - valeur_decalee(table, "prix", jours)
        table[f"var_taux_{jours}j"] = table["taux"] - valeur_decalee(table, "taux", jours)
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
    table["jour_semaine"] = table["date"].dt.dayofweek
    return table.drop(columns=["date", "mediane_dep"]).sort_values(["station", "jour"]).reset_index(drop=True)


def _completes(table: pd.DataFrame) -> pd.DataFrame:
    table = table.dropna(subset=["prix", *VARIABLES])
    return table.astype({"jours_depuis_changement": int, "age_prix_jours": int})


def ajouter_cible_et_variables(table: pd.DataFrame, date_fin: str = DATE_FIN_DONNEES) -> pd.DataFrame:
    """Table d'analyse : une ligne par (station, jour) complète, dont le prix à J + HORIZON_JOURS est
    connu au plus tard le `date_fin` (métriques figées même quand l'historique s'allonge)."""
    table = calculer_variables(table)
    limite = (pd.Timestamp(date_fin) - pd.Timedelta(days=HORIZON_JOURS)).strftime("%Y-%m-%d")
    table = _completes(table.dropna(subset=["variation_future"]))
    table = table[table["jour"] <= limite].copy()
    table["hausse"] = (table["variation_future"] > 0).astype(int)
    return table.reset_index(drop=True)


def lignes_du_jour(table_variables: pd.DataFrame, jour: str) -> pd.DataFrame:
    """Lignes complètes (variables connues) du `jour`, sans cible : l'entrée du conseil du jour."""
    lignes = _completes(table_variables[table_variables["jour"] == jour])
    return lignes.drop(columns=["variation_future"]).reset_index(drop=True)


def lire_table_analyse(base: Path = BASE, date_fin: str = DATE_FIN_DONNEES) -> pd.DataFrame:
    """Construit la table d'analyse : requête SQL de backend/sql/, puis cible et variables en pandas."""
    return ajouter_cible_et_variables(executer_requete_analyse(base), date_fin)


def enregistrer_table_analyse(table: pd.DataFrame, base: Path = BASE, nom: str = "table_analyse") -> None:
    """Enregistre une table pandas dans SQLite sous `nom` (remplacée) : `table_analyse` ou `table_jour`."""
    with closing(sqlite3.connect(base)) as con:
        table.to_sql(nom, con, if_exists="replace", index=False)


def lire_table_enregistree(base: Path = BASE, nom: str = "table_analyse") -> pd.DataFrame:
    """Relit une table enregistrée par `python -m backend.train` (`table_analyse` ou `table_jour`)."""
    if not base.exists():
        raise FileNotFoundError(f"Base introuvable : {base}. {MESSAGE_RELANCE}")
    with closing(sqlite3.connect(base)) as con:
        existe = con.execute(
            "select count(*) from sqlite_master where type = 'table' and name = ?", (nom,)
        ).fetchone()[0]
        if not existe:
            raise FileNotFoundError(f"Table {nom} absente de {base}. {MESSAGE_RELANCE}")
        return pd.read_sql(f"select * from {nom}", con)


def lire_stations(base: Path = BASE) -> pd.DataFrame:
    """Lit la table SQLite `stations` (référentiel du flux quotidien, voir backend/sql/schema.sql)."""
    if not base.exists():
        raise FileNotFoundError(f"Base introuvable : {base}. {MESSAGE_RELANCE}")
    with closing(sqlite3.connect(base)) as con:
        return pd.read_sql("select * from stations", con)
