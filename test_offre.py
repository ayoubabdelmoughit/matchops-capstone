from backend.agents.analyseur_offre import analyser_offre

offre = """
Nous recherchons un Developpeur Web Junior pour rejoindre notre equipe.
Competences requises : Python, JavaScript, developpement web, bases de donnees.
Experience : 1 a 2 ans minimum.
Niveau : junior.
"""

print(analyser_offre(offre))