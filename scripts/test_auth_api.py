import requests

API = "http://localhost:8020"

# Signup
r = requests.post(f"{API}/auth/recruteur/signup", data={
    "email": "recruteur@matchops.com",
    "mot_de_passe": "test1234"
})
print("SIGNUP:", r.status_code, r.json())

# Login (avec session pour garder le cookie)
session = requests.Session()
r = session.post(f"{API}/auth/recruteur/login", data={
    "email": "recruteur@matchops.com",
    "mot_de_passe": "test1234"
})
print("LOGIN:", r.status_code, r.json())

# Appel protege (avec le cookie de la session)
r = session.get(f"{API}/metrics")
print("METRICS (connecte):", r.status_code, r.json())

# Appel protege SANS cookie (nouvelle session vide)
r2 = requests.get(f"{API}/metrics")
print("METRICS (pas connecte):", r2.status_code)