import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b")


def calculer_matching(candidat: dict, offre: dict) -> dict:
    """Jour 17/20 : compare un candidat et une offre, renvoie un score + justification."""
    prompt = f"""Tu es un expert en recrutement. Compare ce candidat et cette offre d'emploi,
et renvoie UNIQUEMENT un JSON avec les champs :
score (nombre entre 0 et 100), competences_communes (liste), competences_manquantes (liste), justification (texte court).

CANDIDAT :
{json.dumps(candidat, ensure_ascii=False)}

OFFRE :
{json.dumps(offre, ensure_ascii=False)}
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