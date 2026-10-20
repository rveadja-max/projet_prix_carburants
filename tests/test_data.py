"""Tests du chargement des données brutes dans SQLite (mini-jeu de la fixture `base_test`)."""
import sqlite3
from contextlib import closing

import pytest

from backend.data import charger_brut_dans_sqlite


def requete(base, sql):
    with closing(sqlite3.connect(base)) as con:
        return con.execute(sql).fetchall()


def test_chargement_compte_les_tables(base_test):
    assert requete(base_test, "select count(*) from stations")[0][0] == 5
    assert requete(base_test, "select count(*) from brent where dollars_baril is null")[0][0] == 0
    assert requete(base_test, "select count(*) from brent where jour = '2026-01-12'")[0][0] == 0
    assert requete(base_test, "select max(jour) from brent")[0][0] <= "2026-01-31"
    assert requete(base_test, "select max(jour) from taux_change")[0][0] <= "2026-01-31"
    assert requete(base_test, "select count(*) from calendrier")[0][0] == 31


def test_chargement_ignore_prix_aberrants_et_dates_apres_fin(base_test):
    prix = requete(base_test, "select valeur, maj from prix where station='5900004'")
    assert len(prix) == 2
    assert all(0.8 <= v <= 3.5 and m <= "2026-01-31T23:59:59" for v, m in prix)


def test_chargement_garde_seulement_le_gazole(base_test):
    assert requete(base_test, "select count(*) from prix where station='5900001'")[0][0] == 31


def test_chargement_derive_departement_zone_et_dedoublonne(base_test):
    ligne = requete(base_test, "select departement, zone, ville from stations where station='5900003'")
    assert ligne == [("59", "A", "LILLE")]
    assert requete(base_test, "select count(*) from prix where station='5900002'")[0][0] == 10


def test_chargement_renvoie_les_comptes(tmp_path_factory, base_test):
    # La fixture a déjà chargé ; on recharge dans une autre base à partir des mêmes fichiers.
    dossier = base_test.parent
    comptes = charger_brut_dans_sqlite(
        [dossier / "PrixCarburants_annuel_2026.zip"], dossier / "brent.csv", dossier / "eurusd.csv",
        tmp_path_factory.mktemp("rec") / "b.db", date_fin="2026-01-31",
    )
    assert comptes["stations"] == 5
    assert comptes["prix_ignores"] == 2


def test_fichier_absent_leve_une_erreur(tmp_path):
    with pytest.raises(FileNotFoundError):
        charger_brut_dans_sqlite([tmp_path / "absent.zip"], base=tmp_path / "b.db")
