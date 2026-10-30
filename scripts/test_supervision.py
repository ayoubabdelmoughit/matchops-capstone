import json
import requests

BASE = "http://127.0.0.1:8000"
s = requests.Session()

email = "test_supervision@example.com"
mot_de_passe = "test1234"

r = s.post(f"{BASE}/auth/recruteur/login", data={"email": email, "mot_de_passe": mot_de_passe})
if r.status_code != 200:
    s.post(f"{BASE}/auth/recruteur/signup", data={"email": email, "mot_de_passe": mot_de_passe})
    r = s.post(f"{BASE}/auth/recruteur/login", data={"email": email, "mot_de_passe": mot_de_passe})

print("LOGIN:", r.status_code, r.json())

offre = """
Nous recherchons un Developpeur Web Junior pour rejoindre notre equipe.
Competences requises : Python, JavaScript, developpement web, bases de donnees.
Experience : 1 a 2 ans minimum.
Niveau : junior.
"""

with open("test_cv.pdf", "rb") as f:
    r = s.post(f"{BASE}/match", files={"cv": f}, data={"offre_texte": offre})
print("MATCH:", r.status_code)

r = s.get(f"{BASE}/supervision/traces")
print("TRACES:")
print(json.dumps(r.json(), indent=2, ensure_ascii=False))