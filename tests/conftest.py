"""Fixture partagée : un mini-jeu de données chargé dans une base SQLite de test."""
import zipfile
from datetime import date, timedelta
from pathlib import Path

import pytest

from backend import train
from backend.config import FICHIER_MODELE
from backend.data import charger_brut_dans_sqlite

DATE_FIN_TEST = "2026-01-31"
JANVIER = [date(2026, 1, 1) + timedelta(days=i) for i in range(31)]


def ligne_prix(nom: str, maj: str, valeur: float) -> str:
    return f'<prix nom="{nom}" id="1" maj="{maj}" valeur="{valeur}"/>'


def ligne_station(identifiant: str, cp: str, zone: str, ville: str, prix: list[str]) -> str:
    return (
        f'<pdv id="{identifiant}" latitude="5000000" longitude="300000" cp="{cp}" pop="{zone}">'
        f"<adresse>1 rue de l'Église</adresse><ville>{ville}</ville>{''.join(prix)}</pdv>"
    )


def fabriquer_xml() -> str:
    prix_lille = [
        ligne_prix("Gazole", f"{jour}T06:00:00", round(1.60 + 0.01 * (jour.day // 4), 2)) for jour in JANVIER
    ]
    prix_lille.append(ligne_prix("SP95", "2026-01-01T06:00:00", 1.75))
    prix_lille.append(ligne_prix("Gazole", "2026-01-01T06:00:00", 1.60))  # doublon exact à dédoublonner
    prix_roubaix = [
        ligne_prix("Gazole", f"{jour}T06:00:00", 1.65) for jour in JANVIER if jour.day % 2 == 0 and jour.day < 20
    ]
    prix_roubaix.append(ligne_prix("Gazole", "2026-01-10T15:00:00", 1.999))
    prix_aberrants = [
        ligne_prix("Gazole", "2026-01-05T06:00:00", 1.70),
        ligne_prix("Gazole", "2026-01-06T06:00:00", 1.71),
        ligne_prix("Gazole", "2026-01-07T06:00:00", 9.99),
        ligne_prix("Gazole", "2026-02-05T06:00:00", 1.72),
    ]
    stations = [
        ligne_station("5900001", "59000", "R", "LILLE", prix_lille),
        ligne_station("5900002", "59100", "R", "ROUBAIX", prix_roubaix),
        ligne_station("5900003", "59000", "A", "LILLE", [ligne_prix("Gazole", "2026-01-03T06:00:00", 1.80)]),
        ligne_station("7500001", "75001", "R", "PARIS", [ligne_prix("Gazole", "2026-01-03T06:00:00", 1.90)]),
        ligne_station("5900004", "59000", "R", "LILLE", prix_aberrants),
    ]
    return (
        '<?xml version="1.0" encoding="ISO-8859-1"?>\n<pdv_liste>' + "".join(stations) + "</pdv_liste>"
    )


def jours_ouvres(debut: date, fin: date) -> list[date]:
    jours = [debut + timedelta(days=i) for i in range((fin - debut).days + 1)]
    return [jour for jour in jours if jour.weekday() < 5]


ENTETE_FLUX = (
    "Code postal;pop;adresse;ville;geom;Mise à jour des prix;prix_id;Prix;Carburant;Carburant en rupture;"
    "Début rupture;Fin rupture;Automate 24-24 (oui/non);id;fermeture"
)


def ligne_flux(cp, zone, ville, geom, maj, prix, carburant, rupture, automate, station, fermeture="") -> str:
    fermeture = '"' + fermeture.replace('"', '""') + '"' if fermeture else ""
    return f"{cp};{zone};1 rue de l'Église;{ville};{geom};{maj};1;{prix};{carburant};{rupture};;;{automate};{station};{fermeture}"


def ecrire_flux(chemin: Path) -> None:
    """Mini flux quotidien (format réel : `;`, UTF-8 avec BOM, une ligne par carburant et par rupture)."""
    lignes = [
        ENTETE_FLUX,
        # Même prix que l'archive le 31 à 06:00 : doublon à supprimer de l'historique.
        ligne_flux("59000", "R", "LILLE", "50.0, 3.0", "2026-01-31T06:00:00+00:00", "1.67", "Gazole", "", "Oui", "5900001"),
        ligne_flux("59000", "R", "LILLE", "50.0, 3.0", "2026-01-31T06:00:00+00:00", "1.80", "SP95", "", "Oui", "5900001"),
        # Prix daté après la date de fin (ignoré) et rupture de gazole en cours (deux lignes pour une station).
        ligne_flux("59100", "R", "ROUBAIX", "50.69, 3.18", "2026-02-05T06:00:00+00:00", "1.70", "Gazole", "Gazole", "Non", "5900002"),
        ligne_flux("59100", "R", "ROUBAIX", "50.69, 3.18", "2026-02-05T06:00:00+00:00", "1.70", "Gazole", "SP95", "Non", "5900002"),
        ligne_flux("59000", "A", "LILLE", "50.01, 3.01", "2026-01-03T06:00:00+00:00", "1.80", "Gazole", "", "Non", "5900003"),
        ligne_flux("75001", "R", "PARIS", "48.86, 2.34", "2026-01-03T06:00:00+00:00", "1.90", "Gazole", "", "Non", "7500001"),
        # Fermeture définitive depuis le 20 janvier.
        ligne_flux("59000", "R", "LILLE", "50.02, 3.02", "", "", "", "", "Non", "5900004",
                   '{"@type": "D", "@debut": "2026-01-20T00:00:00", "@fin": ""}'),
        # Station absente des archives, sans position, au dernier prix très ancien (vu dans le flux réel).
        ligne_flux("59000", "R", "LILLE", "", "2015-03-02T06:00:00+00:00", "1.50", "Gazole", "", "Non", "5900005"),
    ]
    chemin.write_text("\n".join(lignes) + "\n", encoding="utf-8-sig")


def ecrire_taux(chemin: Path) -> None:
    lignes = ["KEY,FREQ,CURRENCY,TIME_PERIOD,OBS_VALUE,OBS_STATUS"]
    for jour in jours_ouvres(date(2025, 12, 1), date(2026, 2, 2)):
        lignes.append(f"EXR.D.USD.EUR.SP00.A,D,USD,{jour},1.10,A")
    chemin.write_text("\n".join(lignes) + "\n", encoding="utf-8")


@pytest.fixture(scope="session")
def base_test(tmp_path_factory) -> Path:
    dossier = tmp_path_factory.mktemp("mini_jeu")
    archive = dossier / "PrixCarburants_annuel_2026.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("PrixCarburants_annuel_2026.xml", fabriquer_xml().encode("iso-8859-1"))
    ecrire_flux(dossier / "flux_quotidien.csv")
    ecrire_taux(dossier / "eurusd.csv")
    base = dossier / "test.db"
    charger_brut_dans_sqlite(
        [archive], dossier / "flux_quotidien.csv", dossier / "eurusd.csv", base, date_fin=DATE_FIN_TEST
    )
    return base


@pytest.fixture(scope="session")
def modele_entraine():
    if not FICHIER_MODELE.exists():
        train.main()
