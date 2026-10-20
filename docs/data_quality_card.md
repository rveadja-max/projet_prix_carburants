# Data Quality Card : prix du gazole (Nord et Pas-de-Calais), Brent et euro/dollar

## Identité

| Question | Réponse |
|---|---|
| Unité d'observation | Une station et un jour (table d'analyse) ; à la source, un prix horodaté par station et carburant |
| Source, licence, lien | Prix : prix-carburants.gouv.fr, archives XML annuelles (Licence Ouverte). Brent : EIA série RBRTE via FRED (domaine public). Euro/dollar : BCE. URL dans `backend/config.py` |
| Période et population couvertes | 2025-01-01 → 2026-10-19 (données figées à cette date). Périmètre d'analyse : départements 59 et 62, stations hors autoroute, gazole |
| Taille | Chargement : 14 980 identifiants de stations (2025 et 2026, y compris stations sans gazole), 2 829 198 prix de gazole, 472 cotations Brent, 479 taux euro/dollar, calendrier de 657 jours. Table d'analyse : 475 stations, 207 958 lignes station-jour, du 2025-01-08 au 2026-10-16 |
| Cible | `hausse` = 1 si le prix à J+3 est strictement plus haut que celui de J. Taux de hausse de 0,352 sur la table d'analyse |

## Défauts trouvés et ce qu'on en fait

| Défaut | Combien (chiffre et %) | Comment on l'a vu | Ce qu'on en fait, et pourquoi |
|---|---|---|---|
| Trous de séries | La station médiane (toute la France) n'envoie une mise à jour que 26 % des jours. Dans le périmètre, le prix avant midi (report de 7 jours au plus) n'est connu que pour 54 % des couples station-jour | Profil exploratoire, puis construction de la grille station-jour | Report du dernier prix connu sur 7 jours au plus. Au-delà, ou si le prix à J+3 est inconnu, la ligne est exclue (46 % des couples station-jour du périmètre, d'où les 207 958 lignes restantes) |
| Doublons | Dédoublonnés au chargement (test sur un doublon exact fabriqué) | Test dans `tests/` | Une seule ligne par station et par jour (test de la table d'analyse) |
| Prix aberrants ou impossibles | 0 prix ignoré sur 2 829 198 : tous entre 1,2 et 3,0 €/L | Filtre [0,8 ; 3,5] €/L et date de fin dans le chargement | Le filtre reste en place pour les prochains téléchargements |
| Stations hors périmètre | 14 980 identifiants chargés, 475 stations retenues | Filtre sur le département (59, 62) et le type de zone | Autoroute (`pop` différent de R) et autres départements exclus : ils ne correspondent pas aux tournées de la flotte |
| Saut du 1er janvier 2026 | Médiane nationale : 1,554 → 1,599 €/L entre le 30/12/2025 et le 02/01/2026 | Courbe de la médiane | Gardé tel quel. Cause non vérifiée (fiscalité probable, non confirmée). Pas de variable « fiscalité » inventée |
| Retard de publication du Brent | Le 2026-10-20, dernière valeur au 2026-10-14. Corrélation entre la variation du Brent sur 7 jours et la variation de la pompe à venir : 0,45 avec le Brent de la veille, 0,09 avec 8 jours de retard | Comparaison des dates | Retard réglable (`RETARD_BRENT_JOURS`). Deux scénarios présentés : Brent de la veille et Brent à 8 jours |
| Jours sans cotation (Brent, taux) | Week-ends et jours fériés | Calendrier | Report de la dernière cotation **avant** la date, jamais après |
| `jours_depuis_changement` | Le premier jour observé compte comme un changement | Lecture du code | Valeurs censurées à gauche : à garder en tête pour l'interprétation |
| Classes déséquilibrées | 34,5 % de hausses sur l'entraînement (35,2 % sur l'ensemble de la table d'analyse) | Taux de la cible | Pas de pondération des classes : le seuil issu des coûts exige des probabilités non déformées |

## Les pièges pour le modèle

| Question | Réponse |
|---|---|
| Variables à risque de **fuite** (connues seulement après la décision) | Prix du jour = dernier prix **avant midi** ; Brent et taux de la veille au plus tôt (retard réglable) ; aucune valeur après 2026-10-19. Le prix à J+3 sert uniquement à fabriquer la cible. Un test vérifie que le Brent du jour J n'utilise que des cotations antérieures |
| Variables sensibles | Aucune : données de prix de stations, pas de personnes |
| Biais de sélection | Seuls les couples station-jour dont le prix avant midi est connu (54 %) ont une ligne : les stations qui déclarent rarement leurs prix sont moins présentes |
| Données personnelles | Aucune. Adresses de stations publiques |
| **Changement de source** | La page data.gouv.fr citée dans le cadrage (`.../prix-des-carburants-en-france-flux-quotidien`) renvoie 404. Les archives XML de prix-carburants.gouv.fr sont utilisées à la place. **À faire valider par le formateur** |

## Ce qu'on attend des données

- Les variables qui devraient être les plus utiles : la variation du Brent sur 7 jours, l'écart au prix médian du département, la variation de la médiane départementale.
- Ce que les données ne permettent pas de dire : pourquoi le prix d'une station change ; l'effet de la fiscalité ; ce qui se passe hors du Nord et du Pas-de-Calais ou pour un autre carburant.
