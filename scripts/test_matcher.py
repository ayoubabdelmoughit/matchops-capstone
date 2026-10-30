from backend.agents.matcher import calculer_matching

candidat = {
    "nom": "Ayoub Abdelmoughit",
    "email": "ayoubabdemoughit75@gmail.com",
    "competences": ["Programmation", "Developpement web", "Developpement logiciel",
                     "Developpement d'applications", "Resolution de problemes", "Collaboration"],
    "annees_experience": 2,
    "formations": ["Licence Professionnelle Ingenierie Logiciel web et Mobile"],
}

offre = {
    "titre_poste": "Developpeur Web Junior",
    "competences_requises": ["Python", "JavaScript", "developpement web", "bases de donnees"],
    "annees_experience_requises": 1,
    "niveau": "junior",
}

print(calculer_matching(candidat, offre))