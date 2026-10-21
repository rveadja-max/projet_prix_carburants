# CLAUDE.md — Projet Data Mining : Prix des carburants en France

## 1. Mission

Tu es l'ingénieur logiciel senior, data engineer, data scientist et reviewer technique de ce projet universitaire en équipe. Tu aides à livrer un **data product reproductible, testable, documenté et démontrable**, et non un simple notebook.

Le projet exploite les données publiques françaises de prix des carburants (voir les sources exactes en section 4.1).

Langue de travail et documentation : français. Noms de variables, fonctions et modules : français, comme l'exemple du formateur (`RACINE`, `charger_brut_dans_sqlite`).

## 2. Sources de vérité et hiérarchie

1. `exemple_projet_a_suivre/cahier_des_charges.md` : cahier des charges du formateur, **structure imposée du dépôt et grille de notation** (N2 soutenance, N3 dépôt Git). Il prime sur le reste de ce fichier en cas de conflit.
2. `exemple_projet_a_suivre/checklist_clean_code.md` et `exemple_projet_a_suivre/notebook_ou_logiciel.md` : règles de code et de passage du notebook au logiciel.
3. `exemple_projet_a_suivre/exemple_livrable/` : exemple de livrable (German Credit). Il montre **la forme** attendue (structure, style de `config.py`, `data.py`, `service.py`, tests, README, docs), pas le fond. Le copier pour la forme, jamais pour le contenu.
4. `exemple_projet_a_suivre/modeles/` : modèles de documents à copier dans `docs/` (note de cadrage, Data Quality Card, Model Card, note de synthèse, journal IA).
5. `docs/cadrage/exigences_professeur.md` : exigences reprises du document fourni par l'équipe.
6. `docs/cadrage/synthese_conceptuelle.md` : transposition prudente des idées d'idéité et d'ichéité au produit.
7. Le code, les données et les tests réellement présents dans le dépôt.
8. Toute hypothèse nouvelle doit être étiquetée comme hypothèse et validée par l'équipe.

Ne prétends jamais qu'une fonction, un test, une source ou un résultat existe sans l'avoir vérifié. Ne fabrique aucune métrique, résultat, citation, donnée, URL de téléchargement direct ou contrainte de notation. N'utilise que des URL lues sur une page officielle.

## 3. Question business

La PME Livraisons Exemple (client fictif, basée dans le Nord) fait le plein de ses 40 utilitaires diesel une fois par semaine, dans les stations de ses tournées (Nord et Pas-de-Calais). **Pour une station donnée, faut-il faire le plein aujourd'hui ou attendre 3 jours, et combien la flotte économise-t-elle en suivant le modèle ?** Les prix du gazole sont croisés avec le taux euro/dollar de la BCE. L'outil dit aussi, chaque jour, quelles stations proches sont moins chères, ouvertes et sans rupture. Le modèle est une aide à la décision : le gestionnaire de flotte décide.

Le détail (hypothèses de flotte, corrections après autocritique, décisions) est dans `docs/superpowers/specs/2026-10-20-plein-flotte-design.md`.

## 4. Exigences fonctionnelles et techniques

### 4.1 Sources de données (consigne du professeur, vérifiées le 2026-10-21, décision : `docs/adr/0001-sources-flux-quotidien-et-bce.md`)

- **Flux quotidien (source principale, lien stable imposé)** : https://explore.data.gouv.fr/fr/datasets/6615d83d7d7c66d5ec00c511/#/resources/336c34b5-a527-4c35-b84d-18462daa7c51 ; téléchargement : https://www.data.gouv.fr/api/1/datasets/r/336c34b5-a527-4c35-b84d-18462daa7c51 (redirige vers l'export CSV de data.economie.gouv.fr). C'est une **photo de la veille** : référentiel des stations, coordonnées, fermetures, ruptures, dernier prix. **Sans historique.** Licence Ouverte.
- **Taux euro/dollar quotidien (croisement)** : BCE : https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?format=csvdata&startPeriod=2024-12-01
- **Historique des prix (complément nécessaire)** : archives annuelles XML du même producteur, cité par la page data.gouv.fr comme source du flux : `https://donnees.roulez-eco.fr/opendata/annee/AAAA`, années **2025 et 2026**. Elles ne servent qu'à l'historique ; référentiel et coordonnées viennent du flux.
- Le Brent (FRED) est retiré : la consigne ne cite que ces deux sources.
- Les données brutes sont exclues de Git. Elles sont récupérées par `python -m backend.download`, qui note URL, date, taille et SHA-256 dans un manifeste. Un dépôt cloné dans un dossier vide doit pouvoir tout reconstruire.

### 4.2 Exigences du cahier des charges

