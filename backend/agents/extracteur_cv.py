import pdfplumber
import requests
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b")


def extraire_texte_pdf(chemin_pdf: str) -> str:
    """Essaie de lire le texte directement depuis le PDF (rapide, gratuit)."""
    texte = ""
    with pdfplumber.open(chemin_pdf) as pdf:
        for page in pdf.pages:
            contenu = page.extract_text()
            if contenu:
                texte += contenu + "\n"
    return texte.strip()


def structurer_cv(texte_brut: str) -> dict:
    """Jour 17/20 : un agent (Ollama) transforme le texte brut en JSON structure."""
    prompt = f"""Tu es un extracteur de CV. A partir du texte suivant, extrais UNIQUEMENT un JSON avec les champs :
nom, email, competences (liste), annees_experience (nombre), formations (liste).
Reponds uniquement avec le JSON, rien d'autre.

Texte du CV :
{texte_brut}
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


def extraire_cv(chemin_pdf: str) -> dict:
    """Pipeline complet : PDF -> texte -> JSON structure.
    Jour 19 : si le texte extrait est vide/trop court, le PDF est probablement
    une image scannee -> il faudrait basculer vers VOCR (a ajouter plus tard)."""
    texte = extraire_texte_pdf(chemin_pdf)

    if len(texte) < 30:
        return {
            "erreur": "PDF semble etre une image scannee (texte insuffisant). "
                      "VOCR necessaire ici (jour 19)."
        }

    return {
        "texte_brut": texte,
        "donnees_structurees": structurer_cv(texte),
    }