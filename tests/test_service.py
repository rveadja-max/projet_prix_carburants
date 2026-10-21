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


def test_alternatives_refuse_une_station_inconnue(modele_entraine):
    with pytest.raises(ValueError, match="Station inconnue"):
        service.alternatives("0000000")


def test_alternatives_proches_et_rentables(modele_entraine):
    from backend.config import NB_ALTERNATIVES, RAYON_KM

    stations = service.lister_stations()["station"]
    resultats = [service.alternatives(s) for s in stations.iloc[:40]]
    non_vides = [r for r in resultats if not r.empty]
    assert non_vides, "aucune alternative sur 40 stations : vérifier les coordonnées"
    for r in non_vides:
        assert {"station", "ville", "adresse", "distance_km", "gain_c_l", "gain_plein_euros"} <= set(r.columns)
        assert len(r) <= NB_ALTERNATIVES
        assert (r["distance_km"] <= RAYON_KM).all() and (r["gain_plein_euros"] > 0).all()
        assert r["gain_plein_euros"].is_monotonic_decreasing
