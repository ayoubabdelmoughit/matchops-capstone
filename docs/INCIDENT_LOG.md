# Journal d'Incident — MatchOps

Ce document trace un incident réel, simulé le **30 octobre 2026**, en suivant
les 4 étapes du [`RUNBOOK.md`](./RUNBOOK.md) (Jour 23).

## Résumé

| Champ | Valeur |
|---|---|
| Date | 2026-10-30, ~07:00 UTC+1 |
| Type | Panne du fournisseur LLM (Ollama Cloud) — scénario anticipé dans le Runbook |
| Cause | `OLLAMA_API_KEY` invalide (modifiée volontairement pour ce test) |
| `correlation_id` de référence | `a1851188-b2a4-4af5-adf1-1ac22c4a4d0b` |
| Sévérité | Moyenne — un seul agent (`extracteur_cv`) affecté, aucune perte de données |
| Statut | **Résolu** |

## 1. Détection

- Un candidat a soumis une candidature réelle via le dashboard et a reçu
  l'erreur suivante côté client :
  ```
  Erreur : Erreur pipeline: 401 Client Error: Unauthorized for url: https://ollama.com/api/chat
  ```
- Les logs serveur confirment la même erreur, **avec le `correlation_id`
  déjà rattaché avant même l'échec** — preuve que l'observabilité (Jour 21)
  fonctionne y compris pendant un incident :
  ```
  2026-10-30 07:02:17,157 INFO [correlation_id=a1851188-b2a4-4af5-adf1-1ac22c4a4d0b]
  agent=extracteur_cv statut=erreur duree_ms=1356.9
  INFO: "POST /match HTTP/1.1" 500 Internal Server Error
  ```
- L'onglet **Superviseur** ne montre pas ce run (la trace n'est persistée en
  base qu'en cas de pipeline complet) — confirmant un point d'amélioration
  noté en section « Suites » ci-dessous.

## 2. Contention

- Le pipeline a été laissé actif : une seule requête était en cours, aucun
  dossier candidat n'a été laissé dans un état incohérent (l'exception est
  interceptée dans `/match`, journalisée via `log_dlq`, et renvoyée au
  client sous forme d'erreur 500 claire plutôt qu'un plantage silencieux).
- Décision : ne pas accepter de nouvelles candidatures tant que la clé
  n'est pas corrigée, pour éviter d'accumuler des échecs dans la Dead
  Letter Queue (`decisions_dlq`).
- Responsable identifié et heure de détection notée (projet mono-personne).

## 3. Remédiation

Cause confirmée : `OLLAMA_API_KEY` dans `.env` invalide.

Action : clé restaurée à sa valeur correcte dans `.env`, puis redémarrage
du serveur (`uvicorn backend.main:app --reload`). Redémarrage propre
confirmé :
```
INFO:     Application startup complete.
```
(Les erreurs `401` sur `/metrics` et `/decisions` juste après sont la
conséquence attendue de la perte des sessions en mémoire au redémarrage —
limite déjà documentée dans l'[`AGENT_CARD.md`](./AGENT_CARD.md), pas un
nouvel incident : simple reconnexion nécessaire.)

## 4. Rétablissement

- Nouvelle candidature rejouée sur la même offre : pipeline complet
  exécuté avec succès — **score 95, statut « Approuvée »**, message
  personnalisé généré correctement (« Bonjour Ayoub Abdelmoughit, ... »).
- Le dernier run CI/CD (GitHub Actions) reste vert (`pytest` +
  `docker-build`), confirmant qu'aucune régression de code n'est liée à
  cet incident — la cause était uniquement une variable d'environnement.
- Aucune mise à jour de l'Agent Card nécessaire : l'incident correspond
  exactement au scénario déjà anticipé dans le Runbook (« Erreur Ollama
  401/429/503 »).

## Suites (amélioration continue)

- **Constat** : un run qui échoue avant le nœud `decideur` n'est pas
  visible dans l'onglet Superviseur (seules les traces de pipelines
  complets sont actuellement persistées). Amélioration future : persister
  aussi les traces partielles en cas d'échec, pour une visibilité complète
  des incidents directement dans le dashboard.
