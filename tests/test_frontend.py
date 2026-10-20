from streamlit.testing.v1 import AppTest


def test_application_demarre_sans_erreur(modele_entraine):
    app = AppTest.from_file("../frontend/app.py", default_timeout=60).run()
    assert not app.exception
    assert len(app.tabs) == 3
