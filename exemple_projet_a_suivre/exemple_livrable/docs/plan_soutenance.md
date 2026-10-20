# Plan de soutenance : exemple (12 min de pitch, 6 min de questions)

Une idée par slide. **Le titre de chaque slide est la conclusion**, pas le sujet.

| # | Titre de slide (= message) | Contenu | Temps |
|---|---|---|---|
| 1 | « Accepter tous les crédits coûte 1,50 par demande : on peut diviser ce coût par 2,6 » | Client, enjeu, chiffre clé | 1 min |
| 2 | « Un défaut coûte 5 fois plus qu'un bon client refusé » | Question business, matrice de coûts, décision visée | 1 min |
| 3 | « 1 000 demandes, 30 % de défauts, aucune fuite » | Data Quality Card en 4 points ; ce qu'on a exclu et pourquoi | 1 min 30 |
| 4 | « Trois profils d'emprunteurs, dont un à 47 % de défaut » | Segmentation K-means : 3 personas (non supervisé) | 1 min 30 |
| 5 | « La forêt aléatoire bat la baseline, et reste stable en validation croisée » | Baseline, puis RF ; ROC-AUC et écart-type de la CV | 1 min 30 |
| 6 | « Le bon seuil n'est pas 0,5 mais 1/6 » | Coût moyen selon le seuil : 1,50 → 0,70 → 0,58 | 1 min 30 |
| 7 | « Le compte courant explique l'essentiel du risque » | Importance par permutation ; ce que le métier en fait | 1 min |
| 8 | **Démo Streamlit** | Scorer une demande, faire varier le montant, voir la décision changer | 2 min |
| 9 | « Ce que le modèle ne sait pas faire » | Limites, équité (âge), biais de sélection | 1 min |
| 10 | « Recommandation : l'utiliser comme aide à la décision pendant 3 mois » | Décision demandée au COMEX, prochaines étapes, indicateurs de suivi | 30 s |

**Annexes** (non présentées, mais prêtes pour les questions) : matrice de confusion, hyperparamètres, détail du SQL.
