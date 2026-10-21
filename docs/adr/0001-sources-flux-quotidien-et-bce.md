# ADR-0001 : Sources : flux quotidien data.gouv.fr et taux BCE, historique par les archives, Brent retiré

**Date** : 2026-10-21
**Statut** : proposé (à valider par l'équipe et le professeur)
**Décideurs** : équipe projet, avec l'assistant IA (journal IA, ligne 13)

## Contexte

Le professeur demande d'utiliser le lien stable du flux quotidien sur data.gouv.fr (ressource `336c34b5-a527-4c35-b84d-18462daa7c51`) au lieu de la page prix-carburants.gouv.fr, et de le croiser avec le taux EUR/USD de la BCE. Vérifié le 2026-10-21 :
- le flux est une **photo de la veille** : dernier prix connu par station et carburant, avec les fermetures et les ruptures ;
- il n'a **aucun historique**, et data.gouv.fr ne publie aucun historique national officiel ;
- la question business (faire le plein aujourd'hui ou dans 3 jours) exige pourtant un historique, et le croisement avec un taux quotidien aussi.

## Décision

- **Flux quotidien (lien du professeur)** : il devient le référentiel du réseau (stations, coordonnées, services, fermetures, ruptures) et la source du prix du jour. Son dernier prix complète l'historique.
- **Historique d'apprentissage** : il vient des archives annuelles du même producteur (donnees.roulez-eco.fr), que la page data.gouv.fr cite comme source du flux.
- **BCE** : elle est la seule source de marché.
- **Brent (FRED)** : il est retiré, car la consigne ne le cite pas.

## Alternatives envisagées

### Flux seul + BCE
- **Pour** : respect littéral de la consigne.
- **Contre** : un seul jour de prix, donc pas de modèle de prévision ni de validation temporelle. Le croisement avec la BCE se réduit à un seul taux.
- **Pourquoi pas** : le cahier des charges demande une méthode supervisée validée dans le temps.

### Collecter le flux chaque jour à partir d'aujourd'hui
- **Pour** : une seule source de prix.
- **Contre** : aucun historique avant des semaines de collecte.
- **Pourquoi pas** : rien d'entraînable avant la soutenance. Cette collecte reste l'évolution naturelle en production.

### Garder le Brent en plus
- **Pour** : le Brent de la veille apportait environ 310 €/an, d'après le modèle précédent.
- **Contre** : c'est une troisième source, hors consigne. Le Brent gratuit (FRED) a environ 8 jours de retard, et avec ce retard il n'apportait rien.
- **Pourquoi pas** : la consigne nomme deux sources.

## Conséquences

### Positives
- Le conseil se fait **pour aujourd'hui** (jour du conseil = lendemain du flux), et non plus seulement en rejouant le passé.
- Une station fermée ou en rupture de gazole n'est jamais proposée. Les stations proches sont comparées sur leurs prix du jour réels.
- Les coordonnées viennent du flux, qui est propre. Les archives contenaient des inversions et des trous de coordonnées : ces défauts disparaissent.
- Le croisement avec la BCE est mesuré : modèle « prix seuls » contre « prix + taux BCE », avec un intervalle de confiance.

### Négatives
- L'historique dépend encore du domaine donnees.roulez-eco.fr, que le professeur juge moins stable.
- Le gain du Brent de la veille est perdu (environ 310 €/an d'après le modèle précédent, avec un flux payant).

### Risques
- **Le flux change chaque jour.** Les métriques sont donc figées par `DATE_FIN_DONNEES`, et seul le conseil du jour bouge.
- **Les horodatages du flux portent un faux « +00:00 »** : ils sont en heure locale, comme les archives (vérifié station par station). Ce suffixe est retiré au chargement.
