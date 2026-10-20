"""Tests du chargement SQLite et de la table d'analyse (mini-jeu de la fixture `base_test`)."""
import shutil
import sqlite3
from contextlib import closing

import pandas as pd
import pytest

from backend.data import (
    charger_brut_dans_sqlite, enregistrer_table_analyse, executer_requete_analyse, lire_table_analyse,
    lire_table_enregistree,
)


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


# --- Table d'analyse -------------------------------------------------------------------------
# Rappels sur le mini-jeu : 2026-01-01 est un jeudi. Brent et taux cotés les jours ouvrés seulement,
# Brent à 60 sauf 100 le jeudi 2026-01-15 et "." le lundi 2026-01-12 ; taux toujours à 1,10.
# Périmètre (59/62, zone R) : 5900001, 5900002, 5900004 (5900003 est en zone A, 7500001 à Paris).


@pytest.fixture(scope="module")
def table(base_test):
    return lire_table_analyse(base=base_test)


@pytest.fixture(scope="module")
def requete_seule(base_test):
    return executer_requete_analyse(base=base_test)


def test_une_ligne_par_station_et_par_jour(table):
    assert not table.duplicated(["station", "jour"]).any()


def test_perimetre_departements_et_zone(table):
    assert set(table["station"]) <= {"5900001", "5900002", "5900004"}


def test_prix_dans_les_bornes_et_cible_binaire(table):
    assert table["prix"].between(0.8, 3.5).all()
    assert set(table["hausse"]) <= {0, 1}


def test_brent_sans_fuite(table):
    # pic à 100 le 2026-01-15 : invisible le 15, visible le 16 (retard 1 jour) ;
    # invisible jusqu'au 22, visible le 23 (retard 8 jours)
    ligne = table[table.station == "5900001"].set_index("jour")
    assert ligne.loc["2026-01-15", "brent_eur"] == pytest.approx(60 / 1.10)
    assert ligne.loc["2026-01-16", "brent_eur"] == pytest.approx(100 / 1.10)
    assert ligne.loc["2026-01-22", "brent_eur_realiste"] == pytest.approx(60 / 1.10)
    assert ligne.loc["2026-01-23", "brent_eur_realiste"] == pytest.approx(100 / 1.10)


def test_brent_reporte_le_week_end(requete_seule):
    # le 2026-01-13 (veille = lundi 12, valeur ".") a le brent du vendredi 2026-01-09 ;
    # le lundi 2026-01-12 (veille = dimanche 11) a aussi celui du vendredi 9.
    ligne = requete_seule[requete_seule.station == "5900001"].set_index("jour")
    for jour in ("2026-01-12", "2026-01-13"):
        assert ligne.loc[jour, "brent_eur"] == pytest.approx(60 / 1.10)
        assert ligne.loc[jour, "taux"] == pytest.approx(1.10)
    # Les cotations commencent le 2025-12-01 : aucun jour du calendrier n'est sans Brent ni taux.
    assert requete_seule[["brent_eur", "brent_eur_realiste", "taux"]].notna().all().all()


def test_taux_sans_fuite(base_test, tmp_path):
    # Copie du mini-jeu où le taux du mardi 2026-01-20 passe à 1,25 : invisible le 20, visible le 21.
    base = tmp_path / "copie.db"
    shutil.copy(base_test, base)
    with closing(sqlite3.connect(base)) as con:
        con.execute("update taux_change set dollars_par_euro = 1.25 where jour = '2026-01-20'")
        con.commit()
    ligne = executer_requete_analyse(base)
    ligne = ligne[ligne.station == "5900001"].set_index("jour")
    assert ligne.loc["2026-01-20", "taux"] == pytest.approx(1.10)
    assert ligne.loc["2026-01-21", "taux"] == pytest.approx(1.25)
    assert ligne.loc["2026-01-21", "brent_eur"] == pytest.approx(60 / 1.25)


