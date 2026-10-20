# Question métier, utilisateurs et indicateurs

## Question métier provisoire
Comment aider un utilisateur à repérer les stations-service dont les prix méritent une attention particulière, à comprendre les écarts de profils entre stations et à étudier l'évolution des prix, malgré les données manquantes et les anomalies de collecte ?

## Utilisateurs visés
À confirmer en équipe. Hypothèse de départ : analyste, observateur de marché ou utilisateur souhaitant comparer les prix. Ne pas présumer que l'utilisateur est un consommateur, un gestionnaire de station ou une autorité de contrôle sans validation.

## Décisions que le produit peut soutenir
- choisir les stations à examiner plus en détail ;
- comparer une station à des stations suffisamment comparables ;
- explorer les profils de prix et leur évolution ;
- déterminer si une série est assez complète pour une analyse temporelle.

## Trois fonctions analytiques
### 1. Clustering
But : former des groupes de profils comparables. Les groupes doivent être interprétables par des caractéristiques observées, et non seulement par un numéro de cluster.

Indicateurs possibles à choisir après audit : silhouette si pertinente, stabilité des groupes, taille des groupes, profil médian des prix et couverture de données par groupe.

### 2. Détection d'anomalies
But : détecter des observations atypiques relativement à un référentiel défini (par exemple, même carburant et période, avec comparaison locale si la couverture le permet).

Indicateurs : nombre et taux de signaux, part de signaux examinables, vérification manuelle d'un échantillon, stabilité des alertes aux choix de seuil. Sans étiquettes de vérité terrain, ne pas prétendre calculer une précision/rappel supervisés.

### 3. Séries temporelles
But : décrire les tendances et, si la fréquence et la couverture le permettent, prévoir à horizon explicite.

Évaluation : séparation chronologique, baseline naïve, MAE/RMSE ou autre métrique adaptée, couverture par station/carburant et comparaison avec la baseline. Aucun score avant exécution.

## KPIs métier à rapporter
Ne pas inventer les valeurs ; calculer :
- stations et observations utilisables ;
- couverture temporelle et proportion de trous ;
- stations/carburants couverts par l'analyse ;
- nombre de signaux d'anomalie et exemples explicables ;
- performance de prévision comparée à une baseline, si applicable ;
- temps d'exécution et date de dernière mise à jour ;
- nombre de cas où le produit ne recommande pas de conclusion faute de données.

## Critère de prudence
Une recommandation doit être traçable à une observation et à une règle ou un modèle documenté. Si les données sont insuffisantes, le produit doit afficher « données insuffisantes » plutôt que forcer une réponse.