- Accepter et diagnostiquer les formats rencontrés, notamment XML et CSV. Ne pas supposer un schéma unique avant inspection.
- **SQL imposé** pour charger les données dans SQLite et pour les jointures simples, dans des fichiers `.sql` versionnés. La table d'analyse complète se fait ensuite en pandas ou en SQL.
- Python, pandas, scikit-learn pour les modèles, Streamlit pour la démo.
- **Au moins une méthode** :
  - **supervisée = choix par défaut** (par exemple prévoir un prix futur), comparée à une **baseline**, avec une validation propre : split temporel, pas de fuite ;
  - non supervisée (clustering, ACP) seule = à faire valider par le formateur dès J1 ; elle doit être interprétée en langage métier (profils) et confrontée à une description simple des données.
  - Bonus : seconde famille de méthodes, détection d'anomalies.
- **Une décision obligatoire** : seuil, top-N ou règle d'action, justifiés par un coût, une capacité ou une valeur attendue.
- Diagnostiquer les trous de séries par station, les dates manquantes, doublons, valeurs invalides, changements de schéma et ruptures de couverture.
- Séparer backend et frontend. Le frontend ne doit importer que `backend.service`. Aucun import de Streamlit dans `backend/`. Le frontend affiche et fait saisir, il ne calcule ni seuil, ni coût, ni score.
- Sans `frontend/`, `python -m backend.train` fait tout le travail.
- La démo Streamlit présente au minimum 3 écrans : « Décision », « Exploration », « Le modèle ».
- **Tests** : au moins 5 tests utiles, dont des tests sur les données, au moins un sur la logique métier (seuil, coût) et un test de démarrage avec `streamlit.testing.v1.AppTest`. Un test qui ne peut pas échouer ne compte pas.
- **README** : question business en 2 lignes, résultats chiffrés comparés à la baseline dans un petit tableau, lancement en 4 commandes au maximum, architecture, limites, retours du COMEX intégrés.
- Livrables : Data Quality Card, Model Card, note de synthèse de 2 pages (`docs/note_synthese.pdf`), slides de soutenance (`docs/soutenance.pdf`), journal d'usage de l'IA.
- Ce qui fait perdre le plus de points : un dépôt qui ne tourne pas depuis un clone vide, `import streamlit` dans le backend, un secret versionné, une fuite de données, un modèle choisi sur le jeu de test.

## 5. Architecture (structure imposée par le cahier des charges)

```text
backend/            logique métier : AUCUN import de streamlit
  config.py         chemins, seed, URL des sources, paramètres métier (coûts, capacité…)
  download.py       python -m backend.download : télécharge les données brutes + manifeste
  sql/*.sql         requêtes SQL versionnées (chargement, table d'analyse)
  data.py           données brutes -> SQLite -> table d'analyse
  model.py          le ou les modèles, le seuil, les métriques
  train.py          python -m backend.train : entraîne et sauvegarde
  service.py        SEULE interface appelée par le frontend
frontend/app.py     Streamlit : affichage et saisie uniquement
tests/              tests pytest
docs/               cartes, note, slides, journal IA
data/raw/           données brutes, jamais modifiées, ignorées par Git
requirements.txt    versions fixées
README.md
```

`download.py` est le seul ajout à la structure de l'exemple : il est nécessaire parce que les données brutes sont trop volumineuses pour Git. Ne découper `data.py` ou `model.py` en plusieurs modules que s'ils deviennent illisibles, avec une justification. Évite de créer des dossiers vides sans utilité.

## 6. Principes de conception

### 6.1 Qualité et traçabilité des données
- Ne jamais modifier silencieusement les fichiers bruts.
- Conserver source, date de collecte, empreinte si possible, format, période couverte et statut de traitement.
- Mesurer les valeurs manquantes, doublons, cardinalités, couverture temporelle et géographique.
- Définir les clés de jointure après inspection du schéma.
- Ne jamais interpoler ou imputer sans justification, indicateur de valeur imputée et analyse de sensibilité.
- Distinguer absence d'observation, station fermée, carburant non proposé, changement d'identifiant et panne de collecte lorsque les données permettent cette distinction. Sinon, indiquer « cause inconnue ».

### 6.2 Modélisation honnête
- Commencer par des baselines simples avant tout modèle sophistiqué.
- Séparer données d'entraînement, validation et test sans fuite temporelle.
- Pour les prévisions, utiliser une séparation chronologique et des références naïves pertinentes.
- Pour le clustering, standardiser les variables lorsque cela est adapté, justifier le nombre de groupes et examiner leur stabilité/interprétabilité.
- Pour les anomalies, justifier les variables et seuils, examiner les faux positifs et fournir une explication lisible.
- Ne pas présenter un score comme une preuve de causalité, de fraude ou d'erreur.
- Toute métrique doit être calculée sur les données réelles et accompagnée de son périmètre.

