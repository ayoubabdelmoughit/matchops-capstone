import json
from backend.agents.superviseur import pipeline_matching

offre = """
Nous recherchons un Developpeur Web Junior pour rejoindre notre equipe.
Competences requises : Python, JavaScript, developpement web, bases de donnees.
Experience : 1 a 2 ans minimum.
Niveau : junior.
"""

state_initial = {
    "chemin_cv": "test_cv.pdf",
    "texte_offre": offre,
    "candidat_id": "candidat_001",
    "offre_id": "offre_001",
}

resultat = pipeline_matching.invoke(state_initial)

print("=== CANDIDAT ===")
print(json.dumps(resultat["candidat"], indent=2, ensure_ascii=False))
print("\n=== DECISION ===")
print(json.dumps(resultat["decision"], indent=2, ensure_ascii=False, default=str))
print("\n=== MESSAGE FINAL ===")
print(resultat["message_final"])
print("\n=== TRACE ===")
print(json.dumps(resultat["trace"], indent=2, ensure_ascii=False))