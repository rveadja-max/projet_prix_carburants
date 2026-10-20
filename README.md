# SEP Conseil et Livraisons Exemple : aide au plein de la flotte

> Projet de formation (data mining). Datasets : [prix des carburants en France](https://www.prix-carburants.gouv.fr/rubrique/opendata/) (Licence Ouverte), cours du Brent de l'EIA via [FRED](https://fred.stlouisfed.org/series/DCOILBRENTEU) (domaine public) et taux euro/dollar de la [BCE](https://data.ecb.europa.eu/). Équipe : [à compléter par l'équipe].

## Question business

La PME Livraisons Exemple, basée dans le Nord, fait le plein de ses 40 utilitaires diesel une fois par semaine dans les stations de ses tournées (Nord et Pas-de-Calais). Le gestionnaire de flotte peut avancer ou décaler un plein de quelques jours. **Pour une station donnée, faut-il faire le plein aujourd'hui ou attendre 3 jours, et combien la flotte économise-t-elle en suivant le modèle ?**

Hypothèses fictives : 40 véhicules, 60 L par plein, 1 plein par semaine, soit 124 800 L par an (réglées dans `backend/config.py`).

## Résultats (jeu de test : 55 262 lignes station-jour, du 2026-05-04 au 2026-10-16)

Regret d'une décision = prix payé − min(prix aujourd'hui, prix dans 3 jours), en c€/L.

| Stratégie | Regret moyen (c€/L) |
|---|---|
| Toujours faire le plein tout de suite (situation actuelle) | 1,24 |
| Toujours attendre 3 jours | 1,60 |
| Modèle sans Brent, seuil issu des coûts | 0,90 |
| Modèle avec Brent de la veille, seuil 0,5 | 0,86 |
| **Modèle avec Brent de la veille, seuil issu des coûts (0,26)** | **0,66** |
| Modèle avec Brent à 8 jours de retard, seuil issu des coûts | 0,93 |
| Plafond : connaître l'avenir | 0,00 |

- ROC-AUC de 0,70 sur le test, et de 0,69 ± 0,01 en validation croisée (modèle avec Brent de la veille).
- La variable la plus utile est la variation du Brent sur 7 jours (importance par permutation).
- La segmentation K-means (3 segments) isole 67 stations chères, à 7,76 c€/L au-dessus de la médiane de leur département en moyenne.

Le meilleur écart avec la situation actuelle est de 0,58 c€/L, soit environ 730 € par an pour la flotte fictive (124 800 L). Le plafond (connaître l'avenir) vaut 1,24 c€/L, soit environ 1 550 € par an : l'enjeu est modeste.

## Lancer le projet

Dans un environnement virtuel (`python -m venv .venv`, puis `source .venv/bin/activate` sous WSL ou Linux) :

```bash
pip install -r requirements.txt
python -m backend.train                 # téléchargement, SQLite + table d'analyse SQL + entraînement
python -m pytest                        # 45 tests
python -m streamlit run frontend/app.py # démonstrateur
```

Le premier lancement télécharge environ 62 Mo et a besoin du réseau (le premier `pytest` d'un clone vide aussi, s'il doit entraîner le modèle). SQLite 3.35 ou plus est nécessaire (le Python 3.14 du projet l'embarque). Les données sont figées au 2026-10-19 (`DATE_FIN_DONNEES`) : un nouveau téléchargement ne change pas les chiffres.

## Architecture : backend et frontend séparés

```
backend/                 logique métier (aucun import de streamlit)
  config.py              chemins, seed, sources, périmètre, hypothèses de flotte
  download.py            téléchargement des archives, du Brent et du taux de change + manifeste
  sql/table_analyse.sql  table d'analyse construite en SQL (prix, stations, Brent, taux)
  data.py                fichiers bruts -> SQLite -> table d'analyse
  model.py               Random Forest, seuil, regret, K-means
  train.py               entraînement des 3 modèles et sauvegarde
  service.py             SEULE interface appelée par le frontend
frontend/
  app.py                 Streamlit : affichage uniquement (3 onglets)
tests/                   tests du backend et démarrage de l'appli
docs/                    note de cadrage, Data Quality Card, Model Card, note de synthèse, journal IA, plan de soutenance
data/raw/                données brutes (jamais modifiées, ignorées par Git)
models/                  modèle et métriques produits par l'entraînement (ignorés par Git)
```

**Règle :** le frontend n'importe que `backend.service`. On pourrait remplacer Streamlit par une API FastAPI ou un autre front sans toucher au backend.

## Limites

- Le Brent de la veille suppose un flux quotidien. La source gratuite (EIA via FRED) arrive par lots : le 2026-10-20, la dernière valeur datait du 2026-10-14. En usage réel, il faut un cours quotidien (abonnement ou relevé manuel le matin).
- Avec le retard réel de 8 jours, le modèle fait pire que sans Brent : regret de 0,93 c€/L contre 0,90, et ROC-AUC de 0,67 contre 0,68. Le gain annoncé ne vaut que si le Brent de la veille est disponible.
- Le gain a un plafond : 1,24 c€/L en connaissant l'avenir, environ 1 550 € par an pour la flotte fictive. Le modèle en capte 0,58 c€/L.
- Le modèle conseille de faire le plein dans 62 % des cas. Il ne dit « attendre » que dans une minorité de situations.
- Une seule période de test (2026-05-04 → 2026-10-16), pendant une crise des prix (gazole et Brent en forte hausse en 2026). Les résultats ne sont pas garantis hors de ce contexte, et la validation croisée varie d'un pli à l'autre (écart-type de 0,01 à 0,06 selon le modèle).
- Le 1er janvier 2026, la médiane nationale saute de 1,554 à 1,599 €/L en deux jours. La cause n'est pas vérifiée (une évolution de fiscalité est probable, non confirmée).
- Les volumes de la flotte (40 véhicules, 60 L, 1 plein par semaine) sont fictifs. Les euros par an en dépendent directement.
- Gazole seulement, départements 59 et 62, stations hors autoroute. Aucun calcul d'itinéraire ni de détour.
- Le modèle est une aide à la décision : le gestionnaire décide.

## Retours du COMEX et ce que nous avons changé

| Retour | Ce que nous avons changé |
|---|---|
| à remplir après le J3 | à remplir après le J3 |

La note de synthèse est écrite en Markdown (`docs/note_synthese.md`), puis exportée en PDF (`docs/note_synthese.pdf`) à la main par l'équipe. Les slides sont exportées de la même façon en `docs/soutenance.pdf`.
