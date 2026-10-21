"""Tests du chargement SQLite et de la table d'analyse (mini-jeu de la fixture `base_test`)."""
import shutil
import sqlite3
from contextlib import closing

import pandas as pd
import pytest

from backend.data import (
    calculer_variables, charger_brut_dans_sqlite, enregistrer_table_analyse, executer_requete_analyse, fermee_le,
    heure_locale, lignes_du_jour, lire_flux, lire_table_analyse, lire_table_enregistree,
)


def requete(base, sql):
    with closing(sqlite3.connect(base)) as con:
        return con.execute(sql).fetchall()


def test_chargement_compte_les_tables(base_test):
    assert requete(base_test, "select count(*) from stations")[0][0] == 6            # flux : 6 stations
    assert requete(base_test, "select count(*) from stations_historique")[0][0] == 5  # archives
    assert requete(base_test, "select max(jour) from taux_change")[0][0] <= "2026-01-31"
    # Calendrier du premier prix au jour du conseil (lendemain de la date de fin).
    assert requete(base_test, "select min(jour), max(jour), count(*) from calendrier")[0] == (
        "2026-01-01", "2026-02-01", 32)


def test_chargement_ignore_prix_aberrants_et_dates_apres_fin(base_test):
    prix = requete(base_test, "select valeur, maj from prix where station='5900004'")
    assert len(prix) == 2
    assert all(0.8 <= v <= 3.5 and m <= "2026-01-31T23:59:59" for v, m in prix)
    # Le prix du flux daté du 5 février (après la fin) n'entre ni dans l'historique ni dans le prix du jour.
    assert requete(base_test, "select max(maj) from prix where station='5900002'")[0][0] < "2026-02"
    assert requete(base_test, "select prix_jour from stations where station='5900002'") == [(None,)]


def test_chargement_garde_seulement_le_gazole_et_dedoublonne_le_flux(base_test):
    # 31 prix de l'archive ; le prix du flux du 31 à 06:00 est un doublon exact, le SP95 est ignoré.
    assert requete(base_test, "select count(*) from prix where station='5900001'")[0][0] == 31


def test_chargement_derive_departement_zone_et_dedoublonne(base_test):
    ligne = requete(base_test, "select departement, zone, ville from stations where station='5900003'")
    assert ligne == [("59", "A", "LILLE")]
    assert requete(base_test, "select count(*) from prix where station='5900002'")[0][0] == 10


def test_referentiel_du_flux(base_test):
    lignes = {
        station: (lat, lon, prix, maj, fermee, rupture, automate)
        for station, lat, lon, prix, maj, fermee, rupture, automate in requete(
            base_test, "select station, latitude, longitude, prix_jour, maj_prix_jour, fermee, rupture, "
                       "automate_24_24 from stations")
    }
    assert lignes["5900001"] == (pytest.approx(50.0), pytest.approx(3.0), pytest.approx(1.67),
                                 "2026-01-31T06:00:00", 0, 0, 1)
    assert lignes["5900002"][4:6] == (0, 1)        # rupture de gazole en cours
    assert lignes["5900004"][4] == 1               # fermeture définitive depuis le 20 janvier
    assert lignes["5900005"][:3] == (None, None, pytest.approx(1.50))  # sans position, prix de 2015 gardé
    # Ce prix ancien n'entre pas dans l'historique : il ferait remonter le calendrier à 2015.
    assert requete(base_test, "select count(*) from prix where station='5900005'")[0][0] == 0


def test_heure_locale_retire_le_suffixe_utc_trompeur():
    assert heure_locale("2026-10-20T07:31:00+00:00") == "2026-10-20T07:31:00"
    assert heure_locale("") is None and heure_locale(None) is None


def test_fermee_le():
    temporaire = '{"@type": "T", "@debut": "2026-10-19T00:00:00", "@fin": "2026-10-24T00:00:00"}'
    assert fermee_le(temporaire, "2026-10-21")
    assert not fermee_le(temporaire, "2026-10-25") and not fermee_le(temporaire, "2026-10-18")
    assert fermee_le('[{"@type": "D", "@debut": "2009-02-01T00:00:00", "@fin": ""}]', "2026-10-21")
    assert not fermee_le("", "2026-10-21") and not fermee_le(None, "2026-10-21")


def test_jour_du_conseil_lendemain_du_dernier_prix(base_test):
    _, jour = lire_flux(base_test.parent / "flux_quotidien.csv")
    assert jour == "2026-02-06"  # dernier prix publié : 2026-02-05
    _, jour = lire_flux(base_test.parent / "flux_quotidien.csv", date_fin="2026-01-31")
    assert jour == "2026-02-01"


def test_chargement_renvoie_les_comptes(tmp_path_factory, base_test):
    # La fixture a déjà chargé ; on recharge dans une autre base à partir des mêmes fichiers.
    dossier = base_test.parent
    comptes = charger_brut_dans_sqlite(
        [dossier / "PrixCarburants_annuel_2026.zip"], dossier / "flux_quotidien.csv", dossier / "eurusd.csv",
        tmp_path_factory.mktemp("rec") / "b.db", date_fin="2026-01-31",
    )
    assert comptes["stations"] == 6 and comptes["stations_historique"] == 5
    assert comptes["prix_ignores"] == 2
    assert comptes["jour_conseil"] == "2026-02-01"


