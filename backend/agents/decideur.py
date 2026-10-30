from backend.db import decisions_col, log_audit

SEUIL_AUTO_APPROUVE = 70
SEUIL_REJET_AUTO = 30


def decider(candidat_id: str, offre_id: str, resultat_matching: dict, candidat_nom: str = None, correlation_id: str = None) -> dict:
    """Jour 18 : applique un seuil de decision (bhal le scoring de risque pour les virements).
    score >= 70        -> approuve automatiquement
    30 <= score < 70    -> attente de validation humaine (HITL)
    score < 30          -> rejete automatiquement
    """
    score = resultat_matching.get("score", 0)

    if score >= SEUIL_AUTO_APPROUVE:
        statut = "approuve_auto"
    elif score < SEUIL_REJET_AUTO:
        statut = "rejete_auto"
    else:
        statut = "attente_humain"

    decision = {
        "candidat_id": candidat_id,
        "candidat_nom": candidat_nom,
        "offre_id": offre_id,
        "correlation_id": correlation_id,
        "score": score,
        "statut": statut,
        "resultat_matching": resultat_matching,
    }

    decisions_col.insert_one(decision)
    log_audit("decision_matching", decision)

    return decision