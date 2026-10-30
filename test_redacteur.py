from backend.agents.redacteur import rediger_message

decision = {
    "candidat_id": "candidat_test_1",
    "offre_id": "offre_test_1",
    "score": 38,
    "statut": "attente_humain",
}

print(rediger_message(decision))