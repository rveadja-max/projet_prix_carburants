# Note de synthèse : sans abonnement, le modèle fait gagner 0,34 c€/L (environ 420 € par an), un gain réel mais modeste

**Pour :** gestionnaire de flotte, Livraisons Exemple · **De :** SEP Conseil ([équipe à compléter]) · **Date :** 2026-10-20 · **Document :** livrable de formation, client fictif

## La décision que nous vous demandons

Utiliser le **modèle sans Brent** comme aide à la décision pendant 3 mois sur vos pleins hebdomadaires, et suivre chaque mois le regret moyen observé. Ne prendre un abonnement au cours quotidien du Brent que s'il coûte moins de 310 € par an environ.

## Votre question

Vous faites le plein de 40 utilitaires diesel une fois par semaine, dans le Nord et le Pas-de-Calais. Vous pouvez avancer ou décaler un plein de 3 jours. Aujourd'hui, vous faites le plein tout de suite : sur nos données de test, cela coûte en moyenne 1,24 c€/L de plus que le meilleur des deux jours. Faut-il attendre, et quand ?

## Ce que nous avons trouvé

1. **Les données :** 475 stations, 207 958 lignes station-jour. Beaucoup de stations n'envoient pas de prix tous les jours ; nous reportons le dernier prix sur 7 jours au plus et excluons le reste. Un saut de prix au 1er janvier 2026 n'est pas expliqué.
2. **Les profils** : 3 groupes de stations. Les 67 stations « chères » sont à 7,76 c€/L au-dessus de la médiane de leur département en moyenne.
3. **Le modèle :** sans Brent, le regret moyen passe de 1,24 à 0,90 c€/L sur 55 262 lignes que le modèle n'a jamais vues (du 2026-05-04 au 2026-10-16). Le gain, 0,34 c€/L, est positif mais incertain : intervalle de confiance à 95 % de 0,07 à 0,66 c€/L. Avec le Brent de la veille (flux payant), le regret descend à 0,66.
4. **Le choix de la station :** une station moins chère à moins de 5 km ne rapporte presque rien s'il faut faire un détour (environ 66 € par an, temps du chauffeur compris). Si elle est déjà sur la tournée, le gain peut monter à environ 2 710 € par an. À vérifier avec vos tournées.

## Notre recommandation, chiffrée

| Option | Ce que ça change | Regret moyen (c€/L) | Gain annuel estimé |
|---|---|---|---|
| Ne rien changer (toujours faire le plein tout de suite) | Rien | 1,24 | 0 € |
| Toujours attendre 3 jours | Pire que la situation actuelle | 1,60 | aucun (perte) |
| **Modèle sans Brent (recommandé)** | Un conseil par station et par jour | **0,90** | **environ 420 € par an** (124 800 L), entre 90 et 830 € (IC 95 %) |
| Modèle avec le Brent de la veille | Suppose un abonnement au cours quotidien | 0,66 | environ 730 € par an, soit 310 € de plus que sans Brent |
| Modèle avec le Brent à 8 jours de retard | Pire que sans Brent | 0,93 | gain de 0,31 c€/L sur la situation actuelle, moins que sans Brent |
| Connaître l'avenir (plafond) | Impossible | 0,00 | environ 1 550 € par an au maximum |

**Comment le seuil est fixé :** attendre alors que le prix monte coûte 3,25 c€/L en moyenne ; faire le plein alors que le prix ne monte pas coûte 1,16 c€/L en moyenne. On fait donc le plein dès que la probabilité de hausse dépasse 0,26. Avec un seuil de 0,5, le regret serait de 0,86 c€/L au lieu de 0,66.

## Ce que le modèle ne sait pas faire

- **Le Brent gratuit arrive en retard.** Le 2026-10-20, la dernière valeur datait du 2026-10-14. Avec ce retard, le Brent n'apporte rien (0,93 contre 0,90 c€/L) : c'est pourquoi nous recommandons le modèle sans Brent. Un cours quotidien ajouterait environ 310 € par an.
- **Il conseille « faire le plein » dans 62 % des cas.** Il ne vous fera attendre qu'occasionnellement.
- **Le gain est plafonné.** Même en connaissant l'avenir, on ne gagnerait qu'environ 1 550 € par an avec vos volumes (hypothèses fictives).
- **Le gain dépend de la phase du marché.** Il vient surtout de mai et juin 2026, quand les prix redescendaient. En juillet, quand ils montaient, le modèle a fait un peu pire que « toujours faire le plein ».
- **Une seule période de test**, pendant une crise des prix. Rien ne garantit le même gain en période calme.
- **Gazole seulement**, Nord et Pas-de-Calais, hors autoroute, sans calcul d'itinéraire.

## Ce que nous avons changé après le COMEX

| Retour du COMEX | Ce que nous avons fait |
|---|---|
| à remplir après le J3 | à remplir après le J3 |

## Comment suivre les résultats

| Indicateur | Fréquence | Alerte si | Qui |
|---|---|---|---|
| Regret moyen des pleins du mois, en c€/L (prix payé moins le meilleur des deux prix) | Mensuelle | Il dépasse celui de « toujours faire le plein » sur les mêmes pleins deux mois de suite | Gestionnaire de flotte |
| Disponibilité du cours du Brent de la veille (si abonnement) | Quotidienne | Cours absent ou plus vieux que la veille | Gestionnaire de flotte |

Pour mesurer le vrai gain, nous proposons un **A/B test** : la moitié des véhicules suit le modèle, l'autre moitié fait le plein comme avant, pendant 3 mois.
