# Plan de qualité et de tests

## Données
- [ ] Le fichier source est conservé sans modification.
- [ ] Format réel et encodage vérifiés.
- [ ] Les dates et fuseaux éventuels sont interprétés explicitement.
- [ ] Les identifiants et clés de jointure sont documentés.
- [ ] Les doublons sont quantifiés et leur traitement justifié.
- [ ] Les prix nuls, négatifs, extrêmes et unités inattendues sont examinés.
- [ ] Les trous de séries sont quantifiés par station et carburant.
- [ ] Les raisons de l'absence ne sont pas inventées.
- [ ] Les jointures SQL contrôlent cardinalité et perte de lignes.
- [ ] La reconstruction de la table analytique est reproductible.

## Modèles
- [ ] Baseline documentée.
- [ ] Fuite de données recherchée.
- [ ] Séparation temporelle utilisée pour la prévision.
- [ ] Variables et transformations sauvegardées/documentées.
- [ ] Seuils et hyperparamètres tracés.
- [ ] Métriques calculées par code et reproductibles.
- [ ] Échantillon de signaux d'anomalie examiné.
- [ ] Résultats présentés avec leur périmètre et leurs limites.
- [ ] Pas de conclusion causale ou de fraude tirée d'une anomalie seule.

## Logiciel
- [ ] Backend importable sans Streamlit.
- [ ] Frontend importe uniquement `backend.service`.
- [ ] Tests unitaires pour parsing, validation, features et modèles.
- [ ] Tests d'intégration du pipeline SQL.
- [ ] Cas limites : fichier vide, XML invalide, CSV avec colonnes manquantes, doublons, séries trop courtes.
- [ ] Service gère les données insuffisantes.
- [ ] Smoke test de l'application Streamlit.
- [ ] Instructions d'installation testées depuis un environnement propre.

## Présentation
- [ ] Une décision métier est visible en premier.
- [ ] Une recommandation est accompagnée d'une explication.
- [ ] Les limites sont affichées sans attendre les questions.
- [ ] Les chiffres du diaporama correspondent aux résultats générés.
- [ ] La démonstration peut être rejouée à partir d'un cas préparé.
