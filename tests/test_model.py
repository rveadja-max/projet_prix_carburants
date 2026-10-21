"""Tests unitaires de la logique métier (sans base de données)."""
import numpy as np
import pandas as pd
import pytest

from backend.model import (
    VARIABLES_PROFIL, VARIABLES_SANS_BRENT, cout_moyen, couts_moyens, couts_references,
    creer_pipeline, decouper_temporel, evaluer, profils_stations, regret, segmenter, seuil_optimal,
)


def test_seuil_issu_des_couts():
    assert seuil_optimal(3.0, 1.0) == pytest.approx(0.25)


def test_couts_moyens_comptent_les_zeros_dans_la_baisse():
    delta = pd.Series([0.02, 0.0, -0.01, 0.0])
    hausse = (delta > 0).astype(int)
    assert couts_moyens(delta, hausse) == pytest.approx((2.0, 1 / 3))


def test_regret_selon_la_decision():
    delta = np.array([0.02, -0.01])
    assert regret(delta, np.array([True, True])) == pytest.approx([0.0, 1.0])
    assert regret(delta, np.array([False, False])) == pytest.approx([2.0, 0.0])


def test_cout_moyen():
    delta = np.array([0.02, -0.01, 0.02, -0.01])   # +2 c, -1 c, +2 c, -1 c
    proba = np.array([0.9, 0.9, 0.1, 0.1])         # plein, plein, attendre, attendre
    # plein et hausse : 0 ; plein et baisse : 1 ; attendre et hausse : 2 ; attendre et baisse : 0
    assert cout_moyen(delta, proba, 0.5) == pytest.approx(3 / 4)


def test_references():
    r = couts_references(np.array([0.02, -0.01]))
    assert r["toujours_plein"] == pytest.approx(0.5)
    assert r["toujours_attendre"] == pytest.approx(1.0)
    assert r["oracle"] == 0.0


def test_split_temporel_sans_chevauchement():
    jours = pd.date_range("2026-04-25", "2026-05-10").strftime("%Y-%m-%d")
    entrainement, test = decouper_temporel(pd.DataFrame({"jour": jours, "station": "S1"}), "2026-04-30", 3)
    assert entrainement["jour"].max() == "2026-04-30"
    assert test["jour"].min() == "2026-05-04"


def test_segmenter_ajoute_k_segments():
    generateur = np.random.default_rng(42)
    profils = pd.DataFrame(generateur.normal(size=(30, 3)), columns=VARIABLES_PROFIL)
    resultat = segmenter(profils, k=3)
    assert set(resultat["segment"]) == {0, 1, 2}
    assert "segment" not in profils.columns


def test_profils_stations():
    table = pd.DataFrame({
        "station": [1, 1, 1, 1, 2, 2],
        "ecart_mediane_dep": [0.02, 0.04, 0.0, 0.02, -0.01, -0.01],
        "var_prix_1j": [0.0, 0.01, 0.0, -0.01, 0.0, 0.0],
    })
    profils = profils_stations(table, jours_min=2)
    assert list(profils.columns) == VARIABLES_PROFIL
    assert profils.loc[1, "prix_relatif"] == pytest.approx(2.0)
    assert profils.loc[1, "changements_par_semaine"] == pytest.approx(7 * 0.5)
    assert profils.loc[2, "changements_par_semaine"] == 0.0


def test_evaluer_et_pipeline():
    generateur = np.random.default_rng(0)
    X = pd.DataFrame(generateur.normal(size=(300, len(VARIABLES_SANS_BRENT))), columns=VARIABLES_SANS_BRENT)
    y = (X["var_prix_1j"] + 0.1 * generateur.normal(size=300) > 0).astype(int)
    delta = pd.Series(np.where(y == 1, 0.02, -0.01))
    pipeline = creer_pipeline().set_params(foret__min_samples_leaf=5)
    pipeline.fit(X[:200], y[:200])
    resultat = evaluer(pipeline, X[200:], y[200:], delta[200:], 0.3)
    assert resultat["roc_auc"] > 0.9
    assert set(resultat) == {"roc_auc", "cout_moyen_modele", "cout_moyen_seuil_05", "importance_permutation"}
    assert next(iter(resultat["importance_permutation"])) == "var_prix_1j"


