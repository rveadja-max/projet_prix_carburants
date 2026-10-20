# SEP Conseil et Banque Exemple : aide à l'octroi de crédit

> **Exemple de livrable** fourni par le formateur. Il montre la forme attendue, pas le fond : votre projet porte sur **votre** dataset et **votre** question. Dataset : [UCI German Credit](https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data) (CC BY 4.0), réservé à cet exemple.

## Question business

La banque accorde des crédits à la consommation. Accorder un crédit à un client qui fera défaut coûte **5 fois plus** que refuser un bon client. **Quelles demandes faut-il accorder, et lesquelles faut-il étudier de plus près ?**

## Résultats (jeu de test, 250 demandes)

| Stratégie | Coût moyen par demande |
|---|---|
| Tout accepter (situation actuelle) | 1,50 |
| Random Forest, seuil 0,5 | 0,70 |
| **Random Forest, seuil issu des coûts (1/6)** | **0,58** |

- ROC-AUC de 0,79 sur le test, et de 0,79 ± 0,03 en validation croisée.
- La variable la plus utile est le statut du compte courant (importance par permutation).
- La segmentation K-means (3 segments) isole des crédits longs et élevés, avec un taux de défaut de 47 % contre 30 % en moyenne.

## Lancer le projet

Dans un environnement virtuel (`python -m venv .venv`, puis `source .venv/Scripts/activate` sous Git Bash) :

```bash
pip install -r requirements.txt
python -m backend.train                 # SQLite + table d'analyse SQL + entraînement
python -m pytest                        # 8 tests
python -m streamlit run frontend/app.py # démonstrateur
```

## Architecture : backend et frontend séparés

```
backend/                 logique métier (aucun import de streamlit)
  config.py              chemins, seed, matrice de coûts
  sql/table_analyse.sql  table d'analyse construite en SQL
  data.py                fichier brut -> SQLite -> table d'analyse
  model.py               Random Forest, seuil, coût, K-means
  train.py               entraînement et sauvegarde du modèle
  service.py             SEULE interface appelée par le frontend
frontend/
  app.py                 Streamlit : affichage uniquement
tests/                   tests du backend et démarrage de l'appli
docs/                    Data Quality Card, Model Card, note de synthèse, journal IA, plan de soutenance
data/raw/                données brutes (jamais modifiées)
```

**Règle :** le frontend n'importe que `backend.service`. On pourrait remplacer Streamlit par une API FastAPI ou un autre front sans toucher au backend.

## Limites

- 1 000 demandes allemandes des années 1990 : l'exemple n'est pas transposable tel quel à une banque d'aujourd'hui.
- Les variables sensibles (sexe et statut marital, nationalité) sont exclues, mais d'autres, comme l'âge, peuvent jouer le même rôle. Voir `docs/model_card.md`.
- Au seuil de 1/6, 208 demandes sur 250 (83 %) partent en étude approfondie. C'est rentable avec ces coûts, mais seulement si les conseillers ont le temps.
- Le modèle est une aide à la décision : le conseiller décide.

## Retours du COMEX et ce que nous avons changé

| Retour | Ce que nous avons changé |
|---|---|
| Direction financière : « Combien de dossiers en étude, concrètement ? » | Nombre de dossiers en étude ajouté aux limites et à la note de synthèse |
| Protection des données : « Et l'âge ? » | Suivi des refus par tranche d'âge ajouté au plan de suivi (`docs/note_synthese.md`) |
| DSI : « Qui relance l'entraînement ? » | Règle de réentraînement ajoutée à la Model Card |

La note de synthèse est écrite en Markdown (`docs/note_synthese.md`), puis exportée en PDF pour le client.