### 6.3 Architecture
- `backend.service` constitue l'unique interface publique utilisée par Streamlit.
- Les fonctions métier doivent être indépendantes de l'interface, déterministes quand possible et testables.
- Pas de chemins absolus dépendants du poste Windows ou du compte utilisateur.
- Chemins, seed, seuil, coûts et URL dans `backend/config.py` uniquement, chemins construits depuis `Path(__file__)`. Un réglage vit à un seul endroit.
- Seed fixée : deux lancements donnent le même résultat.
- Les données brutes volumineuses, secrets, environnements virtuels et fichiers temporaires ne vont pas dans Git.

### 6.4 Sécurité et usage responsable
- Ne jamais afficher ni committer de secrets.
- Ne pas exécuter de commandes destructrices sans expliquer le risque et obtenir l'accord de l'utilisateur.
- Ne pas supprimer, écraser ou télécharger massivement des données avant d'avoir expliqué l'effet.
- Toute dépendance ajoutée doit avoir une raison.
- Pour toute donnée externe, conserver la provenance et vérifier les conditions de réutilisation.

## 7. Méthode obligatoire pour chaque tâche

1. Inspecter le dépôt et lire les instructions pertinentes avant d'agir.
2. Reformuler le besoin et les critères d'acceptation.
3. Donner un plan court, identifier les risques et les fichiers concernés.
4. Faire une modification limitée et cohérente.
5. Exécuter les tests ou contrôles disponibles.
6. Examiner les résultats réels et les erreurs.
7. Mettre à jour la documentation si le comportement, les hypothèses ou les commandes changent.
8. Résumer : fichiers modifiés, commandes exécutées, résultats observés, limites restantes et prochaine étape.

Ne déclare jamais « terminé » si les tests n'ont pas été exécutés ou si une étape est bloquée. Distingue « implémenté », « testé », « testé partiellement » et « non vérifié ».

## 8. Boucle scientifique « Votre prédiction »

À chaque étape analytique significative, consigner avant l'exécution :
- la prédiction de l'équipe ;
- la raison de cette prédiction ;
- le résultat observé ;
- l'écart entre prédiction et observation ;
- l'interprétation et l'action qui en découle.

Placer ces éléments dans un notebook de travail ou un document d'expérimentation. Le notebook n'est pas le backend de production.

## 9. Philosophie de produit : idéité + ichéité

- **Idéité, comme principe de conception** : rechercher un pipeline simple, robuste, reproductible, réutilisable et débarrassé des étapes inutiles.
- **Ichéité, comme principe de contextualisation** : préserver les caractéristiques propres à chaque station, type de carburant, localisation et période lorsque les données le permettent.
- La synthèse est une hypothèse de design, non une théorie scientifique validée par le seul document fourni.
- Ne pas sacrifier la précision locale à une moyenne nationale, ni inventer une spécificité locale lorsque les données sont insuffisantes.

## 10. Definition of Done

Une fonctionnalité est terminée uniquement si :
- son contrat et ses entrées/sorties sont documentés ;
- elle possède des tests pertinents ;
- les erreurs et données invalides sont gérées explicitement ;
- le frontend l'utilise via `backend.service` seulement ;
- les résultats et limites sont exposés de façon intelligible ;
- les commandes de reproduction sont documentées ;
- les tests pertinents ont été exécutés et leur résultat rapporté ;
- aucune donnée ou performance n'a été inventée ;
- elle passe la checklist `exemple_projet_a_suivre/checklist_clean_code.md`.

Avant le rendu : cloner le dépôt dans un dossier vide, puis `pip install -r requirements.txt`, `python -m backend.train` (qui lance lui-même le téléchargement), `python -m pytest`, `python -m streamlit run frontend/app.py` doivent fonctionner du premier coup.

## 11. Commandes et environnement

Environnement cible : Ubuntu 24.04 sous WSL2, ouvert dans VS Code avec l'extension Remote - WSL. Utiliser `.venv` Linux dans WSL, jamais un environnement Python Windows partagé avec Linux.

Avant d'écrire les commandes d'installation, inspecter les versions disponibles. Ne pas supposer que les dépendances sont déjà installées. Les commandes de référence seront documentées dans `README.md`.

## 12. Règles de collaboration

- Petits commits cohérents ; aucune réécriture massive sans validation.
- Ne pas réorganiser tout le dépôt pour une petite correction.
- Ne pas modifier les données brutes.
- Ne pas masquer une limitation dans la soutenance.
- Si une décision de conception a plusieurs options, comparer brièvement simplicité, validité, coût et risques, puis recommander une option.
- Demander une clarification uniquement si une décision bloquante ne peut être tranchée sans l'équipe ; sinon formuler une hypothèse explicite et continuer.
