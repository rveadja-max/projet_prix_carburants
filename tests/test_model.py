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
