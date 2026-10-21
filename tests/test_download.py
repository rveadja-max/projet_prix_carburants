"""Tests du téléchargement des données brutes (sans accès réseau)."""
import io
import json
import zipfile

import pytest

from backend import download


def fabriquer_zip() -> bytes:
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w") as archive:
        archive.writestr("PrixCarburants_annuel_2025.xml", "<pdv_liste></pdv_liste>")
    return tampon.getvalue()


def faux_ouvreur(contenu: bytes, appels: list):
    def ouvrir_url(url, delai):
        appels.append(url)
        return io.BytesIO(contenu)

    return ouvrir_url


def test_url_archive_contient_annee():
    assert download.url_archive(2025).endswith("/opendata/annee/2025")


def test_telechargement_ecrit_zip_valide_et_empreinte(tmp_path):
    contenu = fabriquer_zip()
    appels = []

    entree = download.telecharger_archive(2025, tmp_path, ouvrir_url=faux_ouvreur(contenu, appels))

    cible = tmp_path / "PrixCarburants_annuel_2025.zip"
    assert cible.read_bytes() == contenu
    assert entree["sha256"] == download.empreinte_sha256(cible)
    assert entree["size_bytes"] == len(contenu)
    assert entree["url"] == appels[0]


def test_archive_presente_pas_retelechargee(tmp_path):
    (tmp_path / "PrixCarburants_annuel_2025.zip").write_bytes(fabriquer_zip())
    appels = []

    entree = download.telecharger_archive(2025, tmp_path, ouvrir_url=faux_ouvreur(b"", appels))

    assert entree is None
    assert appels == []


def test_forcer_retelecharge(tmp_path):
    (tmp_path / "PrixCarburants_annuel_2025.zip").write_bytes(b"ancien")
    appels = []

    entree = download.telecharger_archive(
        2025, tmp_path, forcer=True, ouvrir_url=faux_ouvreur(fabriquer_zip(), appels)
    )

    assert entree is not None
    assert len(appels) == 1


def test_archive_invalide_rejetee_et_supprimee(tmp_path):
    with pytest.raises(ValueError):
        download.telecharger_archive(
            2025, tmp_path, ouvrir_url=faux_ouvreur(b"<html>erreur</html>", [])
        )

    assert list(tmp_path.iterdir()) == []


def test_manifeste_garde_les_entrees_precedentes(tmp_path):
    manifeste = tmp_path / "manifest.json"
    download.mettre_a_jour_manifeste([{"file": "a.zip", "sha256": "1"}], manifeste)
    download.mettre_a_jour_manifeste([{"file": "b.zip", "sha256": "2"}], manifeste)

    contenu = json.loads(manifeste.read_text(encoding="utf-8"))

    assert set(contenu) == {"a.zip", "b.zip"}


def test_csv_valide_ecrit_avec_empreinte(tmp_path):
    contenu = b"KEY,FREQ,TIME_PERIOD,OBS_VALUE\nEXR.D.USD.EUR.SP00.A,D,2026-10-13,1.16\n"
    cible = tmp_path / "eurusd.csv"
    entree = download.telecharger_csv("http://x", cible, "KEY,",
                                      ouvrir_url=faux_ouvreur(contenu, []))
    assert cible.read_bytes() == contenu
    assert entree["sha256"] == download.empreinte_sha256(cible)


def test_csv_avec_mauvais_entete_rejete(tmp_path):
    cible = tmp_path / "eurusd.csv"
    with pytest.raises(ValueError):
        download.telecharger_csv("http://x", cible, "KEY,",
                                 ouvrir_url=faux_ouvreur(b"<html>erreur</html>", []))
    assert list(tmp_path.iterdir()) == []


def test_flux_quotidien_garde_la_page_source(tmp_path):
    contenu = "\ufeffCode postal;pop;adresse\n59000;R;1 rue\n".encode("utf-8")
    cible = tmp_path / "flux_quotidien.csv"
    entree = download.telecharger_csv("http://x", cible, "Code postal;", page_source="http://page",
                                      ouvrir_url=faux_ouvreur(contenu, []))
    assert entree["source_page"] == "http://page" and entree["url"] == "http://x"
