# Architecture

```text
data.gouv.fr : flux quotidien (CSV)  ─┐   BCE : taux EUR/USD (CSV)   archives annuelles (XML zippé)
                                      │            │                          │
                                      └──── backend/download.py ──────────────┘   + data/raw/manifest.json
                                                   │
                                                   v
              backend/data.py + backend/sql/schema.sql  ->  SQLite data/carburants.db
                 stations (référentiel du flux) · stations_historique · prix · taux_change · calendrier
                                                   │
                                                   v
              backend/sql/table_analyse.sql : grille station × jour, prix connu à midi, taux de la veille
                                                   │
                                                   v
              backend/data.py (pandas) : cible et variables   ->  table_analyse (métriques figées)
                                                                ->  table_jour (conseil du jour)
                                                   │
                                                   v
              backend/model.py + backend/train.py : 2 forêts (prix seuls, prix + taux BCE), seuil issu
              des coûts, choix du modèle en validation croisée, top-3 des stations, K-means
                                                   │
                                                   v
                         models/modele.joblib + models/metriques.json
                                                   │
                                                   v
                         backend/service.py  (SEULE interface)  ->  frontend/app.py (Streamlit)
```

## Frontière backend/frontend

`frontend/app.py` importe uniquement `backend.service`. Il ne lit ni CSV ni XML, n'écrit pas de SQL, ne calcule ni seuil ni coût, et n'entraîne rien. `backend/` n'importe jamais Streamlit. Sans `frontend/`, `python -m backend.train` fait tout le travail.

## Rôle des modules

| Module | Rôle |
|---|---|
| `backend/config.py` | Chemins, URL des sources, périmètre, dates, hypothèses de flotte et de détour, seed |
| `backend/download.py` | Téléchargement du flux, du taux et des archives ; contrôle du format ; manifeste (URL, date, taille, SHA-256) |
| `backend/sql/schema.sql` | Schéma des tables SQLite |
| `backend/sql/table_analyse.sql` | Jointure des sources sur la grille station × jour, sans fuite |
| `backend/data.py` | Lecture du flux et des archives, chargement SQLite, variables et cible en pandas |
| `backend/model.py` | Forêt aléatoire, découpage temporel, seuil, regret, intervalle de confiance, choix de la station, K-means |
| `backend/train.py` | Pipeline complet, choix du modèle, diagnostic de qualité, sauvegarde |
| `backend/service.py` | Conseil du jour, rejeu d'un jour passé, stations proches, carte, croisement des sources, segments |
| `frontend/app.py` | 3 onglets : Décision, Exploration, Le modèle |

## Données et reproductibilité

- `data/raw/` : copies brutes immuables, hors Git, reconstruites par `python -m backend.download`.
- Les métriques sont figées par `DATE_FIN_DONNEES`. Le conseil du jour suit le flux le plus récent : `python -m backend.download --forcer`, puis `python -m backend.train`.
- Le choix des sources est expliqué dans `docs/adr/0001-sources-flux-quotidien-et-bce.md`.
