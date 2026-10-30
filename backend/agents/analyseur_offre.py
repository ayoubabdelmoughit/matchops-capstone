import os
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b")


def analyser_offre(texte_offre: str) -> dict:
    """Jour 17/20 : extrait d'une offre d'emploi les champs structures necessaires au matching."""
    prompt = f"""Tu es un analyseur d'offres d'emploi. A partir du texte suivant, extrais UNIQUEMENT un JSON avec les champs :
titre_poste, competences_requises (liste), annees_experience_requises (nombre), niveau (junior/confirme/senior).
Reponds uniquement avec le JSON, rien d'autre.

Texte de l'offre :
{texte_offre}
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