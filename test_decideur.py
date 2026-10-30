import json
from backend.agents.decideur import decider

resultat_matching = {
    "score": 38,
    "competences_communes": ["developpement web"],
    "competences_manquantes": ["Python", "JavaScript", "bases de donnees"],
    "justification": "Score moyen, experience suffisante mais competences techniques manquantes.",
}

decision = decider("candidat_test_1", "offre_test_1", resultat_matching)
print(json.dumps(decision, indent=2, ensure_ascii=False, default=str))