# Agent Card — MatchOps

## Identité

| Champ | Valeur |
|---|---|
| Nom | MatchOps — Agent de Matching Candidat ↔ Offre d'Emploi |
| Version | v1.0.0 |
| Responsable | Ayoub Abdelmoughit (propriétaire & technique) |
| Domaine | Marché du travail / Recrutement |

## Que fait l'agent ?

MatchOps lit un CV (PDF) et le texte d'une offre d'emploi, calcule un score
de compatibilité de 0 à 100, puis décide automatiquement (approuvé /
rejeté) ou transmet le dossier à un recruteur humain pour arbitrage si le
score est ambigu. Un message est ensuite rédigé pour le candidat, adapté à
la décision prise.

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

## Responsable humain & supervision

- **Propriétaire** : Ayoub Abdelmoughit — répond des décisions prises par
  l'agent, arbitre les dossiers en zone grise (30-69) depuis l'espace
  recruteur du dashboard.
- Chaque décision — automatique ou humaine — est tracée dans la collection
  MongoDB `audit_trail` (Jour 18).
- Chaque exécution du pipeline est tracée avec la latence de chaque agent
  dans l'onglet **Superviseur** du dashboard (Jour 20/21).

## Limites connues

- Pas de lecture OCR pour les CV scannés en image (seuil de détection
  présent dans le code, bascule non encore implémentée).
- Les comptes recruteurs utilisent une session en mémoire (non persistante
  entre redémarrages du serveur) — simplification acceptée pour ce projet
  pédagogique, à remplacer par un store de session distribué en production.
- Dépend de la disponibilité d'Ollama Cloud (clé API gratuite, pas de SLA).

## KPIs suivis

- Taux de décisions automatiques vs. revue humaine
- Latence moyenne par agent (onglet Superviseur)
- Taux d'échec / requêtes en Dead Letter Queue (`decisions_dlq`)

## Que faire en cas d'incident ?

Voir [`RUNBOOK.md`](./RUNBOOK.md).
