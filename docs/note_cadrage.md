# Note de cadrage : aide au plein de la flotte (gazole)

**Équipe :** [à compléter par l'équipe] · **Dataset :** prix des carburants en France (prix-carburants.gouv.fr), croisé avec le cours du Brent (EIA via FRED) et le taux euro/dollar (BCE) · **Client imaginé :** Livraisons Exemple (PME, Nord), 40 utilitaires diesel ; le gestionnaire de flotte décide

## 1. La question business, en 2 lignes

Pour une station donnée, faut-il faire le plein de la flotte aujourd'hui ou attendre 3 jours ? Combien la flotte économise-t-elle en suivant le modèle ?

## 2. Les 5 questions du cours 1

| Question | Votre réponse |
|---|---|
| Qu'appelle-t-on exactement la cible ? | Une hausse = le prix du gazole à J+3 est strictement plus haut que celui de J, dans la même station. Prix du jour = dernier prix enregistré avant midi. |
| Que fera le client du résultat ? | Le gestionnaire fait le plein tout de suite (hausse probable) ou attend 3 jours. |
| Combien de cas peut-il traiter ? | Un plein par semaine et par véhicule, 40 véhicules : la capacité n'est pas la contrainte. |
| Combien coûte une erreur, combien rapporte une bonne décision ? | Attendre alors que le prix monte coûte en moyenne 3,25 c€/L. Faire le plein alors que le prix ne monte pas coûte en moyenne 1,16 c€/L (mesurés sur l'entraînement, zéros compris). |
| Quelles données, depuis quand, et qui les connaît ? | Archives XML 2025 et 2026 de prix-carburants.gouv.fr, 475 stations du Nord et du Pas-de-Calais, du 2025-01-08 au 2026-10-16. Brent et euro/dollar quotidiens. Données figées au 2026-10-19. |

## 3. Les familles de méthodes prévues

| Famille (carte du data mining) | Pour répondre à quelle question du client ? |
|---|---|
| Supervisé : classification (forêt aléatoire) | Le prix va-t-il monter dans les 3 jours ? |
| Non supervisé : clustering (K-means) | Quels profils de stations ? (prix relatif, changements par semaine, volatilité) |
| Bonus | Aucun |

## 4. Comment saura-t-on que ça marche ?

- **Baseline** (ce qu'on fait sans modèle) : toujours faire le plein tout de suite, regret moyen de 1,24 c€/L sur le test.
- **Métrique qui compte pour le client** : le regret moyen en c€/L (prix payé moins le meilleur des deux prix), pas l'accuracy.
- **Succès** : le modèle avec Brent (veille) et seuil issu des coûts est plus bas que la situation actuelle, et plus bas que le modèle sans Brent. Sinon, on l'écrit dans les limites.

## 5. Les risques déjà vus

- Le Brent gratuit arrive avec du retard (8 jours le 2026-10-20) : un scénario réaliste est présenté à côté du scénario principal.
- Le gain maximal est faible (plafond de 1,24 c€/L) ; le prix ne bouge pas dans la majorité des cas.
- Crise de prix en 2026 : une seule période de test, changement de régime possible.
- Trous dans les séries de prix : report du dernier prix sur 7 jours au plus, au-delà la ligne est exclue.
- Saut inexpliqué au 1er janvier 2026.
- Source : la page data.gouv.fr citée dans le cadrage renvoie 404 ; changement de source à faire valider par le formateur.

## 6. Qui fait quoi

| Membre | Rôle principal (SQL et données, modèle, application, documents et soutenance) |
|---|---|
| [à compléter par l'équipe] | [à compléter par l'équipe] |
