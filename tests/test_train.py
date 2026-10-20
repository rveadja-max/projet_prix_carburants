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
