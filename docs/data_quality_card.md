# Data Quality Card : prix du gazole (Nord et Pas-de-Calais) et euro/dollar BCE

## Identité

| Question | Réponse |
|---|---|
| Unité d'observation | Une station et un jour (table d'analyse) ; à la source, un prix horodaté par station et carburant |
| Source, licence, lien | **Flux quotidien** data.gouv.fr, ressource `336c34b5-a527-4c35-b84d-18462daa7c51` (Licence Ouverte) : référentiel des stations, coordonnées, fermetures, ruptures, dernier prix (photo de la veille, sans historique). **Euro/dollar** : BCE, taux de référence quotidien. **Historique des prix** : archives XML annuelles du même producteur (donnees.roulez-eco.fr). URL dans `backend/config.py`, choix dans `docs/adr/0001-sources-flux-quotidien-et-bce.md` |
| Période et population couvertes | Historique 2025-01-01 → veille du jour du conseil ; métriques figées au 2026-10-19. Flux du 2026-10-21 (prix jusqu'au 2026-10-20). Périmètre : départements 59 et 62, stations hors autoroute, gazole |
| Taille | Flux : 75 746 lignes, 9 946 stations (468 dans le périmètre). Archives : 14 980 identifiants de stations (716 dans le périmètre), 2 832 430 prix de gazole (archives + flux, dédoublonnés), 480 taux euro/dollar. Table d'analyse : 475 stations, 207 958 lignes station-jour, du 2025-01-08 au 2026-10-16 |
| Cible | `hausse` = 1 si le prix à J+3 est strictement plus haut que celui de J. Taux de hausse de 0,352 sur la table d'analyse |

## Défauts trouvés et ce qu'on en fait

| Défaut | Combien (chiffre et %) | Comment on l'a vu | Ce qu'on en fait, et pourquoi |
|---|---|---|---|
| Trous de séries | La station médiane (toute la France) n'envoie une mise à jour que 26 % des jours. Dans le périmètre, le prix avant midi (report de 7 jours au plus) n'est connu que pour 54 % des couples station-jour | Profil exploratoire, puis construction de la grille station-jour | Report du dernier prix connu sur 7 jours au plus. Au-delà, ou si le prix à J+3 est inconnu, la ligne est exclue (46 % des couples station-jour du périmètre, d'où les 207 958 lignes restantes) |
| Doublons | Dédoublonnés au chargement (test sur un doublon exact fabriqué) | Test dans `tests/` | Une seule ligne par station et par jour (test de la table d'analyse) |
| Prix aberrants ou impossibles | 0 prix ignoré sur 2 829 198 : tous entre 1,2 et 3,0 €/L | Filtre [0,8 ; 3,5] €/L et date de fin dans le chargement | Le filtre reste en place pour les prochains téléchargements |
| Stations hors périmètre | 14 980 identifiants chargés, 475 stations retenues | Filtre sur le département (59, 62) et le type de zone | Autoroute (`pop` différent de R) et autres départements exclus : ils ne correspondent pas aux tournées de la flotte |
| Saut du 1er janvier 2026 | Médiane nationale : 1,554 → 1,599 €/L entre le 30/12/2025 et le 02/01/2026 | Courbe de la médiane | Gardé tel quel. Cause non vérifiée (fiscalité probable, non confirmée). Pas de variable « fiscalité » inventée |
| Flux : lignes répétées | Une ligne par station, carburant **et rupture** : 75 746 lignes pour 9 946 stations | Comptage par identifiant | Ramené à une ligne par station au chargement (test sur une station à deux lignes) |
| Flux : faux fuseau horaire | Les dates portent « +00:00 » mais sont en heure locale : les mêmes prix ont la même heure dans les archives (vérifié sur 6 stations) | Comparaison flux / archives | Suffixe retiré (`heure_locale`). Sans cela, la règle « prix connu avant midi » serait décalée de 2 heures |
| Flux : prix très anciens | Des « derniers prix » datent de 2009. Dans le périmètre, 91 stations ont un prix de plus de 7 jours et 45 n'ont pas de prix de gazole | Âge du prix au jour du conseil | Gardés dans le référentiel mais jamais proposés comme alternative ; un prix antérieur aux archives n'entre pas dans l'historique (sinon le calendrier remontait à 2009 : bug trouvé et corrigé, test dédié) |
| Flux : stations fermées ou en rupture | Dans le périmètre, le 2026-10-21 : 9 stations fermées, 27 en rupture de gazole | Champs `fermeture` (JSON, temporaire ou définitive) et `Carburant en rupture` | Jamais proposées comme alternative ; signalées dans l'écran Décision |
| Stations disparues | 248 des 716 stations du périmètre dans les archives sont absentes du flux du jour | Jointure archives / flux | Gardées pour l'apprentissage (passé réel), exclues du conseil du jour |
| Jours sans cotation (taux) | Week-ends et jours fériés | Calendrier | Report de la dernière cotation **avant** la date, jamais après |
| Coordonnées des stations | Archives : inversions latitude/longitude et positions absentes (3 + 3 stations dans le périmètre). Flux : toutes dans les bornes du Nord et du Pas-de-Calais, 1 sans position | Contrôle des bornes | Coordonnées prises dans le flux seulement ; sans position : pas d'alternative proposée |
| `jours_depuis_changement` | Le premier jour observé compte comme un changement | Lecture du code | Valeurs censurées à gauche : à garder en tête pour l'interprétation |
| Classes déséquilibrées | 34,5 % de hausses sur l'entraînement (35,2 % sur l'ensemble de la table d'analyse) | Taux de la cible | Pas de pondération des classes : le seuil issu des coûts exige des probabilités non déformées |

## Les pièges pour le modèle

| Question | Réponse |
|---|---|
| Variables à risque de **fuite** (connues seulement après la décision) | Prix du jour = dernier prix **avant midi** ; taux BCE de la veille au plus tôt (fixé à 14 h 15) ; métriques limitées aux jours dont le prix à J+3 est connu au 2026-10-19. Le prix à J+3 sert uniquement à fabriquer la cible. Des tests vérifient que le taux du jour J n'utilise que des cotations antérieures. Le choix du modèle se fait en validation croisée sur l'entraînement, jamais sur le test |
| Variables sensibles | Aucune : données de prix de stations, pas de personnes |
| Biais de sélection | Seuls les couples station-jour dont le prix avant midi est connu (54 %) ont une ligne : les stations qui déclarent rarement leurs prix sont moins présentes |
| Données personnelles | Aucune. Adresses de stations publiques |
| **Changement de source** | Le professeur impose le flux quotidien data.gouv.fr (lien stable) et la BCE. Le flux n'a pas d'historique : les archives du même producteur complètent l'historique. **À faire valider par le professeur** (ADR-0001) |

## Ce qu'on attend des données

- Les variables qui se sont révélées les plus utiles : la variation de la médiane départementale sur 7 jours et l'écart au prix médian du département. Le taux BCE arrive ensuite, sans améliorer la décision.
- Ce que les données ne permettent pas de dire : pourquoi le prix d'une station change ; l'effet de la fiscalité ; ce qui se passe hors du Nord et du Pas-de-Calais ou pour un autre carburant.
