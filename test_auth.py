from backend.auth import creer_compte, connecter, utilisateur_courant, deconnecter

# Creation de compte
compte = creer_compte("recruteur@test.com", "motdepasse123")
print("Compte cree:", compte)

# Connexion
token = connecter("recruteur@test.com", "motdepasse123")
print("Token recu:", token[:16] + "...")

# Verification
email = utilisateur_courant(token)
print("Utilisateur courant:", email)

# Deconnexion
deconnecter(token)
print("Apres deconnexion:", utilisateur_courant(token))

# Test mauvais mot de passe
try:
    connecter("recruteur@test.com", "mauvais")
except ValueError as e:
    print("Erreur attendue:", e)