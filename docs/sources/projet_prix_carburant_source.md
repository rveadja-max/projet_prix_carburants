Nous sommes des consultants : on part toujours de la décision du client.
Trois notes d'équipe, avec des grilles connues dès aujourd'hui.

Chaque étape d'un notebook contient une cellule « Votre prédiction ».

Vous écrivez le résultat que vous attendez : un chiffre, un ordre de grandeur, une tendance.
Vous exécutez.
Si le résultat vous surprend, c'est là que vous apprenez quelque chose.
Un dataminer qui ne s'étonne jamais ne regarde pas ses résultats.

Le livrable est un data product : backend, frontend, documents, soutenance.

# Notre livrable : un data product, pas un notebook

Un dépôt Git, avec un backend (données, SQL, modèles) et un frontend Streamlit séparés.
Une démo où un utilisateur métier choisit un cas et voit la recommandation.
Des documents : Data Quality Card, Model Card, note de synthèse de 2 pages, journal d'usage de l'IA.
Tout est écrit dans le cahier des charges : projet/cahier_des_charges.md.

Le frontend affiche c'est à dire ==> Ce qu'on voit souvent ==> Un seul fichier app.py qui lit le CSV, entraîne le modèle et affiche le résultat. Impossible à tester, impossible à réutiliser.
et le backend décide, c'est à dire ==> Ce qu'on attend ==> backend/ fait tout le travail. frontend/app.py n'appelle que backend/service.py. Si on supprime le frontend, le backend marche encore.



## dataset voici le lien pour télécharger les données ===>  https://www.data.gouv.fr/datasets/prix-des-carburants-en-france-flux-quotidien

clustering
détection d'anomalies
série temporelle
Piège à trouver et résoudre: Formats XML/CSV ; trous dans les séries par station


## Outils utilisés : SQL et Python se complètent
SQL est imposé pour
extraire les données ;
joindre les tables ;
construire la table d'analyse.
Ensuite, au choix
pandas ou SQL pour explorer ;
scikit-learn pour les modèles ;
Streamlit pour la démo.
Attention : En entreprise, les données sont dans une base. Savoir les en sortir proprement, c'est la moitié du métier.

## Démo : à quoi ressemble un livrable réussi
Un exemple complet, sur un autre sujet (le crédit bancaire, Ce sujet est réservé à l'exemple) : projet/exemple_livrable/ nous servira pour faire le notre.

1-L'écran « Décision » : un dossier, une recommandation.
2-L'écran « Exploration » : les profils.
3-L'écran « Le modèle » : les chiffres et les limites, en clair.

# Une soutenance réussie raconte une décision
1-Un titre de sujet « Résultats du modèle »

2-Un titre de conclusion « Appeler 300 clients par mois évite 40 départs »

Parlez en euros ou en clients avant de parler de ROC-AUC.
Dites vos limites vous-mêmes.
Finissez par une décision demandée, pas par « des questions ? ».


## Question business

exemple de question business ==> La banque accorde des crédits à la consommation. Accorder un crédit à un client qui fera défaut coûte **5 fois plus** que refuser un bon client. **Quelles demandes faut-il accorder, et lesquelles faut-il étudier de plus près ?**

## Lancer le projet

```bash
python -m venv .venv && source .venv/Scripts/activate   # Windows (Git Bash)
pip install -r requirements.txt
python -m backend.train                 # SQLite + table d'analyse SQL + entraînement
python -m pytest                        # 8 tests
python -m streamlit run frontend/app.py # démonstrateur


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
**Règle :** le frontend n'importe que `backend.service`. On pourrait remplacer Streamlit par une API FastAPI ou un autre front sans toucher au backend.

## Limites

Un des exemples de limites qu'on peut avoir pour le sujet bancaire
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
