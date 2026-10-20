"""Tests de l'interface du backend (modèle et métriques produits par backend.train)."""
import pytest

from backend import service


def test_conseiller_refuse_une_station_inconnue(modele_entraine):
    with pytest.raises(ValueError, match="Station inconnue"):
        service.conseiller("0000000", "2026-06-01")


def test_conseiller_refuse_une_date_hors_test(modele_entraine):
    station = service.lister_stations()["station"].iloc[0]
    with pytest.raises(ValueError, match="période de test"):
        service.conseiller(station, "2025-03-01")


def test_conseiller_renvoie_une_decision(modele_entraine):
    station = service.lister_stations()["station"].iloc[0]
    jour = service.jours_disponibles(station)[0]
    r = service.conseiller(station, jour)
    assert 0 <= r["proba_hausse"] <= 1
    assert r["decision"] in {"faire le plein", "attendre 3 jours"}
    assert r["decision"] == ("faire le plein" if r["proba_hausse"] > r["seuil"] else "attendre 3 jours")
    assert r["seuil"] == pytest.approx(service.metriques()["seuil"])


def test_profils_segments(modele_entraine):
    assert len(service.profils_segments(3)) == 3
