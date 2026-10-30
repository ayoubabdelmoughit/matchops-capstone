"""
Tests automatises (Jour 22) du module d'authentification (backend/auth.py).

backend/auth.py persiste les comptes dans MongoDB (recruteurs_col). Pour que
ces tests tournent sans secret / sans connexion reseau dans la CI GitHub
Actions, la collection Mongo est mockee par une fausse collection en memoire
(meme principe que tests/test_decideur.py pour decisions_col).
"""
import pytest
from unittest.mock import patch

from backend.auth import creer_compte, connecter, deconnecter, utilisateur_courant


class FausseCollection:
    """Imite .find_one()/.insert_one() de pymongo avec un dict en memoire."""

    def __init__(self):
        self._comptes = {}

    def find_one(self, filtre):
        return self._comptes.get(filtre["email"])

    def insert_one(self, document):
        self._comptes[document["email"]] = document


def _email_unique():
    import uuid
    return f"test_{uuid.uuid4().hex[:8]}@matchops.com"


@pytest.fixture(autouse=True)
def _mock_recruteurs_col():
    with patch("backend.auth.recruteurs_col", FausseCollection()):
        yield


def test_creer_compte_puis_connecter():
    email = _email_unique()
    creer_compte(email, "motdepasse123")
    token = connecter(email, "motdepasse123")
    assert token is not None
    assert utilisateur_courant(token) == email


def test_connecter_mauvais_mot_de_passe_leve_erreur():
    email = _email_unique()
    creer_compte(email, "motdepasse123")
    with pytest.raises(ValueError):
        connecter(email, "mauvais_mot_de_passe")


def test_creer_compte_email_deja_utilise_leve_erreur():
    email = _email_unique()
    creer_compte(email, "motdepasse123")
    with pytest.raises(ValueError):
        creer_compte(email, "autremotdepasse")


def test_deconnecter_invalide_le_token():
    email = _email_unique()
    creer_compte(email, "motdepasse123")
    token = connecter(email, "motdepasse123")
    deconnecter(token)
    assert utilisateur_courant(token) is None


def test_utilisateur_courant_token_inconnu_retourne_none():
    assert utilisateur_courant("token_qui_n_existe_pas") is None
