# Runbook d'Incident — MatchOps

Ce document est écrit **avant** l'incident, pour ne pas improviser sous
pression. Il suit les 4 étapes vues en Jour 23.

## 1. Détection

Signaux qu'un incident est en cours :

- Un candidat reçoit un message incohérent ou vide (`message_final` vide).
- Le score de matching semble aberrant (ex : 0 ou 100 systématique).
- L'onglet **Superviseur** montre un agent avec `statut: "erreur"` dans la
  trace, ou une latence anormalement élevée (> 10s par agent).
- Des entrées s'accumulent dans la Dead Letter Queue (`decisions_dlq`).
- Le backend ne répond plus (`/metrics` timeout ou 500).

## 2. Contention

1. Ne pas couper le pipeline en plein milieu d'une requête en cours
   (risque de dossier candidat orphelin).
2. Si Ollama Cloud est en panne : arrêter temporairement le endpoint
   public `/match` (variable d'environnement ou commentaire rapide de la
   route) pour éviter d'accumuler des échecs dans la DLQ.
3. Alerter le responsable (Ayoub Abdelmoughit) — dans ce projet
   mono-personne, se noter l'incident et l'heure de détection.

## 3. Remédiation

Selon la cause :

| Symptôme | Action |
|---|---|
| Erreur Ollama (401/429/503) | Vérifier `OLLAMA_API_KEY` dans `.env`, vérifier le quota du compte Ollama Cloud |
| `ConfigurationError` MongoDB (DNS/SRV) | Utiliser la connection string sans SRV (hosts explicites `shard-00-00/01/02`), voir `.env` |
| Score de matching incohérent | Vérifier le prompt de `matcher.py`, rejouer un cas connu avec `test_matcher.py` |
| Régression après un changement de code | `git log --oneline` pour identifier le commit fautif, puis `git revert <hash> --no-edit` (voir ci-dessous) |
| Session recruteur perdue après redémarrage | Attendu (sessions en mémoire) — se reconnecter, documenté dans les limites de l'Agent Card |

### Rollback avec Git

```bash
# Annuler un commit précis sans effacer l'historique (recommandé) :
git revert <hash-du-commit> --no-edit
git push origin main

# Revenir à un tag stable connu (destructif, usage exceptionnel) :
git reset --hard v1.0.0
```

`git revert` est préféré : il crée un nouveau commit qui annule le
changement, sans effacer l'historique — contrairement à
`git reset --hard`, destructif et à éviter en équipe/production.

## 4. Rétablissement

1. Rejouer les cas de test (`tests/test_decideur.py` + un cas réel via
   `/match`) pour confirmer que le comportement est redevenu correct.
2. Vérifier l'onglet **Pipeline CI/CD** : le dernier run GitHub Actions
   doit être vert avant de considérer l'incident clos.
3. Mettre à jour l'[`AGENT_CARD.md`](./AGENT_CARD.md) si l'incident a
   révélé une nouvelle limite de l'agent.
4. Poser un tag Git (patch, `vX.Y.Z+1`) documentant le correctif.
