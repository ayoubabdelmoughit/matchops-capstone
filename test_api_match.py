import requests

with open("test_cv.pdf", "rb") as f:
    files = {"cv": ("test_cv.pdf", f, "application/pdf")}
    data = {
        "offre_texte": """
        Nous recherchons un Developpeur Web Junior pour rejoindre notre equipe.
        Competences requises : Python, JavaScript, developpement web, bases de donnees.
        Experience : 1 a 2 ans minimum.
        Niveau : junior.
        """
    }
    r = requests.post("http://localhost:8020/match", files=files, data=data)

print(r.status_code)
print(r.json())