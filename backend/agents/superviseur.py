import time
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from backend.agents.extracteur_cv import extraire_cv
from backend.agents.analyseur_offre import analyser_offre
from backend.agents.matcher import calculer_matching
from backend.agents.decideur import decider
from backend.agents.redacteur import rediger_message

import json


class MatchingState(TypedDict):
    chemin_cv: str
    texte_offre: str
    candidat_id: str
    offre_id: str
    candidat: Optional[dict]
    offre: Optional[dict]
    resultat_matching: Optional[dict]
    decision: Optional[dict]
    message_final: Optional[str]
    trace: Optional[list]


def _ajouter_trace(state: MatchingState, nom_agent: str, debut: float, statut: str):
    duree_ms = round((time.time() - debut) * 1000, 1)
    if state.get("trace") is None:
        state["trace"] = []
    state["trace"].append({
        "agent": nom_agent,
        "duree_ms": duree_ms,
        "statut": statut,
    })


def noeud_extracteur(state: MatchingState) -> MatchingState:
    debut = time.time()
    try:
        resultat = extraire_cv(state["chemin_cv"])
        candidat = json.loads(resultat["donnees_structurees"])
        state["candidat"] = candidat
        _ajouter_trace(state, "extracteur_cv", debut, "ok")
    except Exception:
        _ajouter_trace(state, "extracteur_cv", debut, "erreur")
        raise
    return state


def noeud_analyseur(state: MatchingState) -> MatchingState:
    debut = time.time()
    try:
        resultat = analyser_offre(state["texte_offre"])
        state["offre"] = json.loads(resultat)
        _ajouter_trace(state, "analyseur_offre", debut, "ok")
    except Exception:
        _ajouter_trace(state, "analyseur_offre", debut, "erreur")
        raise
    return state


def noeud_matcher(state: MatchingState) -> MatchingState:
    debut = time.time()
    try:
        resultat = calculer_matching(state["candidat"], state["offre"])
        state["resultat_matching"] = json.loads(resultat)
        _ajouter_trace(state, "matcher", debut, "ok")
    except Exception:
        _ajouter_trace(state, "matcher", debut, "erreur")
        raise
    return state


def noeud_decideur(state: MatchingState) -> MatchingState:
    debut = time.time()
    try:
        nom_candidat = (state.get("candidat") or {}).get("nom")
        decision = decider(state["candidat_id"], state["offre_id"], state["resultat_matching"], candidat_nom=nom_candidat)
        state["decision"] = decision
        _ajouter_trace(state, "decideur", debut, "ok")
    except Exception:
        _ajouter_trace(state, "decideur", debut, "erreur")
        raise
    return state


def noeud_redacteur(state: MatchingState) -> MatchingState:
    debut = time.time()
    try:
        state["message_final"] = rediger_message(state["decision"])
        _ajouter_trace(state, "redacteur", debut, "ok")
    except Exception:
        _ajouter_trace(state, "redacteur", debut, "erreur")
        raise
    return state


def construire_graph():
    graph = StateGraph(MatchingState)

    graph.add_node("extracteur", noeud_extracteur)
    graph.add_node("analyseur", noeud_analyseur)
    graph.add_node("matcher", noeud_matcher)
    graph.add_node("decideur", noeud_decideur)
    graph.add_node("redacteur", noeud_redacteur)

    graph.set_entry_point("extracteur")
    graph.add_edge("extracteur", "analyseur")
    graph.add_edge("analyseur", "matcher")
    graph.add_edge("matcher", "decideur")
    graph.add_edge("decideur", "redacteur")
    graph.add_edge("redacteur", END)

    return graph.compile()


pipeline_matching = construire_graph()