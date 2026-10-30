# Agent Card — MatchOps

## Identité

| Champ | Valeur |
|---|---|
| Nom | MatchOps — Agent de Matching Candidat ↔ Offre d'Emploi |
| Version | v1.1.0 |
| Responsable | Ayoub Abdelmoughit (propriétaire & technique) |
| Domaine | Marché du travail / Recrutement |
| Dépôt | github.com/ayoubabdelmoughit/matchops-capstone |

## Que fait l'agent ?

Un recruteur authentifié publie des offres d'emploi (titre + description)
dans l'espace recruteur. Un candidat authentifié choisit une offre dans la
liste et dépose son CV (PDF). MatchOps lit le CV, calcule un score de
compatibilité de 0 à 100 avec l'offre choisie, puis décide automatiquement
(approuvé / rejeté) ou transmet le dossier à un recruteur humain pour
arbitrage si le score est ambigu. Un message personnalisé (nom réel du
candidat, extrait du CV) est ensuite rédigé et affiché au candidat dans
son espace « Mes candidatures ».

## Architecture (pipeline LangGraph à 5 agents)

```
Extracteur CV → Analyseur Offre → Matcher → Décideur → Rédacteur
```

| Agent | Rôle | Modèle / outil |
|---|---|---|
| Extracteur CV | Lit le PDF, structure le profil (compétences, expérience, formations) | pdfplumber + Ollama gpt-oss:120b |
| Analyseur Offre | Extrait les compétences et le niveau requis de l'offre | Ollama gpt-oss:120b |
| Matcher | Compare candidat ↔ offre, calcule le score et la justification | Ollama gpt-oss:120b |
| Décideur | Applique le seuil de décision (logique pure, sans IA) | Python (règles fixes) |
| Rédacteur | Rédige le message final pour le candidat | Ollama gpt-oss:120b |

## Règle de décision (Human-in-the-Loop)

| Score | Décision |
|---|---|
| ≥ 70 | Approuvé automatiquement |
| 30 – 69 | Transmis à un recruteur humain (revue requise) |
| < 30 | Rejeté automatiquement |

## Gouvernance des accès (authentification)

| Rôle | Accès | Mécanisme |
|---|---|---|
| Recruteur | Crée/liste/supprime les offres, arbitre les dossiers en zone grise, consulte KPIs/Historique/Superviseur | Compte email+mot de passe, cookie `session_token` |
| Candidat | Liste les offres disponibles, dépose un CV pour une offre, consulte « Mes candidatures » | Compte email+mot de passe, cookie `candidat_session_token` |

Le endpoint `/match` exige un candidat authentifié (`Depends(candidat_connecte)`) ;
la création/suppression d'offres exige un recruteur authentifié
(`Depends(recruteur_connecte)`). Aucune action de matching n'est possible de
façon anonyme.

## Observabilité

- Chaque appel à `/match` génère un **`correlation_id`** unique (UUID4),
  propagé dans l'état du pipeline, dans chaque entrée de trace des 5
  agents, dans les logs Python (`logger_monitoring`), persisté dans
  MongoDB (`decisions`) et renvoyé au client via l'en-tête de réponse
  `X-Correlation-Id`.
- Ce `correlation_id` est visible dans l'onglet **Superviseur** du
  dashboard pour relier un run complet à ses logs et à sa décision.

## Responsable humain & supervision

- **Propriétaire** : Ayoub Abdelmoughit — répond des décisions prises par
  l'agent, arbitre les dossiers en zone grise (30-69) depuis l'espace
  recruteur du dashboard.
- Chaque décision — automatique ou humaine — est tracée dans la collection
  MongoDB `audit_trail` (Jour 18).
- Chaque exécution du pipeline est tracée avec la latence de chaque agent
  et son `correlation_id` dans l'onglet **Superviseur** du dashboard
  (Jour 20/21).

## Limites connues

- Pas de lecture OCR pour les CV scannés en image — écarté volontairement
  du périmètre de ce projet (non requis par les critères de validation
  officiels du mini-projet).
- Les sessions (recruteur et candidat) sont en mémoire (non persistantes
  entre redémarrages du serveur) — simplification acceptée pour ce projet
  pédagogique, à remplacer par un store de session distribué (Redis par
  exemple) en production.
- Dépend de la disponibilité d'Ollama Cloud (clé API gratuite, pas de SLA).

## KPIs suivis

- Taux de décisions automatiques vs. revue humaine
- Latence moyenne par agent (onglet Superviseur)
- Taux d'échec / requêtes en Dead Letter Queue (`decisions_dlq`)
- Nombre d'offres actives / nombre de candidatures par offre

## Que faire en cas d'incident ?

Voir [`RUNBOOK.md`](./RUNBOOK.md).

Un incident réel (panne du fournisseur LLM) a été simulé et résolu avec ce
Runbook le 2026-10-30 — voir [`INCIDENT_LOG.md`](./INCIDENT_LOG.md) pour le
détail des 4 étapes appliquées.
