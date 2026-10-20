import numpy as np
import pytest

from backend import service
from backend.data import charger_brut_dans_sqlite, lire_table_analyse
from backend.model import VARIABLES, cout_moyen, seuil_optimal


@pytest.fixture
def table(tmp_path):
    base = tmp_path / "test.db"
    charger_brut_dans_sqlite(base=base)
    return lire_table_analyse(base=base)


def test_une_ligne_par_demande(table):
    assert len(table) == 1000
    assert table["client_id"].is_unique


def test_cible_binaire_et_taux_de_defaut_attendu(table):
    assert set(table["defaut"]) == {0, 1}
    assert table["defaut"].mean() == pytest.approx(0.30)


def test_variables_sensibles_exclues(table):
    assert {"statut_personnel_sexe", "travailleur_etranger"}.isdisjoint(table.columns)


def test_seuil_issu_de_la_matrice_de_couts():
    assert seuil_optimal() == pytest.approx(1 / 6)


def test_cout_moyen():
    y = np.array([1, 0, 1, 0])
    proba = np.array([0.9, 0.9, 0.0, 0.0])
    # défaut refusé : 0 ; bon refusé : 1 ; défaut accepté : 5 ; bon accepté : 0
    assert cout_moyen(y, proba, 0.5) == pytest.approx(6 / 4)


def test_scorer_refuse_une_variable_manquante(modele_entraine):
    with pytest.raises(ValueError, match="Variables manquantes"):
        service.scorer({"montant": 1000})


def test_scorer_renvoie_une_decision(modele_entraine):
    demande = service.lister_demandes()[VARIABLES].iloc[0].to_dict()
    resultat = service.scorer(demande)
    assert 0 <= resultat["proba_defaut"] <= 1
    assert resultat["decision"] in {"accorder", "refuser"}
