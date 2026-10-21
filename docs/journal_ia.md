# Journal d'usage de l'IA

> Journal de la session du 2026-10-20. Les prompts sont résumés en substance. Le code final est réel : chaque ligne renvoie à un fichier ou à un document de ce dépôt.

**Outils utilisés :** Claude (assistant de code, Claude Code), avec des agents qui écrivent chaque tâche et d'autres qui la relisent.

| # | Fichier ou étape | Le prompt (résumé) | Ce que l'IA a produit | Gardé | Corrigé, et pourquoi | Refusé, et pourquoi |
|---|---|---|---|---|---|---|
| 1 | Cadrage du dépôt | « Respecte exactement `exemple_projet_a_suivre` » | Lecture du cahier des charges et de l'exemple, liste des écarts du dépôt | La liste des écarts | | |
| 2 | Choix du client | (proposé par l'IA) | Un gestionnaire de flotte | Accepté par l'équipe | | |
| 3 | Données complémentaires | « D'autres groupes ont le même sujet ; le professeur propose de croiser avec une base complémentaire » | Brent (EIA via FRED) et euro/dollar (BCE), sources vérifiées | Brent et euro/dollar | | INSEE écarté |
| 4 | Spec, question business (§ 2.1) | « Autocritique ta question business et corrige les biais selon les données » | Mesures sur les données, puis corrections | Toutes les corrections de la spec | Horizon de 7 jours ramené à 3 jours : incohérent avec un plein hebdomadaire (**décision business**) ; retard de publication du Brent mesuré, scénario à 8 jours ajouté (**validation**) ; cible « hausse > 1 c€ » remplacée par « hausse stricte » et formule du seuil corrigée (**correct**) ; plafond de gain affiché ; split temporel adapté à la crise 2026 (**validation**) ; périmètre 59/62 ; règle de report des trous ; saut du 1er janvier signalé | |
| 5 | Relecture de la spec | Relecture par un autre agent | 6 questions | 5 tranchées par l'IA : données figées au 2026-10-19, 4 commandes, prix avant midi et taux de la veille, 2 actions seulement, PDF exportés à la main | | |
| 6 | Modèle de la démo | La relecture pose la question du modèle | | | Tranché par l'équipe : modèle « Brent de la veille » | |
| 7 | Tâches 1 à 8 | Exécution du plan, chaque tâche écrite par un agent et relue par un autre | Code, tests, documents | Chargement en Python comme l'exemple | Test du week-end incapable d'échouer (**tests**) ; 5 variables sans test de valeur (**tests**) ; station à une ligne qui faisait planter la segmentation (**robustesse**) ; validation croisée sans purge, qui donnait 0,674 / 0,696 / 0,651 (**fuite de données**, corrigée par des plis en jours entiers avec purge de 3 jours) | `class_weight="balanced"` retiré : le seuil issu des coûts exige des probabilités non déformées (**décision business**) |
| 8 | Analyse critique (2026-10-21) | « Analyse la question business comme un ingénieur des données publiques, trouve les goulots et une stratégie problème-solution » | 4 goulots mesurés sur les vraies données : gain en titre non déployable (Brent payant), dépendance à la phase du marché, probabilités mal calibrées, levier « choix de la station » absent | Les 4 chantiers ci-dessous | L'IA annonçait ~3 500 €/an pour le choix de la station sans compter le détour : faux, voir ligne 9 (**décision business**) | |
| 9 | Choix de la station | « Fais les 4 dans l'ordre » | Top-3 des stations à moins de 5 km, gain net du détour (carburant + chauffeur) ; coordonnées chargées | Le top-N et ses deux scénarios | 6 stations aux coordonnées inversées ou absentes dans les archives (**robustesse**) ; avec le détour, le gain tombe à ~66 €/an, ~2 710 € seulement si la station est sur la tournée (**décision business**) | |
| 10 | Modèle sans Brent en titre | idem | Intervalle de confiance par bootstrap, valeur d'un Brent quotidien | Tout | Bootstrap par jours remplacé par un bootstrap par semaines : les jours proches sont corrélés, l'intervalle par jours était trop étroit (**validation**) | |
| 11 | Regret par mois | idem | Tableau mensuel | Tout | | |
| 12 | Calibration | idem | Calibration isotonique sur les plis temporels | Le diagnostic (score de Brier) | | Calibration refusée : pire sur la validation de l'entraînement (regret 0,638 → 0,888 avec Brent). Décidé sur l'entraînement, pas sur le test (**fuite de données** évitée : choisir sur le test) |
| 13 | Nouvelle consigne : flux quotidien data.gouv.fr + BCE | Refaire la base avec le lien imposé et le taux BCE, corriger les erreurs | Analyse du flux (photo de la veille, sans historique), ADR-0001, nouveau schéma SQL (`schema.sql`), référentiel du flux (fermetures, ruptures, coordonnées), conseil du jour, 2 modèles prix seuls / prix + taux, choix en validation croisée, onglets Décision / Exploration / Le modèle | Tout | Suffixe « +00:00 » du flux reconnu comme faux en comparant aux archives (**fuite de données** évitée : décalage de 2 h sur « prix connu avant midi ») ; prix du flux datant de 2009 qui faisaient remonter le calendrier, trouvé par le diagnostic qualité et corrigé avec un test (**validation**) | Changer de modèle après avoir vu que « prix seuls » fait mieux sur le test : refusé (**fuite de données** : choisir sur le test) |

## Les catégories de la checklist du TD 4

correct · fuite de données · validation · décision business · robustesse · sécurité et RGPD · reproductibilité · dépendances · tests · lisibilité

## Bilan en 3 lignes

- **Ce que l'IA nous a fait gagner :** la mesure des données avant de figer la question (horizon, retard du Brent, plafond de gain), et le squelette du pipeline et des tests.
- **L'erreur qui nous aurait coûté le plus cher :** la validation croisée sans purge, qui donnait des scores trop bons parce que des jours voisins se retrouvaient de part et d'autre d'un pli.
- **Ce que nous ne lui confierions pas sans relecture :** le choix de la question, de la cible et du seuil, et l'écriture des limites. L'équipe doit relire elle-même tous les chiffres du README, les textes de la soutenance et les limites.
