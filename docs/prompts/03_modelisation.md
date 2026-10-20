# Prompt 03 — Modèles et évaluation rigoureuse

À partir de la table d'analyse SQL validée, propose trois pistes distinctes : clustering, détection d'anomalies et analyse/prévision temporelle. N'entraîne rien avant d'avoir vérifié le périmètre et les limites des données.

Pour chacune :
1. écris « Votre prédiction » avant l'exécution ;
2. définis l'usage métier ;
3. construis une baseline simple ;
4. justifie variables, transformations, paramètres et critères de sélection ;
5. choisis un protocole d'évaluation adapté ;
6. calcule les métriques à partir des données réelles ;
7. interprète les résultats en termes métier ;
8. consigne les limites et conditions d'abstention.

Clustering : examiner l'interprétabilité, la taille des groupes et la stabilité. Anomalies : expliquer le référentiel de comparaison, les seuils et les faux positifs ; ne pas parler de fraude. Séries temporelles : vérifier la fréquence, les trous et la couverture ; séparer chronologiquement ; comparer à une baseline naïve ; ne pas interpoler silencieusement ni laisser fuiter le futur.

Si les données ne permettent pas une prévision défendable, documente cette conclusion et propose une analyse descriptive plutôt qu'un résultat artificiel. Mets à jour la Model Card. Ne fabrique aucune performance.
