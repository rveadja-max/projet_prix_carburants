# Journal d'usage de l'IA

> Exemple de journal pour le projet German Credit. Le code final est réel : chaque ligne renvoie à un fichier de ce dépôt. Les prompts et les réponses de l'IA sont reconstitués pour la formation.

**Outils utilisés :** un assistant de code dans l'éditeur, et un chat pour les questions de méthode.

| # | Fichier ou étape | Le prompt (résumé) | Ce que l'IA a produit | Gardé | Corrigé, et pourquoi | Refusé, et pourquoi |
|---|---|---|---|---|---|---|
| 1 | `backend/sql/table_analyse.sql` | « Décode les codes A11, A12... du fichier German Credit en libellés lisibles » | Un grand `CASE WHEN` par variable | La structure en `CASE WHEN` | Deux libellés inversés pour `statut_compte`, vérifiés dans la documentation UCI (**correct**) | |
| 2 | `backend/model.py` | « Entraîne un modèle pour prédire le défaut » | Une forêt aléatoire avec SMOTE, évaluée à l'accuracy | La forêt aléatoire dans un `Pipeline` | L'accuracy remplacée par le coût moyen et la ROC-AUC : avec 30 % de défauts, l'accuracy cache les erreurs coûteuses (**validation**) | SMOTE appliqué **avant** le split : des copies des demandes du test se retrouvaient dans l'entraînement (**fuite de données**). Remplacé par `class_weight="balanced"` |
| 3 | `backend/model.py` | « Quel seuil de décision utiliser ? » | `predict()`, donc un seuil de 0,5 | | Seuil calculé à partir des coûts de `config.py` : 1/6. Le coût moyen passe de 0,70 à 0,58 (**décision business**) | |
| 4 | `backend/service.py` | « Évite de recharger le modèle à chaque clic » | `@st.cache_resource` sur la fonction de chargement | L'idée de mettre le modèle en cache | `functools.lru_cache` à la place : le backend ne doit pas importer streamlit (règle de séparation) | |
| 5 | `backend/service.py` | idem | `joblib.load` sans vérification | | Message clair si le modèle n'existe pas encore : « lancer d'abord python -m backend.train » (**robustesse**) | |
| 6 | `tests/test_backend.py` | « Écris des tests pour le backend » | 6 tests, dont `assert modele is not None` et `assert len(table) > 0` | Le test « une ligne par demande » | | Les tests qui ne peuvent pas échouer (**tests**). Remplacés par un test sur le seuil et un test « aucune variable sensible dans le modèle » |
| 7 | `requirements.txt` | « Donne les dépendances du projet » | 11 paquets, dont `imbalanced-learn`, `seaborn` et `xgboost` | pandas, scikit-learn, joblib, streamlit, pytest | Versions fixées (**reproductibilité**) | Les paquets inutilisés (**dépendances**) |

## Bilan en 3 lignes

- **Ce que l'IA nous a fait gagner :** le décodage SQL et le squelette de l'application Streamlit, écrits en quelques minutes.
- **L'erreur qui nous aurait coûté le plus cher :** SMOTE avant le split. Le score affiché était trop beau, et faux. Nous l'aurions présenté au COMEX.
- **Ce que nous ne lui confierions pas sans relecture :** le choix de la métrique et du seuil. L'IA ne connaît pas les coûts du client.
