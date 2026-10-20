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


def ecrire_brent(chemin: Path) -> None:
    lignes = ["observation_date,DCOILBRENTEU"]
    for jour in jours_ouvres(date(2025, 12, 1), date(2026, 2, 2)):  # 2026-02-02 est après date_fin
        valeur = "." if jour == date(2026, 1, 12) else "100.0" if jour == date(2026, 1, 15) else "60.0"
        lignes.append(f"{jour},{valeur}")
    chemin.write_text("\n".join(lignes) + "\n", encoding="utf-8")


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
    ecrire_brent(dossier / "brent.csv")
    ecrire_taux(dossier / "eurusd.csv")
    base = dossier / "test.db"
    charger_brut_dans_sqlite(
        [archive], dossier / "brent.csv", dossier / "eurusd.csv", base, date_fin=DATE_FIN_TEST
    )
    return base


@pytest.fixture(scope="session")
def modele_entraine():
    if not FICHIER_MODELE.exists():
        train.main()
