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


def test_conseil_du_jour_utilise_le_modele_retenu(modele_entraine):
    m = service.metriques()
    for station in service.lister_stations()["station"].iloc[:30]:
        try:
            r = service.conseil_du_jour(station)
        except ValueError as erreur:
            assert "Pas de conseil" in str(erreur)
            continue
        assert r["jour"] == m["qualite"]["jour_conseil"]
        assert r["decision"] == ("faire le plein" if r["proba_hausse"] > r["seuil"] else "attendre 3 jours")
        assert 0.5 < r["taux"] < 2
        return
    pytest.fail("aucun conseil du jour sur 30 stations : vérifier table_jour")


def test_etat_station_vient_du_flux(modele_entraine):
    station = service.lister_stations()["station"].iloc[0]
    etat = service.etat_station(station)
    assert {"prix_jour", "maj_prix_jour", "fermee", "rupture", "automate_24_24", "prix_frais"} <= set(etat)
    with pytest.raises(ValueError, match="Station inconnue"):
        service.etat_station("0000000")


def test_carte_et_croisement_des_sources(modele_entraine):
    carte = service.carte_reseau()
    assert carte["latitude"].between(49.5, 51.5).all() and carte["longitude"].between(1, 4.5).all()
    assert set(carte["etat"]) <= {"ouverte", "prix absent ou périmé", "rupture de gazole", "fermée"}
    serie = service.serie_marche()
    assert list(serie.columns) == ["jour", "gazole", "euro_dollar"]
    assert serie.iloc[0][["gazole", "euro_dollar"]].tolist() == [100, 100]


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
        assert {"station", "ville", "adresse", "prix_jour", "distance_km", "gain_c_l", "gain_plein_euros"} <= set(r.columns)
        assert not r["station"].isin(service.carte_reseau().query("etat != 'ouverte'")["station"]).any()
        assert len(r) <= NB_ALTERNATIVES
        assert (r["distance_km"] <= RAYON_KM).all() and (r["gain_plein_euros"] > 0).all()
        assert r["gain_plein_euros"].is_monotonic_decreasing
