from streamlit.testing.v1 import AppTest


def test_application_demarre_sans_erreur(modele_entraine):
    app = AppTest.from_file("../frontend/app.py", default_timeout=60).run()
    assert not app.exception
    assert [onglet.label for onglet in app.tabs] == ["Décision", "Exploration", "Le modèle"]


def test_onglet_decision_affiche_conseil_du_jour_et_stations_proches(modele_entraine):
    app = AppTest.from_file("../frontend/app.py", default_timeout=60).run()
    assert any("moins chères aujourd'hui" in titre.value for titre in app.subheader)
    assert any(titre.value.startswith("Conseil du ") for titre in app.subheader)


def test_onglet_modele_montre_economie_et_apport_du_taux_bce(modele_entraine):
    app = AppTest.from_file("../frontend/app.py", default_timeout=60).run()
    libelles = [metrique.label for metrique in app.metric]
    assert any("Économie annuelle" in libelle for libelle in libelles)
    assert any("taux BCE" in libelle for libelle in libelles)


def test_onglet_exploration_croise_les_deux_sources(modele_entraine):
    app = AppTest.from_file("../frontend/app.py", default_timeout=60).run()
    assert any("Croisement des deux sources" in titre.value for titre in app.subheader)


def test_onglet_modele_montre_le_regret_par_mois(modele_entraine):
    app = AppTest.from_file("../frontend/app.py", default_timeout=60).run()
    assert any("par mois" in titre.value for titre in app.subheader)
