import hashlib
import hmac
import secrets

from backend.db import db

recruteurs_col = db["recruteurs"]
candidats_comptes_col = db["candidats_comptes"]

# Sessions en memoire, separees par role : token -> email (simple pour ce
# capstone ; une vraie prod stockerait ca dans Mongo/Redis avec expiration)
sessions = {}            # recruteurs (nom garde pour compatibilite)
sessions_candidats = {}  # candidats


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    sel = secrets.token_hex(16)
    empreinte = hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode(), sel.encode(), 100_000)
    return f"{sel}${empreinte.hex()}"


def verifier_mot_de_passe(mot_de_passe: str, hash_stocke: str) -> bool:
    sel, empreinte_attendue = hash_stocke.split("$")
    empreinte = hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode(), sel.encode(), 100_000)
    return hmac.compare_digest(empreinte.hex(), empreinte_attendue)


def _creer_compte(collection, email: str, mot_de_passe: str) -> dict:
    if collection.find_one({"email": email}):
        raise ValueError("Un compte existe deja avec cet email.")
    compte = {"email": email, "mot_de_passe_hash": hacher_mot_de_passe(mot_de_passe)}
    collection.insert_one(compte)
    return {"email": email}


def _connecter(collection, sessions_dict: dict, email: str, mot_de_passe: str) -> str:
    compte = collection.find_one({"email": email})
    if not compte or not verifier_mot_de_passe(mot_de_passe, compte["mot_de_passe_hash"]):
        raise ValueError("Email ou mot de passe incorrect.")
    token = secrets.token_hex(32)
    sessions_dict[token] = email
    return token


# ---- Recruteurs (noms d'origine conserves : main.py les importe tels quels) ----

def creer_compte(email: str, mot_de_passe: str) -> dict:
    return _creer_compte(recruteurs_col, email, mot_de_passe)


def connecter(email: str, mot_de_passe: str) -> str:
    return _connecter(recruteurs_col, sessions, email, mot_de_passe)


def deconnecter(token: str):
    sessions.pop(token, None)


def utilisateur_courant(token: str):
    return sessions.get(token)


# ---- Candidats ----

def creer_compte_candidat(email: str, mot_de_passe: str) -> dict:
    return _creer_compte(candidats_comptes_col, email, mot_de_passe)


def connecter_candidat(email: str, mot_de_passe: str) -> str:
    return _connecter(candidats_comptes_col, sessions_candidats, email, mot_de_passe)


def deconnecter_candidat(token: str):
    sessions_candidats.pop(token, None)


def utilisateur_candidat_courant(token: str):
    return sessions_candidats.get(token)
