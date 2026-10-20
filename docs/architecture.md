# Architecture cible

```text
data.gouv.fr / fichiers source
          |
          v
backend.data.source -> parsing XML/CSV -> validation / profilage
          |                                  |
          v                                  v
     SQLite ou base SQL <--- schéma / tables / requêtes SQL
          |
          v
table d'analyse SQL -> features -> modèles -> évaluation
                                            |
                                            v
                                   backend.service
                                            |
                                            v
                                      frontend/app.py
                                         Streamlit
```

## Frontière backend/frontend
`frontend/app.py` importe uniquement les fonctions publiques de `backend.service`. Il ne lit pas les CSV/XML, ne construit pas de requêtes SQL et n'entraîne pas de modèle.

## Rôle des composants
- `backend/data/source.py` : provenance et découverte des fichiers.
- `backend/data/parsing.py` : lecture contrôlée des formats réels détectés.
- `backend/data/validation.py` : schéma, types, doublons, valeurs impossibles et couverture.
- `backend/data/database.py` : chargement SQL et transactions.
- `backend/sql/schema.sql` : tables normalisées.
- `backend/sql/table_analyse.sql` : jointures et construction de la table d'analyse.
- `backend/features.py` : variables dérivées documentées.
- `backend/models/` : clustering, anomalies, séries temporelles.
- `backend/evaluation.py` : baselines, protocoles et métriques.
- `backend/train.py` : pipeline reproductible.
- `backend/service.py` : API métier stable appelée par le frontend.
- `frontend/app.py` : présentation, filtres et visualisations.
- `tests/` : tests unitaires, intégration et test de démarrage.

## Stockage
SQLite est un choix de départ raisonnable pour un prototype local, mais le volume et les formats réels doivent être mesurés avant de le figer. SQL reste obligatoire quelle que soit la technologie relationnelle retenue.

## Données et reproductibilité
- `data/raw/` : copie source immuable.
- `data/interim/` : transformations intermédiaires reproductibles.
- `data/processed/` : données analytiques reconstruites par pipeline.
- Les données volumineuses ne sont pas versionnées dans Git par défaut.
- Conserver métadonnées, dates, provenance et empreintes de fichiers lorsque possible.
