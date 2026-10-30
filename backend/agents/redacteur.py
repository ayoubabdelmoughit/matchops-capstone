import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b")


def rediger_message(decision: dict) -> str:
    """Jour 17/20 : redige un message adapte au statut de la decision."""
    statut = decision.get("statut")

    if statut == "approuve_auto":
        instruction = "Felicite le candidat et invite-le a une prochaine etape (entretien)."
    elif statut == "rejete_auto":
        instruction = "Remercie le candidat poliment, explique brievement le manque d'adequation, sans decourager."
    else:
        instruction = "Informe le candidat que sa candidature est en cours d'examen par un recruteur humain."

    nom_candidat = decision.get("candidat_nom")
    consigne_nom = (
        f"Adresse-toi au candidat par son prenom/nom reel : {nom_candidat}. N'utilise JAMAIS de placeholder entre crochets comme [Nom du candidat]."
        if nom_candidat
        else "Le nom du candidat est inconnu : commence le message par 'Bonjour,' sans placeholder entre crochets."
    )

    prompt = f"""Tu es un redacteur RH. Redige un court message (3-4 phrases) en francais pour un candidat,
selon cette instruction : {instruction}

{consigne_nom}

Contexte de la decision :
{json.dumps(decision, ensure_ascii=False, default=str)}
"""
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        headers={"Authorization": f"Bearer {OLLAMA_API_KEY}"},
        json={
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]