# Plan de soutenance : aide au plein de la flotte (12 min de pitch, 6 min de questions)

Une idée par slide. **Le titre de chaque slide est la conclusion**, pas le sujet. Slides exportées à la main en `docs/soutenance.pdf` par l'équipe.

| # | Titre de slide (= message) | Contenu | Temps |
|---|---|---|---|
| 1 | « Faire le plein tout de suite coûte 1,24 c€/L de plus que le meilleur jour : le modèle ramène ce regret à 0,66 » | Client, enjeu, chiffre clé | 1 min |
| 2 | « Plein aujourd'hui ou dans 3 jours : une erreur d'attente coûte 3,25 c€/L, une erreur de plein 1,16 » | Question business, coûts de chaque erreur, décision visée | 1 min |
| 3 | « 475 stations du Nord et du Pas-de-Calais, 207 958 lignes, et un Brent qui arrive avec 8 jours de retard » | Data Quality Card en 4 points : trous de séries, saut du 1er janvier, retard du Brent, aucune fuite | 1 min 30 |
| 4 | « Trois profils de stations, dont 67 stations chères à 7,76 c€/L de plus que la médiane » | Segmentation K-means : 3 profils (non supervisé) | 1 min 30 |
| 5 | « Le Brent de la veille améliore le modèle (ROC-AUC 0,70) ; avec 8 jours de retard, il fait pire que sans » | Baseline, puis les 3 modèles ; ROC-AUC et écart-type de la validation croisée | 1 min 30 |
| 6 | « Le bon seuil n'est pas 0,5 mais 0,26 » | Regret selon le seuil : 1,24 → 0,86 → 0,66 | 1 min 30 |
| 7 | « La variation du Brent sur 7 jours est la variable la plus utile » | Importance par permutation ; ce que le métier en fait | 1 min |
| 8 | **Démo Streamlit** | Choisir une station et un jour, lire la probabilité de hausse et la recommandation | 2 min |
| 9 | « Ce que le modèle ne sait pas faire : le gain plafonne à environ 1 550 € par an » | Limites : plafond, une seule période de test, plein conseillé 62 % du temps, volumes fictifs | 1 min |
| 10 | « Recommandation : l'utiliser comme aide à la décision pendant 3 mois, avec un Brent quotidien » | Décision demandée au COMEX, A/B test, indicateurs de suivi | 30 s |

**Annexes** (non présentées, mais prêtes pour les questions) : hyperparamètres, détail du SQL, scénario Brent à 8 jours, saut du 1er janvier.