def test_fichier_absent_leve_une_erreur(tmp_path):
    with pytest.raises(FileNotFoundError):
        charger_brut_dans_sqlite([tmp_path / "absent.zip"], base=tmp_path / "b.db")


# --- Table d'analyse -------------------------------------------------------------------------
# Rappels sur le mini-jeu : 2026-01-01 est un jeudi. Taux coté les jours ouvrés seulement, toujours à 1,10.
# Calendrier jusqu'au 2026-02-01, jour du conseil.
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


def copie_modifiee(base_test, dossier, modification: str):
    """Copie le mini-jeu dans `dossier` et y applique une requête de modification."""
    base = dossier / "copie.db"
    shutil.copy(base_test, base)
    with closing(sqlite3.connect(base)) as con:
        con.execute(modification)
        con.commit()
    return base


def test_taux_reporte_le_week_end(base_test, requete_seule, tmp_path):
    # Copie où le taux du vendredi 2026-01-09 passe à 1,20 (1,10 ailleurs).
    base = copie_modifiee(base_test, tmp_path, "update taux_change set dollars_par_euro = 1.20 where jour = '2026-01-09'")
    ligne = executer_requete_analyse(base)
    ligne = ligne[ligne.station == "5900001"].set_index("jour")
    assert ligne.loc["2026-01-09", "taux"] == pytest.approx(1.10)  # veille = jeudi 8
    assert ligne.loc["2026-01-10", "taux"] == pytest.approx(1.20)  # veille = vendredi 9
    assert ligne.loc["2026-01-12", "taux"] == pytest.approx(1.20)  # veille = dimanche 11 -> vendredi 9
    assert ligne.loc["2026-01-13", "taux"] == pytest.approx(1.10)  # veille = lundi 12
    # Les cotations commencent le 2025-12-01 : aucun jour du calendrier n'est sans taux.
    assert requete_seule["taux"].notna().all()


def test_taux_sans_fuite(base_test, tmp_path):
    # Copie du mini-jeu où le taux du mardi 2026-01-20 passe à 1,25 : invisible le 20, visible le 21.
    base = copie_modifiee(
        base_test, tmp_path, "update taux_change set dollars_par_euro = 1.25 where jour = '2026-01-20'"
    )
    ligne = executer_requete_analyse(base)
    ligne = ligne[ligne.station == "5900001"].set_index("jour")
    assert ligne.loc["2026-01-20", "taux"] == pytest.approx(1.10)
    assert ligne.loc["2026-01-21", "taux"] == pytest.approx(1.25)
    assert ligne.loc["2026-01-22", "taux"] == pytest.approx(1.10)  # veille = 21 : 1,10
    # var_taux_7j = taux(J) - taux(J-7), sur la table complète.
    table = lire_table_analyse(base)
    ligne = table[table.station == "5900001"].set_index("jour")
    assert ligne.loc["2026-01-21", "var_taux_7j"] == pytest.approx(1.25 - 1.10)  # taux du 21 - taux du 14
    assert ligne.loc["2026-01-28", "var_taux_7j"] == pytest.approx(1.10 - 1.25)  # taux du 28 - taux du 21
    assert ligne.loc["2026-01-14", "var_taux_7j"] == pytest.approx(0.0)  # avant : 1,10 - 1,10 (le 21 n'entre pas)
    assert ligne.loc["2026-01-21", "var_taux_1j"] == pytest.approx(1.25 - 1.10)
    assert ligne.loc["2026-01-24", "var_taux_3j"] == pytest.approx(1.10 - 1.25)  # taux du 24 (du 23) - taux du 21


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
    # nombre de lignes du SQL seul == nombre de couples (calendrier × stations du périmètre) = 32 × 3
    assert len(requete_seule) == 32 * 3
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
    assert ligne.loc["2026-01-16", "var_taux_7j"] == pytest.approx(0.0)
    # var_prix_3j = prix(J) - prix(J-3) : le 12, 1,63 - 1,62 (le 9) ; le 15, 1,63 - 1,63 (le 12).
    # (une version tournée vers l'avant donnerait 0 le 12 et 0,01 le 15)
    assert ligne.loc["2026-01-12", "var_prix_3j"] == pytest.approx(0.01)
    assert ligne.loc["2026-01-15", "var_prix_3j"] == pytest.approx(0.0)
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


def test_metriques_figees_a_la_date_de_fin(base_test):
    # Seuls les jours dont le prix à J + 3 est connu au plus tard à la date de fin entrent dans la table.
    assert lire_table_analyse(base_test, date_fin="2026-01-20")["jour"].max() == "2026-01-17"


def test_lignes_du_jour_sans_cible(requete_seule):
    # Jour du conseil (2026-02-01) : 5900001 a un prix (du 31) et toutes ses variables ; 5900002, muette
    # depuis le 18, et 5900004, depuis le 6, n'ont pas de conseil.
    jour = lignes_du_jour(calculer_variables(requete_seule), "2026-02-01")
    assert list(jour["station"]) == ["5900001"]
    assert "variation_future" not in jour and "hausse" not in jour
    assert jour["prix"].iloc[0] == pytest.approx(1.67)
