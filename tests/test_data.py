"""Tests du chargement SQLite et de la table d'analyse (mini-jeu de la fixture `base_test`)."""
import shutil
import sqlite3
from contextlib import closing

import pandas as pd
import pytest

from backend.data import (
    charger_brut_dans_sqlite, convertir_coordonnee, lire_flux_quotidien, lire_position,
    enregistrer_table_analyse, executer_requete_analyse, lire_table_analyse,
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


def test_chargement_garde_les_coordonnees_en_degres(base_test):
    # Le XML donne les coordonnées en cent-millièmes de degré : 5000000 -> 50,0°.
    ligne = requete(base_test, "select latitude, longitude from stations where station='5900001'")
    assert ligne == [(pytest.approx(50.0), pytest.approx(3.0))]


def test_convertir_coordonnee():
    assert convertir_coordonnee("4620100") == pytest.approx(46.201)
    assert convertir_coordonnee("-55300") == pytest.approx(-0.553)
    assert convertir_coordonnee("") is None
    assert convertir_coordonnee(None) is None
    assert convertir_coordonnee("0") is None  # station sans position connue
    assert convertir_coordonnee("3.892") == pytest.approx(3.892)  # déjà en degrés (station 59750006)


def test_lire_position_corrige_les_inversions_vues_dans_les_archives():
    assert lire_position("5062565.00168", "303513.857653") == pytest.approx((50.6256500168, 3.03513857653))
    # Latitude et longitude inversées (stations 59000011 et 62360005), parfois déjà en degrés (59750006).
    assert lire_position("302417.918393", "5061699.11034") == pytest.approx((50.6169911034, 3.02417918393))
    assert lire_position("3.892", "50.282") == pytest.approx((50.282, 3.892))
    assert lire_position("", "") == (None, None)
    # Hors métropole, une latitude plus petite que la longitude est normale (La Réunion) : pas d'inversion.
    assert lire_position("-2090000", "5550000") == pytest.approx((-20.9, 55.5))


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


def copie_modifiee(base_test, dossier, modification: str):
    """Copie le mini-jeu dans `dossier` et y applique une requête de modification."""
    base = dossier / "copie.db"
    shutil.copy(base_test, base)
    with closing(sqlite3.connect(base)) as con:
        con.execute(modification)
        con.commit()
    return base


def test_brent_reporte_le_week_end(base_test, requete_seule, tmp_path):
    # Copie où le Brent du vendredi 2026-01-09 passe à 70 (60 ailleurs, 100 le 15).
    base = copie_modifiee(base_test, tmp_path, "update brent set dollars_baril = 70 where jour = '2026-01-09'")
    ligne = executer_requete_analyse(base)
    ligne = ligne[ligne.station == "5900001"].set_index("jour")
    assert ligne.loc["2026-01-09", "brent_eur"] == pytest.approx(60 / 1.10)  # veille = jeudi 8 : 60
    assert ligne.loc["2026-01-10", "brent_eur"] == pytest.approx(70 / 1.10)  # veille = vendredi 9
    assert ligne.loc["2026-01-12", "brent_eur"] == pytest.approx(70 / 1.10)  # veille = dimanche 11 -> vendredi 9
    assert ligne.loc["2026-01-13", "brent_eur"] == pytest.approx(70 / 1.10)  # veille = lundi 12 "." -> vendredi 9
    assert ligne.loc["2026-01-14", "brent_eur"] == pytest.approx(60 / 1.10)  # veille = mardi 13 : 60
    # Les cotations commencent le 2025-12-01 : aucun jour du calendrier n'est sans Brent ni taux.
    assert requete_seule[["brent_eur", "brent_eur_realiste", "taux"]].notna().all().all()


def test_taux_sans_fuite(base_test, tmp_path):
    # Copie du mini-jeu où le taux du mardi 2026-01-20 passe à 1,25 : invisible le 20, visible le 21.
    base = copie_modifiee(
        base_test, tmp_path, "update taux_change set dollars_par_euro = 1.25 where jour = '2026-01-20'"
    )
    ligne = executer_requete_analyse(base)
    ligne = ligne[ligne.station == "5900001"].set_index("jour")
    assert ligne.loc["2026-01-20", "taux"] == pytest.approx(1.10)
    assert ligne.loc["2026-01-21", "taux"] == pytest.approx(1.25)
    assert ligne.loc["2026-01-21", "brent_eur"] == pytest.approx(60 / 1.25)
    assert ligne.loc["2026-01-22", "taux"] == pytest.approx(1.10)  # veille = 21 : 1,10
    # var_taux_7j = taux(J) - taux(J-7), sur la table complète.
    table = lire_table_analyse(base)
    ligne = table[table.station == "5900001"].set_index("jour")
    assert ligne.loc["2026-01-21", "var_taux_7j"] == pytest.approx(1.25 - 1.10)  # taux du 21 - taux du 14
    assert ligne.loc["2026-01-28", "var_taux_7j"] == pytest.approx(1.10 - 1.25)  # taux du 28 - taux du 21
    assert ligne.loc["2026-01-14", "var_taux_7j"] == pytest.approx(0.0)  # avant : 1,10 - 1,10 (le 21 n'entre pas)


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
    # var_prix_3j = prix(J) - prix(J-3) : le 12, 1,63 - 1,62 (le 9) ; le 15, 1,63 - 1,63 (le 12).
    # (une version tournée vers l'avant donnerait 0 le 12 et 0,01 le 15)
    assert ligne.loc["2026-01-12", "var_prix_3j"] == pytest.approx(0.01)
    assert ligne.loc["2026-01-15", "var_prix_3j"] == pytest.approx(0.0)
    # Brent réaliste (cotation <= J-8) : le 23 voit le 100 du 15, le 16 voit le 8 -> 60.
    # var_brent_realiste_7j le 23 = 100/1,10 - 60/1,10 ; le 16 = 60/1,10 (le 8) - 60/1,10 (le 1er) = 0.
    assert ligne.loc["2026-01-23", "var_brent_realiste_7j"] == pytest.approx(40 / 1.10)
    assert ligne.loc["2026-01-16", "var_brent_realiste_7j"] == pytest.approx(0.0)
    # 5900002 : prix reporté du 2026-01-12 (06:00) au 2026-01-13, donc âge 1 jour.
    assert table.set_index(["station", "jour"]).loc[("5900002", "2026-01-13"), "age_prix_jours"] == 1


def test_mediane_du_departement(table):
    # Le 2026-01-16 dans le 59 : 5900001 = 1,60 + 0,01 × 4 = 1,64 ; 5900002 = 1,65 (mis à jour le 16) ;
    # 5900004 muet (dernière mise à jour le 6). Médiane = (1,64 + 1,65) / 2 = 1,645.
    # Le 2026-01-09 : 5900001 = 1,62 ; 5900002 = 1,65 (du 8) ; 5900004 = 1,71 (du 6). Médiane = 1,65.
    # Le 2026-01-23 : 5900001 = 1,65 ; 5900002 = 1,65 (du 18). Médiane = 1,65.
    lignes = table.set_index(["station", "jour"])
    assert lignes.loc[("5900001", "2026-01-16"), "ecart_mediane_dep"] == pytest.approx(1.64 - 1.645)
    assert lignes.loc[("5900002", "2026-01-16"), "ecart_mediane_dep"] == pytest.approx(1.65 - 1.645)
    # var_mediane_dep_7j le 16 = 1,645 - 1,65 (le 9).
    for station in ("5900001", "5900002"):
        assert lignes.loc[(station, "2026-01-16"), "var_mediane_dep_7j"] == pytest.approx(1.645 - 1.65)
    # Le 18 : 1,64 et 1,65 -> 1,645. Le 11 : 1,62 ; 1,999 (du 10 à 15:00) ; 1,71 -> 1,71.
    # var_mediane_dep_7j le 18 = 1,645 - 1,71 = -0,065. Vers l'avant (le 25 : 1,66 et 1,65 -> 1,655)
    # on aurait 1,645 - 1,655 = -0,01.
    assert lignes.loc[("5900001", "2026-01-18"), "var_mediane_dep_7j"] == pytest.approx(1.645 - 1.71)


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


# --- Flux quotidien (lien stable data.gouv.fr) -------------------------------------------------


def test_lire_flux_quotidien_filtre_carburant_bornes_et_date(tmp_path):
    flux = tmp_path / "prix_quotidien.csv"
    flux.write_text(
        "id;cp;pop;adresse;ville;prix_nom;prix_valeur;prix_maj;geom\n"
        "5900001;59000;R;1 rue de l'Église;LILLE;Gazole;1.62;2026-10-20 06:00:00;3.05,50.63\n"
        "5900001;59000;R;1 rue de l'Église;LILLE;SP95;1.75;2026-10-20 06:00:00;3.05,50.63\n"
        "5900002;59100;R;2 rue de la Paix;ROUBAIX;Gazole;9.99;2026-10-20 06:00:00;3.17,50.69\n"
        "5900003;59200;R;3 rue du Nord;TOURCOING;Gazole;1.65;2026-12-31 06:00:00;3.16,50.72\n"
        "5900004;59300;R;4 rue du Sud;VALENCIENNES;Gazole;1.55;2026-10-19 06:00:00;3.52,50.36\n",
        encoding="utf-8",
    )
    base = tmp_path / "b.db"
    with closing(sqlite3.connect(base)) as con:
        con.executescript(
            "create table stations (station TEXT PRIMARY KEY, cp TEXT, departement TEXT, zone TEXT,"
            " ville TEXT, adresse TEXT, latitude REAL, longitude REAL);"
            "create table prix (station TEXT, maj TEXT, valeur REAL);"
        )
        ignores = lire_flux_quotidien(flux, "2026-10-20", con)
        stations = con.execute(
            "select station, departement, latitude, longitude from stations order by station"
        ).fetchall()
        prix = con.execute("select station, maj, valeur from prix order by station").fetchall()

    # Le SP95 est sauté sans comptage (autre carburant, comme dans l'archive XML) ;
    # 9,99 (hors bornes) et le 2026-12-31 (après date_fin) sont comptés comme ignorés.
    assert ignores == 2
    assert stations == [
        ("5900001", "59", pytest.approx(50.63), pytest.approx(3.05)),
        ("5900004", "59", pytest.approx(50.36), pytest.approx(3.52)),
    ]
    assert prix == [
        ("5900001", "2026-10-20T06:00:00", pytest.approx(1.62)),
        ("5900004", "2026-10-19T06:00:00", pytest.approx(1.55)),
    ]