def test_prix_du_jour_ignore_les_mises_a_jour_apres_midi(table):
    # 5900002 : prix du 2026-01-10 = celui de 06:00 ; le 1,999 de 15:00 apparaît le 2026-01-11
    ligne = table[table.station == "5900002"].set_index("jour")
    assert ligne.loc["2026-01-10", "prix"] == pytest.approx(1.65)
    assert ligne.loc["2026-01-10", "date_maj"] == "2026-01-10T06:00:00"
    assert ligne.loc["2026-01-11", "prix"] == pytest.approx(1.999)
    assert ligne.loc["2026-01-11", "date_maj"] == "2026-01-10T15:00:00"
    # Cible du 2026-01-11 : prix du 14 (1,65 mis à jour le 14 à 06:00) - 1,999.
    assert ligne.loc["2026-01-11", "variation_future"] == pytest.approx(1.65 - 1.999)
    assert ligne.loc["2026-01-11", "hausse"] == 0


def test_station_muette_plus_de_7_jours_exclue(table, requete_seule):
    # 5900002 : dernière mise à jour le 2026-01-18 à 06:00, donc prix connu jusqu'au 25 (report de 7 jours) ;
    # le prix à J+3 étant exigé, aucune ligne après le 2026-01-22
    sql = requete_seule[requete_seule.station == "5900002"].set_index("jour")
    assert sql.loc["2026-01-25", "prix"] == pytest.approx(1.65)
    assert pd.isna(sql.loc["2026-01-26", "prix"])
    assert table.loc[table.station == "5900002", "jour"].max() == "2026-01-22"


def test_jointure_marche_ne_duplique_pas(requete_seule):
    # nombre de lignes du SQL seul == nombre de couples (calendrier × stations du périmètre) = 31 × 3
    assert len(requete_seule) == 31 * 3
    assert not requete_seule.duplicated(["station", "jour"]).any()


def test_variables_calculees_sur_le_passe(table):
    # 5900001 : prix 1,60 + 0,01 × (jour // 4), mis à jour chaque jour à 06:00.
    ligne = table[table.station == "5900001"].set_index("jour")
    assert ligne.loc["2026-01-12", "var_prix_1j"] == pytest.approx(0.01)       # 1,63 - 1,62
    assert ligne.loc["2026-01-12", "var_prix_7j"] == pytest.approx(0.02)       # 1,63 - 1,61 (le 5)
    assert ligne.loc["2026-01-12", "jours_depuis_changement"] == 0
    assert ligne.loc["2026-01-15", "jours_depuis_changement"] == 3
    assert ligne.loc["2026-01-11", "variation_future"] == pytest.approx(0.01)  # 1,63 (le 14) - 1,62
    assert ligne.loc["2026-01-11", "hausse"] == 1
    assert ligne.loc["2026-01-12", "hausse"] == 0                              # 1,63 le 12 et le 15
    assert ligne.loc["2026-01-12", "age_prix_jours"] == 0
    assert ligne.loc["2026-01-12", "jour_semaine"] == 0                        # lundi
    assert ligne.loc["2026-01-16", "var_brent_7j"] == pytest.approx(40 / 1.10)
    assert ligne.loc["2026-01-16", "var_taux_7j"] == pytest.approx(0.0)
    # 5900002 : prix reporté du 2026-01-12 (06:00) au 2026-01-13, donc âge 1 jour.
    assert table.set_index(["station", "jour"]).loc[("5900002", "2026-01-13"), "age_prix_jours"] == 1


def test_aucune_variable_manquante(table):
    assert not table.isna().any().any()
    assert table["jour"].str.fullmatch(r"\d{4}-\d{2}-\d{2}").all()


def test_table_enregistree_aller_retour(table, tmp_path):
    base = tmp_path / "b.db"
    with pytest.raises(FileNotFoundError, match="python -m backend.train"):
        lire_table_enregistree(base)
    sqlite3.connect(base).close()
    with pytest.raises(FileNotFoundError, match="python -m backend.train"):
        lire_table_enregistree(base)
    enregistrer_table_analyse(table, base)
    relue = lire_table_enregistree(base)
    assert len(relue) == len(table)
    assert list(relue.columns) == list(table.columns)


def test_base_absente_leve_une_erreur(tmp_path):
    with pytest.raises(FileNotFoundError, match="python -m backend.train"):
        lire_table_analyse(base=tmp_path / "absente.db")
