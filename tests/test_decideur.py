"""
Tests automatises (Jour 22) de l'agent Decideur (backend/agents/decideur.py).

Categories couvertes :
  - format      : la decision retournee contient bien toutes les cles attendues
  - policy      : les seuils de decision (70 / 30) sont respectes exactement
  - robustesse  : entrees invalides / limites (score manquant, valeurs au bord)

MongoDB (decisions_col) et l'audit trail (log_audit) sont mockes : ces tests
ne touchent jamais la vraie base Atlas et tournent donc sans secret dans la
CI GitHub Actions.
"""
from unittest.mock import patch, MagicMock

from backend.agents.decideur import decider, SEUIL_AUTO_APPROUVE, SEUIL_REJET_AUTO


def _decider_mocke(candidat_id, offre_id, resultat_matching):
    with patch("backend.agents.decideur.decisions_col") as mock_col, \
         patch("backend.agents.decideur.log_audit") as mock_audit:
        mock_col.insert_one = MagicMock()
        decision = decider(candidat_id, offre_id, resultat_matching)
        assert mock_col.insert_one.called, "la decision doit etre persistee"
        assert mock_audit.called, "chaque decision doit etre loggee dans l'audit trail"
    return decision


# ---------- format ----------

def test_format_decision_contient_toutes_les_cles():
    decision = _decider_mocke("c1", "o1", {"score": 55})
    for cle in ("candidat_id", "offre_id", "score", "statut", "resultat_matching"):
        assert cle in decision


def test_format_statut_est_toujours_une_des_3_valeurs():
    valeurs_valides = {"approuve_auto", "rejete_auto", "attente_humain"}
    for score in (0, 29, 30, 69, 70, 100):
        decision = _decider_mocke("c1", "o1", {"score": score})
        assert decision["statut"] in valeurs_valides


# ---------- policy (seuils) ----------

def test_policy_score_eleve_approuve_auto():
    decision = _decider_mocke("c1", "o1", {"score": 85})
    assert decision["statut"] == "approuve_auto"


def test_policy_score_bas_rejete_auto():
    decision = _decider_mocke("c1", "o1", {"score": 10})
    assert decision["statut"] == "rejete_auto"


def test_policy_score_moyen_attente_humain():
    decision = _decider_mocke("c1", "o1", {"score": 50})
    assert decision["statut"] == "attente_humain"


def test_policy_borne_exacte_seuil_approuve():
    # score == 70 -> doit basculer en approuve_auto (>=)
    decision = _decider_mocke("c1", "o1", {"score": SEUIL_AUTO_APPROUVE})
    assert decision["statut"] == "approuve_auto"


def test_policy_borne_juste_sous_seuil_approuve():
    # score == 69 -> doit rester en attente_humain
    decision = _decider_mocke("c1", "o1", {"score": SEUIL_AUTO_APPROUVE - 1})
    assert decision["statut"] == "attente_humain"


def test_policy_borne_exacte_seuil_rejet():
    # score == 30 -> doit rester en attente_humain (seul score < 30 est rejete)
    decision = _decider_mocke("c1", "o1", {"score": SEUIL_REJET_AUTO})
    assert decision["statut"] == "attente_humain"


def test_policy_borne_juste_sous_seuil_rejet():
    # score == 29 -> doit basculer en rejete_auto
    decision = _decider_mocke("c1", "o1", {"score": SEUIL_REJET_AUTO - 1})
    assert decision["statut"] == "rejete_auto"


# ---------- robustesse ----------

def test_robustesse_score_manquant_traite_comme_zero():
    # resultat_matching sans cle "score" -> ne doit jamais planter
    decision = _decider_mocke("c1", "o1", {})
    assert decision["score"] == 0
    assert decision["statut"] == "rejete_auto"


def test_robustesse_resultat_matching_vide_ne_leve_pas_exception():
    try:
        _decider_mocke("c1", "o1", {})
    except Exception as e:
        assert False, f"decider() ne doit jamais lever d'exception, a leve : {e}"
