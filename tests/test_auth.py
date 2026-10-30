"""
Tests automatises (Jour 22) du module d'authentification (backend/auth.py).

Ces tests ne font aucun appel reseau/API externe (pas d'Ollama, pas de
MongoDB) : les comptes recruteur sont geres en memoire dans backend/auth.py,
donc ces tests tournent sans secret dans la CI GitHub Actions.
"""
import pytest

from backend.auth import creer_compte, connecter, deconnecter, utilisateur_courant


def _email_unique():
    import uuid
    return f"test_{uuid.uuid4().hex[:8]}@matchops.com"


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