def test_station_trop_courte_exclue_et_segmentation_possible():
    generateur = np.random.default_rng(1)
    stations = np.repeat(np.arange(10), 40)
    table = pd.DataFrame({
        "station": np.append(stations, 99),
        "ecart_mediane_dep": np.append(generateur.normal(size=400), 0.0),
        "var_prix_1j": np.append(generateur.normal(size=400), np.nan),
    })
    profils = profils_stations(table)
    assert 99 not in profils.index and len(profils) == 10
    assert set(segmenter(profils, k=2)["segment"]) == {0, 1}


def test_plis_temporels_purges_et_consecutifs():
    from backend.model import plis_temporels

    jours = pd.Series(sorted(pd.date_range("2026-01-01", periods=20).strftime("%Y-%m-%d").tolist() * 2))
    dates = pd.to_datetime(jours)
    plis = plis_temporels(jours, n_plis=3, purge_jours=3)
    assert len(plis) == 3
    for entrainement, validation in plis:
        assert not set(dates.iloc[entrainement]) & set(dates.iloc[validation])
        assert dates.iloc[entrainement].max() + pd.Timedelta(days=3) < dates.iloc[validation].min()
    # 20 jours en 4 blocs de 5 : validations = jours 6-10, 11-15, 16-20, consécutives.
    attendu = [(5, 10), (10, 15), (15, 20)]
    for (_, validation), (a, b) in zip(plis, attendu):
        assert list(dates.iloc[validation].dt.day.unique()) == list(range(a + 1, b + 1))


# --- Choix de la station : top-N des stations moins chères à proximité, net du coût du détour ---

def stations_voisines() -> pd.DataFrame:
    """A : station habituelle. B et E proches et moins chères ; C plus chère ; D trop loin ; F sans position."""
    un_km_lat = 1 / 111.195  # 1 km vers le nord, en degrés de latitude
    return pd.DataFrame({
        "station": ["A", "B", "C", "D", "E", "F"],
        "latitude": [50.0, 50.0 + un_km_lat, 50.0 + un_km_lat, 50.0 + 10 * un_km_lat, 50.0 + 0.1 * un_km_lat, None],
        "longitude": [3.0] * 6,
    })


def test_distance_un_degre_de_latitude():
    from backend.model import distance_km

    assert distance_km(50.0, 3.0, 51.0, 3.0) == pytest.approx(111.195, rel=1e-3)
    assert distance_km(50.0, 3.0, 50.0, 3.0) == pytest.approx(0.0)


def test_cout_du_detour():
    from backend.model import cout_detour_euros

    # Aller-retour de 1 km à vol d'oiseau : 2 × 1 × 1,3 = 2,6 km sur route.
    # Coût par km : carburant 9 L/100 km × 2 €/L = 0,18 € + chauffeur 30 €/h ÷ 30 km/h = 1 € -> 1,18 €.
    assert cout_detour_euros(1.0, 2.0) == pytest.approx(2.6 * 1.18)
    assert cout_detour_euros(0.0, 2.0) == 0.0


def test_alternatives_dans_le_rayon_moins_cheres_et_rentables():
    from backend.model import alternatives_station

    # Écart moyen au prix médian du département, en c€/L (appris sur l'entraînement).
    ecarts = pd.Series({"A": 5.0, "B": -5.0, "C": 8.0, "D": -20.0, "E": 4.0, "F": -30.0})
    resultat = alternatives_station(stations_voisines(), ecarts, "A", prix_litre=2.0, rayon_km=5, n=3)
    # B : 10 c€/L × 60 L = 6 € − 3,068 € de détour ; E : 1 c€/L × 60 L = 0,6 € − 0,307 €.
    # C plus chère, D hors rayon, F sans position : exclues.
    assert list(resultat["station"]) == ["B", "E"]
    assert resultat["gain_c_l"].tolist() == pytest.approx([10.0, 1.0])
    assert resultat["gain_plein_euros"].tolist() == pytest.approx([6 - 3.068, 0.6 - 0.3068], rel=1e-3)
    assert list(alternatives_station(stations_voisines(), ecarts, "A", 2.0, 5, n=1)["station"]) == ["B"]


