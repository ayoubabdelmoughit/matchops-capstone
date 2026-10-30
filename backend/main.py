import os
import shutil
import uuid
from typing import Optional
from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Cookie, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId

from backend.agents.superviseur import pipeline_matching
from backend.agents.redacteur import rediger_message
from backend.db import decisions_col, offres_col, dlq_col, log_audit, log_dlq
from backend.auth import (
    creer_compte, connecter, deconnecter, utilisateur_courant,
    creer_compte_candidat, connecter_candidat, deconnecter_candidat, utilisateur_candidat_courant,
)

app = FastAPI(title="Job Matching Capstone API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def recruteur_connecte(session_token: Optional[str] = Cookie(default=None)) -> str:
    email = utilisateur_courant(session_token) if session_token else None
    if not email:
        raise HTTPException(status_code=401, detail="Connexion requise.")
    return email


def candidat_connecte(candidat_session_token: Optional[str] = Cookie(default=None)) -> str:
    email = utilisateur_candidat_courant(candidat_session_token) if candidat_session_token else None
    if not email:
        raise HTTPException(status_code=401, detail="Connexion requise.")
    return email


def candidat_connecte_optionnel(candidat_session_token: Optional[str] = Cookie(default=None)) -> Optional[str]:
    return utilisateur_candidat_courant(candidat_session_token) if candidat_session_token else None


@app.get("/")
def racine():
    return {"status": "ok", "service": "job-matching-capstone"}


@app.post("/auth/recruteur/signup")
def signup_recruteur(email: str = Form(...), mot_de_passe: str = Form(...)):
    try:
        return creer_compte(email, mot_de_passe)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/recruteur/login")
def login_recruteur(response: Response, email: str = Form(...), mot_de_passe: str = Form(...)):
    try:
        token = connecter(email, mot_de_passe)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    response.set_cookie("session_token", token, httponly=True, samesite="lax", max_age=86400)
    return {"email": email}


@app.post("/auth/recruteur/logout")
def logout_recruteur(response: Response, session_token: Optional[str] = Cookie(default=None)):
    if session_token:
        deconnecter(session_token)
    response.delete_cookie("session_token")
    return {"status": "deconnecte"}


@app.get("/auth/recruteur/me")
def me_recruteur(session_token: Optional[str] = Cookie(default=None)):
    email = utilisateur_courant(session_token) if session_token else None
    if not email:
        raise HTTPException(status_code=401, detail="Non connecte.")
    return {"email": email}


@app.post("/auth/candidat/signup")
def signup_candidat(email: str = Form(...), mot_de_passe: str = Form(...)):
    try:
        return creer_compte_candidat(email, mot_de_passe)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/candidat/login")
def login_candidat(response: Response, email: str = Form(...), mot_de_passe: str = Form(...)):
    try:
        token = connecter_candidat(email, mot_de_passe)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    response.set_cookie("candidat_session_token", token, httponly=True, samesite="lax", max_age=86400)
    return {"email": email}


@app.post("/auth/candidat/logout")
def logout_candidat(response: Response, candidat_session_token: Optional[str] = Cookie(default=None)):
    if candidat_session_token:
        deconnecter_candidat(candidat_session_token)
    response.delete_cookie("candidat_session_token")
    return {"status": "deconnecte"}


@app.get("/auth/candidat/me")
def me_candidat(candidat_session_token: Optional[str] = Cookie(default=None)):
    email = utilisateur_candidat_courant(candidat_session_token) if candidat_session_token else None
    if not email:
        raise HTTPException(status_code=401, detail="Non connecte.")
    return {"email": email}


@app.post("/offres")
def creer_offre(titre: str = Form(...), description: str = Form(...), recruteur: str = Depends(recruteur_connecte)):
    offre = {
        "titre": titre,
        "description": description,
        "cree_par": recruteur,
        "cree_le": datetime.now(timezone.utc).isoformat(),
    }
    resultat = offres_col.insert_one(offre)
    offre["_id"] = str(resultat.inserted_id)
    return offre


@app.get("/offres")
def lister_offres():
    """Liste publique (candidat et recruteur) : titres/descriptions des offres ouvertes."""
    offres = list(offres_col.find().sort("_id", -1))
    for o in offres:
        o["_id"] = str(o["_id"])
    return offres


@app.delete("/offres/{offre_id}")
def supprimer_offre(offre_id: str, recruteur: str = Depends(recruteur_connecte)):
    resultat = offres_col.delete_one({"_id": ObjectId(offre_id)})
    if resultat.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Offre introuvable")
    return {"status": "supprimee"}


@app.post("/match")
async def lancer_matching(
    response: Response,
    cv: UploadFile = File(...),
    offre_id: str = Form(...),
    candidat_email: str = Depends(candidat_connecte),
):
    offre_doc = offres_col.find_one({"_id": ObjectId(offre_id)})
    if not offre_doc:
        raise HTTPException(status_code=404, detail="Offre introuvable")

    chemin_cv = os.path.join(UPLOAD_DIR, cv.filename)
    with open(chemin_cv, "wb") as f:
        shutil.copyfileobj(cv.file, f)

    horodatage = int(datetime.now(timezone.utc).timestamp())
    candidat_id = f"candidat_{horodatage}"

    # Jour 21 : un correlation_id unique est genere pour cette execution et
    # propage a travers tous les agents (voir backend/agents/superviseur.py),
    # pour pouvoir suivre une requete de bout en bout dans les logs/traces.
    correlation_id = str(uuid.uuid4())
    response.headers["X-Correlation-Id"] = correlation_id

    state_initial = {
        "chemin_cv": chemin_cv,
        "texte_offre": offre_doc["description"],
        "candidat_id": candidat_id,
        "offre_id": offre_id,
        "correlation_id": correlation_id,
    }

    try:
        resultat = pipeline_matching.invoke(state_initial)
    except Exception as e:
        log_dlq("erreur_pipeline", {"erreur": str(e), "candidat_id": candidat_id, "correlation_id": correlation_id})
        raise HTTPException(status_code=500, detail=f"Erreur pipeline: {e}")

    decision = resultat.get("decision")
    trace = resultat.get("trace")

    if decision and "_id" in decision:
        maj = {
            "trace": trace,
            "candidat_email": candidat_email,
            "offre_titre": offre_doc["titre"],
            "message_final": resultat.get("message_final"),
            "correlation_id": correlation_id,
        }
        decision["candidat_email"] = candidat_email
        decisions_col.update_one({"_id": decision["_id"]}, {"$set": maj})
        decision["_id"] = str(decision["_id"])

    return {
        "candidat": resultat.get("candidat"),
        "offre": resultat.get("offre"),
        "decision": decision,
        "message_final": resultat.get("message_final"),
        "correlation_id": correlation_id,
    }


@app.get("/decisions")
def lister_decisions(statut: Optional[str] = None, recruteur: str = Depends(recruteur_connecte)):
    filtre = {"statut": statut} if statut else {}
    decisions = list(decisions_col.find(filtre).sort("_id", -1).limit(100))
    for d in decisions:
        d["_id"] = str(d["_id"])
    return decisions


@app.post("/decisions/{decision_id}/valider")
def valider_decision(decision_id: str, recruteur: str = Depends(recruteur_connecte)):
    decision = decisions_col.find_one({"_id": ObjectId(decision_id)})
    if not decision:
        raise HTTPException(status_code=404, detail="Decision introuvable")
    decision["statut"] = "approuve_humain"
    nouveau_message = rediger_message(decision)
    decisions_col.update_one(
        {"_id": ObjectId(decision_id)},
        {"$set": {"statut": "approuve_humain", "message_final": nouveau_message}},
    )
    log_audit("validation_humaine", {"decision_id": decision_id, "action": "approuve", "par": recruteur})
    return {"status": "approuve"}


@app.post("/decisions/{decision_id}/rejeter")
def rejeter_decision(decision_id: str, recruteur: str = Depends(recruteur_connecte)):
    decision = decisions_col.find_one({"_id": ObjectId(decision_id)})
    if not decision:
        raise HTTPException(status_code=404, detail="Decision introuvable")
    decision["statut"] = "rejete_humain"
    nouveau_message = rediger_message(decision)
    decisions_col.update_one(
        {"_id": ObjectId(decision_id)},
        {"$set": {"statut": "rejete_humain", "message_final": nouveau_message}},
    )
    log_audit("validation_humaine", {"decision_id": decision_id, "action": "rejete", "par": recruteur})
    return {"status": "rejete"}


@app.get("/suivi/{decision_id}")
def suivre_candidature(decision_id: str):
    """Public (sans auth) : permet au candidat de suivre sa candidature avec
    le numero de suivi recu juste apres son depot."""
    try:
        decision = decisions_col.find_one({"_id": ObjectId(decision_id)})
    except Exception:
        decision = None
    if not decision:
        raise HTTPException(status_code=404, detail="Numero de suivi introuvable")
    return {
        "statut": decision.get("statut"),
        "score": decision.get("score"),
        "message_final": decision.get("message_final"),
    }


@app.get("/candidat/mes-candidatures")
def mes_candidatures(candidat_email: str = Depends(candidat_connecte)):
    decisions = list(
        decisions_col.find({"candidat_email": candidat_email}).sort("_id", -1).limit(50)
    )
    for d in decisions:
        d["_id"] = str(d["_id"])
    return decisions


@app.get("/supervision/erreurs")
def lister_erreurs(recruteur: str = Depends(recruteur_connecte)):
    """Jour 21/22 : expose la Dead Letter Queue (erreurs d'agent + erreurs
    pipeline) pour un affichage temps reel dans l'onglet Superviseur."""
    erreurs = list(dlq_col.find().sort("_id", -1).limit(50))
    for e in erreurs:
        e["_id"] = str(e["_id"])
    return erreurs


@app.get("/metrics")
def obtenir_metriques(recruteur: str = Depends(recruteur_connecte)):
    return {
        "total": decisions_col.count_documents({}),
        "approuve_auto": decisions_col.count_documents({"statut": "approuve_auto"}),
        "rejete_auto": decisions_col.count_documents({"statut": "rejete_auto"}),
        "attente_humain": decisions_col.count_documents({"statut": "attente_humain"}),
    }


@app.get("/supervision/traces")
def lister_traces(recruteur: str = Depends(recruteur_connecte)):
    decisions = list(
        decisions_col.find(
            {},
            {"candidat_id": 1, "candidat_nom": 1, "offre_id": 1, "offre_titre": 1, "score": 1, "statut": 1, "trace": 1, "correlation_id": 1},
        )
        .sort("_id", -1)
        .limit(50)
    )
    for d in decisions:
        d["_id"] = str(d["_id"])
    return decisions