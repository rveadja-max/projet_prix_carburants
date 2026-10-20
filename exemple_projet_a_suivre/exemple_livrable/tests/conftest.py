import pytest

from backend import train
from backend.config import FICHIER_MODELE


@pytest.fixture(scope="session")
def modele_entraine():
    if not FICHIER_MODELE.exists():
        train.main()
