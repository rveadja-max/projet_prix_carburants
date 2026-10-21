"""Tests de l'entraînement : cohérence de metriques.json."""
import json

import pytest

from backend.config import FICHIER_METRIQUES

CLES_MODELE = {
    "roc_auc", "roc_auc_cv_moyenne", "roc_auc_cv_ecart_type", "cout_moyen_modele",
    "cout_moyen_seuil_05", "importance_permutation", "part_plein_modele",
}


def test_metriques_coherentes(modele_entraine):
    m = json.loads(FICHIER_METRIQUES.read_text(encoding="utf-8"))
    assert set(m["modeles"]) == {"sans_brent", "avec_brent", "brent_realiste"}
    assert m["debut_test"] > "2026-05-03"
    assert m["seuil"] == pytest.approx(m["baisse_moyenne_c"] / (m["hausse_moyenne_c"] + m["baisse_moyenne_c"]))
    assert m["couts"]["oracle"] == 0.0
    for modele in m["modeles"].values():
        assert CLES_MODELE <= set(modele)
        # Une AUC faible est une limite à documenter, jamais un échec masqué : on vérifie seulement la validité.
        assert 0 <= modele["roc_auc"] <= 1
        assert 0 <= modele["part_plein_modele"] <= 1
    economie = (m["couts"]["toujours_plein"] - m["modeles"]["avec_brent"]["cout_moyen_modele"]) / 100 * m["litres_par_an"]
    assert m["economie_annuelle_euros"] == pytest.approx(economie)


def test_metriques_choix_station(modele_entraine):
    m = json.loads(FICHIER_METRIQUES.read_text(encoding="utf-8"))
    c = m["choix_station"]
    assert 1.2 <= c["prix_litre"] <= 3.0 and c["rayon_km"] > 0
    for scenario in ("avec_detour", "sur_tournee"):
        s = c[scenario]
        assert {"nb_stations", "part_avec_alternative", "gain_moyen_c_l", "gain_moyen_plein_euros",
                "economie_annuelle_euros"} <= set(s)
        assert 0 <= s["part_avec_alternative"] <= 1
        assert s["economie_annuelle_euros"] == pytest.approx(s["gain_moyen_plein_euros"] * m["pleins_par_an"])
    # Payer le détour ne peut que réduire le nombre de stations où l'on change.
    assert c["avec_detour"]["part_avec_alternative"] <= c["sur_tournee"]["part_avec_alternative"]


def test_gain_vs_situation_actuelle_et_valeur_du_brent(modele_entraine):
    m = json.loads(FICHIER_METRIQUES.read_text(encoding="utf-8"))
    for nom, modele in m["modeles"].items():
        g = modele["gain_vs_plein"]
        assert g["bas"] <= g["moyenne"] <= g["haut"]
        assert g["moyenne"] == pytest.approx(m["couts"]["toujours_plein"] - modele["cout_moyen_modele"])
        assert g["economie_annuelle_euros"] == pytest.approx(g["moyenne"] / 100 * m["litres_par_an"])
    v = m["valeur_brent_veille"]
    attendu = m["modeles"]["sans_brent"]["cout_moyen_modele"] - m["modeles"]["avec_brent"]["cout_moyen_modele"]
    assert v["moyenne"] == pytest.approx(attendu) and v["bas"] <= v["moyenne"] <= v["haut"]
    assert v["economie_annuelle_euros"] == pytest.approx(attendu / 100 * m["litres_par_an"])
