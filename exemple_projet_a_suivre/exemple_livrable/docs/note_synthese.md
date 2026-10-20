# Note de synthèse : le score divise par 2,6 le coût des crédits à la consommation

**Pour :** direction des crédits, Banque Exemple · **De :** SEP Conseil · **Document :** exemple de livrable de la formation

## La décision que nous vous demandons

Utiliser le score comme **aide à la décision** pendant 3 mois, sur toutes les nouvelles demandes, et suivre chaque mois le taux de défaut et le nombre de dossiers envoyés en étude.

## Votre question

Aujourd'hui, vous accordez presque toutes les demandes. Or un crédit accordé à un client qui fera défaut coûte **5 fois plus** qu'un bon client refusé. Quelles demandes accorder directement, et lesquelles étudier de plus près ?

## Ce que nous avons trouvé

1. **Les données sont propres, mais anciennes.** 1 000 demandes, 30 % de défauts, aucun doublon. Nous avons retiré le sexe et la nationalité du modèle.
2. **Trois profils d'emprunteurs.** Les « gros crédits longs » (17 % des demandes, 40 mois en moyenne) font défaut **47 fois sur 100**, contre 22 pour les « petits crédits légers ».
3. **Le score bat la situation actuelle.** Sur 250 demandes jamais vues par le modèle, le coût moyen passe de **1,50 à 0,58** par demande.

## Notre recommandation, chiffrée

Sur les 250 demandes du test :

| Option | Défauts accordés | Bons clients envoyés en étude | Coût moyen par demande |
|---|---|---|---|
| Tout accepter (aujourd'hui) | 75 | 0 | 1,50 |
| Score, seuil de 0,5 | 29 | 30 | 0,70 |
| **Score, seuil de 1/6 (recommandé)** | **2** | **135** | **0,58** |

**Pourquoi 1/6 et pas 0,5 ?** Un défaut coûte 5, un bon client refusé coûte 1. Étudier un dossier devient rentable dès que la probabilité de défaut dépasse 1 sur 6.

## Ce que le modèle ne sait pas faire

- **Il envoie beaucoup de dossiers en étude :** 208 sur 250, soit 83 %. C'est rentable avec vos coûts, mais seulement si vos conseillers ont le temps de les étudier. Si ce n'est pas le cas, il faut relever le seuil, et le coût remonte.
- **Les données datent des années 1990, en Allemagne.** Avant tout usage réel, il faut réentraîner le modèle sur vos propres demandes.
- **On ne connaît l'issue que des crédits accordés.** Les clients refusés par le passé manquent dans les données.
- **L'âge reste dans le modèle.** Il faut vérifier que les jeunes ne sont pas écartés plus souvent sans raison.

## Ce que nous avons changé après le COMEX

| Retour du COMEX | Ce que nous avons fait |
|---|---|
| Direction financière : « Combien de dossiers en étude, concrètement ? » | Ajout du nombre de dossiers en étude (208 sur 250) dans cette note et dans les limites |
| Protection des données : « Et l'âge ? » | Ajout de la vérification des refus par tranche d'âge au plan de suivi |
| DSI : « Qui relance l'entraînement ? » | Ajout d'une règle de réentraînement dans la Model Card |

## Comment suivre les résultats

| Indicateur | Fréquence | Alerte si | Qui |
|---|---|---|---|
| Taux de défaut des crédits accordés | Mensuelle | Il s'écarte de plus de 5 points de 30 % | Direction des risques |
| Part des dossiers envoyés en étude | Hebdomadaire | Plus que la capacité des conseillers | Responsable d'agence |
| Taux de refus par tranche d'âge | Trimestrielle | Écart de plus de 10 points entre deux tranches | Protection des données |

Pour mesurer le vrai gain, nous proposons un **A/B test** : la moitié des agences utilise le score, l'autre non, pendant 3 mois.
