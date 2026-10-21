# Plan de soutenance : aide au plein de la flotte (12 min de pitch, 6 min de questions)

Une idée par slide. **Le titre de chaque slide est la conclusion**, pas le sujet. Slides exportées à la main en `docs/soutenance.pdf` par l'équipe.

| # | Titre de slide (= message) | Contenu | Temps |
|---|---|---|---|
| 1 | « Faire le plein tout de suite coûte 1,24 c€/L de plus que le meilleur jour : l'outil ramène ce regret à 0,94 (≈ 380 € par an) » | Client, enjeu, chiffre clé, intervalle de confiance | 1 min |
| 2 | « Plein aujourd'hui ou dans 3 jours : une erreur d'attente coûte 3,25 c€/L, une erreur de plein 1,16 » | Question business, coûts de chaque erreur, décision visée | 1 min |
| 3 | « Le flux officiel ne donne qu'un jour : nous l'avons croisé avec la BCE et complété par l'historique du même producteur » | Les 2 sources imposées, l'ADR-0001, faux « +00:00 », prix anciens de 2009, aucune fuite | 1 min |
| 4 | « Ce matin, 136 des 468 stations de la zone n'ont pas de prix fiable, 27 sont en rupture et 9 fermées » | Ce que le flux apporte au gestionnaire ; carte de l'onglet Exploration | 1 min |
| 5 | « Trois profils de stations, dont 67 stations chères à 7,76 c€/L de plus que la médiane » | Segmentation K-means (non supervisé) | 1 min |
| 6 | « Le taux euro/dollar ne change rien à la décision : −0,03 c€/L, nul aux erreurs près » | Prix seuls contre prix + taux, choix fait en validation croisée avant le test, refus de changer après coup | 1 min 30 |
| 7 | « Le bon seuil n'est pas 0,5 mais 0,26 » | Regret selon le seuil : 1,24 → 1,00 → 0,94 | 1 min |
| 8 | « La station compte plus que le jour : jusqu'à 2 710 € par an si elle est sur la tournée, 66 € avec un détour » | Top-3 net du détour, prix du jour du flux | 1 min |
| 9 | **Démo Streamlit** | Choisir une station : conseil du jour, état (fermée, rupture), stations proches ; puis Exploration et Le modèle | 2 min |
| 10 | « Ce que l'outil ne sait pas faire : le gain du conseil plafonne à environ 1 550 € par an » | Limites : une seule période de test, juillet perdu, plein conseillé 80 % du temps, volumes fictifs | 1 min |
| 11 | « Recommandation : l'utiliser chaque matin pendant 3 mois, en A/B test » | Décision demandée au COMEX, indicateurs de suivi | 30 s |

**Annexes** (non présentées, mais prêtes pour les questions) : hyperparamètres, détail du SQL, résultats de la version précédente avec Brent (abandonnée : hors consigne), saut du 1er janvier.
