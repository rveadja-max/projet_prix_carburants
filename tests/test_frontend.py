from streamlit.testing.v1 import AppTest


def test_application_demarre_sans_erreur(modele_entraine):
    app = AppTest.from_file("../frontend/app.py", default_timeout=60).run()
    assert not app.exception
    assert len(app.tabs) == 3


def test_onglet_conseil_affiche_les_stations_alternatives(modele_entraine):
    app = AppTest.from_file("../frontend/app.py", default_timeout=60).run()
    assert any("moins chères à proximité" in titre.value for titre in app.subheader)


def test_onglet_modele_met_le_modele_sans_brent_en_titre(modele_entraine):
    app = AppTest.from_file("../frontend/app.py", default_timeout=60).run()
    libelles = [metrique.label for metrique in app.metric]
    assert any("sans Brent" in libelle for libelle in libelles)
    assert any("Brent de la veille" in libelle for libelle in libelles)


def test_onglet_modele_montre_le_regret_par_mois(modele_entraine):
    app = AppTest.from_file("../frontend/app.py", default_timeout=60).run()
    assert any("par mois" in titre.value for titre in app.subheader)
