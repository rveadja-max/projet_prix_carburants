from streamlit.testing.v1 import AppTest


def test_application_demarre_sans_erreur(modele_entraine):
    app = AppTest.from_file("../frontend/app.py", default_timeout=60).run()
    assert not app.exception
    assert len(app.tabs) == 3


def test_onglet_conseil_affiche_les_stations_alternatives(modele_entraine):
    app = AppTest.from_file("../frontend/app.py", default_timeout=60).run()
    assert any("moins chères à proximité" in titre.value for titre in app.subheader)
