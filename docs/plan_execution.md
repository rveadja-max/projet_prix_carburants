# Plan d'exécution en portes de validation

Ne passez pas à la phase suivante tant que la porte actuelle n'est pas validée par au moins un membre de l'équipe autre que l'auteur principal.

## Phase 0 — Cadrage
- [ ] Lire le cahier des charges complet et récupérer la grille de notation.
- [ ] Valider la question métier, les utilisateurs et le périmètre.
- [ ] Transformer les exigences en critères d'acceptation.
- [ ] Répartir les rôles et convenir des règles Git.

**Porte :** un cadrage accepté par toute l'équipe.

## Phase 1 — Environnement et dépôt
- [ ] Ouvrir le dépôt depuis Ubuntu 24.04/WSL dans VS Code.
- [ ] Créer `.venv` Linux et vérifier Python, Git, VS Code Remote WSL.
- [ ] Initialiser Git, `.gitignore`, structure et instructions.
- [ ] Ajouter tests de fumée et CI si le temps le permet.

**Porte :** installation reproductible depuis un clone propre.

## Phase 2 — Audit des données
- [ ] Télécharger depuis la page officielle et noter la date.
- [ ] Inventorier tous les fichiers, formats, tailles, schémas et périodes.
- [ ] Identifier les clés, unités, codes carburants et dates.
- [ ] Quantifier doublons, valeurs manquantes, incohérences et trous par station.
- [ ] Documenter les causes connues et inconnues.

**Porte :** Data Quality Card initiale et décision sur le périmètre analysable.

## Phase 3 — SQL et table d'analyse
- [ ] Définir schéma et clés après inspection des données.
- [ ] Charger les sources de façon contrôlée et idempotente.
- [ ] Écrire les jointures et la table d'analyse en SQL.
- [ ] Tester unicité, cardinalités, intégrité et lignes attendues.
- [ ] Vérifier que les jointures ne multiplient ou ne perdent pas silencieusement les observations.

**Porte :** table d'analyse reproductible et contrôles réussis.

## Phase 4 — Exploration et prédictions
- [ ] Chaque étape analytique commence par « Votre prédiction ».
- [ ] Explorer prix par carburant, zone et temps si disponibles.
- [ ] Examiner les trous de séries et les ruptures de couverture.
- [ ] Consigner les résultats surprenants et les explications possibles.

**Porte :** décisions de préparation justifiées par l'exploration.

## Phase 5 — Modèles
- [ ] Construire une baseline pour chaque famille pertinente.
- [ ] Clustering : choisir variables, mise à l'échelle, nombre de groupes et interprétation.
- [ ] Anomalies : définir le référentiel, les seuils et la revue d'un échantillon.
- [ ] Séries temporelles : vérifier la fréquence et la couverture, séparer chronologiquement, comparer à une baseline.
- [ ] Comparer résultats, limites et coûts de calcul.

**Porte :** chaque modèle a un protocole, des résultats réels et une limite documentée.

## Phase 6 — Service et interface
- [ ] Exposer les fonctions nécessaires par `backend.service`.
- [ ] Construire les vues Décision, Exploration, Le modèle.
- [ ] Montrer le contexte, la justification et les limites des recommandations.
- [ ] Tester que le frontend ne contourne pas le service.

**Porte :** démonstration fluide sur un cas réel reproductible.

## Phase 7 — Qualité et documents
- [ ] Tests unitaires, intégration, données invalides, trous temporels et démarrage.
- [ ] Data Quality Card et Model Card cohérentes avec le code.
- [ ] Note de synthèse de deux pages.
- [ ] Journal IA, avec prompts/usage important, vérification humaine et corrections.
- [ ] Plan de soutenance et script de démo chronométré.

**Porte :** un autre membre peut cloner, lancer, tester et expliquer le projet.

## Phase 8 — Répétition finale
- [ ] Cloner dans un dossier propre ou suivre les instructions depuis zéro.
- [ ] Exécuter toutes les commandes documentées.
- [ ] Répéter la démo sans modifier le code à la volée.
- [ ] Préparer réponses sur les données, les baselines, les limites et le choix des modèles.
- [ ] Terminer par une décision demandée au public.
