"""Tests rapides des branches d'affichage, sans Streamlit ni modèle entraîné.

Exécute le bloc Décision réel avec une interface simulée. Ces tests ne remplacent
pas les tests d'intégration Streamlit de test_frontend.py.
"""
import ast
from pathlib import Path
import unittest
from unittest.mock import MagicMock

import pandas as pd


APP = Path(__file__).resolve().parents[1] / 'frontend' / 'app.py'


def afficher(fermee=False, rupture=False, frais=True, alternatives=False, erreur=False):
    arbre = ast.parse(APP.read_text(encoding='utf-8'))
    bloc = next(n for n in arbre.body if isinstance(n, ast.With)
                and isinstance(n.items[0].context_expr, ast.Name)
                and n.items[0].context_expr.id == 'onglet_decision')
    # Le rejeu historique est indépendant du conseil actuel.
    corps = []
    for instruction in bloc.body:
        if isinstance(instruction, ast.With):
            break
        corps.append(instruction)
    code = compile(ast.Module(body=corps, type_ignores=[]), str(APP), 'exec')
    st, service = MagicMock(), MagicMock()
    st.selectbox.return_value = 'A'
    st.columns.return_value = [MagicMock() for _ in range(3)]
    service.DECISION_PLEIN = 'faire le plein'
    service.etat_station.return_value = {
        'jour_conseil': '2026-10-21', 'fermee': fermee, 'rupture': rupture,
        'prix_frais': frais, 'prix_jour': 1.6, 'maj_prix_jour': '2026-10-20T08:00:00',
        'automate_24_24': True,
    }
    service.conseil_du_jour.return_value = {
        'proba_hausse': .8, 'prix': 1.6, 'taux': 1.1, 'decision': 'faire le plein',
        'seuil': .26, 'modele': 'prix seuls',
    }
    if erreur:
        service.conseil_du_jour.side_effect = ValueError('Historique incomplet')
    service.alternatives.return_value = pd.DataFrame([{
        'station': 'B', 'ville': 'Lille', 'adresse': 'Rue B', 'prix_jour': 1.5,
        'distance_km': 1., 'gain_c_l': 10., 'gain_plein_euros': 2.,
    }]) if alternatives else pd.DataFrame()
    exec(code, {'st': st, 'service': service,
                'metriques': {'choix_station': {'rayon_km': 5}},
                'table_stations': pd.DataFrame([{'station': 'A', 'ville': 'Lille', 'adresse': 'Rue A'}])})
    return st, service


class TestDecisionAffichage(unittest.TestCase):
    def test_station_disponible_garde_son_conseil(self):
        st, service = afficher()
        service.conseil_du_jour.assert_called_once_with('A')
        st.success.assert_called_once()

    def test_fermeture_rupture_et_cumul_bloquent_le_conseil(self):
        for fermee, rupture in [(True, False), (False, True), (True, True)]:
            with self.subTest(fermee=fermee, rupture=rupture):
                st, service = afficher(fermee=fermee, rupture=rupture)
                service.conseil_du_jour.assert_not_called()
                st.success.assert_not_called()
                self.assertTrue(any('même si elle est plus chère' in c.args[0]
                                    for c in st.warning.call_args_list))

    def test_indisponibilite_conserve_les_alternatives(self):
        st, service = afficher(fermee=True, alternatives=True)
        st.dataframe.assert_called_once()
        service.conseil_du_jour.assert_not_called()

    def test_prix_perime_explique_absence_de_comparaison(self):
        st, _ = afficher(frais=False)
        self.assertTrue(any('Comparaison indisponible' in c.args[0] for c in st.info.call_args_list))

    def test_absence_alternative_ne_conseille_pas_de_rester(self):
        st, _ = afficher()
        textes = [c.args[0] for c in st.info.call_args_list]
        self.assertTrue(any('Aucune alternative rentable' in t for t in textes))
        self.assertFalse(any('rester à cette station' in t for t in textes))

    def test_date_et_limite_temps_reel_visibles(self):
        st, _ = afficher()
        self.assertTrue(any('2026-10-21' in c.args[0] and 'temps réel' in c.args[0]
                            for c in st.info.call_args_list))

    def test_historique_incomplet_affiche_un_avertissement(self):
        st, _ = afficher(erreur=True)
        st.warning.assert_any_call('Historique incomplet')
        st.success.assert_not_called()


if __name__ == '__main__':
    unittest.main()