def test_alternative_non_rentable_exclue():
    from backend.model import alternatives_station

    # 0,5 c€/L × 60 L = 0,30 € de gain, pour 3,07 € de détour : on reste à la station habituelle.
    ecarts = pd.Series({"A": 1.0, "B": 0.5})
    assert alternatives_station(stations_voisines().iloc[:2], ecarts, "A", 2.0, 5, n=3).empty


def test_evaluer_choix_station_sur_le_test():
    from backend.model import evaluer_choix_station

    stations = stations_voisines().iloc[:2]           # A et B, à 1 km
    ecarts_entrainement = pd.Series({"A": 5.0, "B": -5.0})  # B choisie pour A ; aucune alternative pour B
    ecarts_test = pd.Series({"A": 4.0, "B": -2.0})          # au test, B n'est plus que 6 c€/L moins chère
    r = evaluer_choix_station(stations, ecarts_entrainement, ecarts_test, prix_litre=2.0, rayon_km=5)
    assert r["nb_stations"] == 2
    assert r["part_avec_alternative"] == pytest.approx(0.5)
    # A : 6 c€/L réalisés ; B : reste, 0. Moyenne : 3 c€/L.
    assert r["gain_moyen_c_l"] == pytest.approx(3.0)
    # A : 6 c€/L × 60 L = 3,60 € − 3,068 € ; B : 0. Moyenne par plein :
    assert r["gain_moyen_plein_euros"] == pytest.approx((3.6 - 3.068) / 2, rel=1e-3)
    assert r["economie_annuelle_euros"] == pytest.approx(r["gain_moyen_plein_euros"] * 40 * 52)


def test_station_sur_la_tournee_sans_cout_de_detour():
    from backend.model import alternatives_station, evaluer_choix_station

    # Plafond du levier : la station moins chère est sur la tournée, aucun détour à payer.
    ecarts = pd.Series({"A": 1.0, "B": 0.5})
    r = alternatives_station(stations_voisines().iloc[:2], ecarts, "A", 2.0, 5, n=3, avec_detour=False)
    assert list(r["station"]) == ["B"] and r["gain_plein_euros"].iloc[0] == pytest.approx(0.30)
    e = evaluer_choix_station(stations_voisines().iloc[:2], ecarts, pd.Series({"A": 1.0, "B": 0.0}), 2.0, 5,
                              avec_detour=False)
    assert e["gain_moyen_c_l"] == pytest.approx(0.5) and e["gain_moyen_plein_euros"] == pytest.approx(0.30)


# --- Intervalle de confiance du gain : bootstrap par blocs de jours consécutifs ---

def test_intervalle_gain_nul_si_strategies_identiques():
    from backend.model import intervalle_gain

    jours = pd.Series(pd.date_range("2026-05-01", periods=28).strftime("%Y-%m-%d"))
    regrets = np.linspace(0, 2, 28)
    assert intervalle_gain(jours, regrets, regrets) == pytest.approx({"moyenne": 0.0, "bas": 0.0, "haut": 0.0})


def test_intervalle_gain_constant():
    from backend.model import intervalle_gain

    jours = pd.Series(pd.date_range("2026-05-01", periods=28).strftime("%Y-%m-%d"))
    r = intervalle_gain(jours, np.full(28, 3.0), np.full(28, 2.0))
    assert r == pytest.approx({"moyenne": 1.0, "bas": 1.0, "haut": 1.0})


def test_intervalle_gain_encadre_la_moyenne_et_tire_des_semaines_entieres():
    from backend.model import intervalle_gain

    # Une seule semaine porte tout le gain : l'intervalle doit aller de 0 (semaine absente du tirage) à plus.
    jours = pd.Series(np.repeat(pd.date_range("2026-05-04", periods=28).strftime("%Y-%m-%d"), 5))
    reference = np.where(np.arange(140) < 35, 4.0, 1.0)
    r = intervalle_gain(jours, reference, np.ones(140), n_tirages=500)
    assert r["moyenne"] == pytest.approx(0.75)  # 35 lignes × 3 c€ / 140 lignes
    assert r["bas"] == pytest.approx(0.0) and r["bas"] <= r["moyenne"] <= r["haut"]
    assert r == intervalle_gain(jours, reference, np.ones(140), n_tirages=500)  # graine fixée
