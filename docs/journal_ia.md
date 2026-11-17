# Journal d'usage de l'IA

| | |
|---|---|
| **Projet** | SEP Conseil et Livraisons Exemple : aide au plein de la flotte (prix des carburants, Nord et Pas-de-Calais) |
| **Cadre** | Projet universitaire de data mining, livrable N3 (critère 4 de la grille) |
| **Équipe** | [à compléter par l'équipe] |
| **Rédacteur du journal** | [à compléter] |
| **Période couverte** | du 2026-10-20 au 2026-11-15 |
| **Version du journal** | 2.0 du 2026-11-15 (voir § 10) |
| **Dépôt** | branche de travail `plein-flotte` |

> **Déclaration.** Le professeur a demandé d'utiliser l'IA pour ce projet. Ce journal dit, pour chaque usage important, ce qui a été demandé, ce que l'IA a produit, ce que l'équipe a gardé, corrigé ou refusé, et pourquoi. Les prompts sont **résumés en substance** : leur texte exact n'a pas été archivé. Les résultats, en revanche, sont vérifiables. Chaque ligne renvoie à un fichier, à un document ou à un commit de ce dépôt.

## Sommaire

1. Outils utilisés
2. Règles d'usage fixées avant de commencer
3. Méthode de contrôle des productions de l'IA
4. Journal des usages (tableau imposé par le modèle du cours)
5. Détail chronologique
6. Registre des corrections par catégorie (checklist du TD 4)
7. Ce qui n'a pas été confié à l'IA
8. Données, confidentialité et sécurité
9. Limites de ce journal
10. Historique des versions
11. Bilan en 3 lignes

---

## 1. Outils utilisés

| Outil | Version | Usage | Preuve |
|---|---|---|---|
| Claude Code (assistant de code en ligne de commande, Anthropic) | modèle Claude Opus 5.5 | Lecture du dépôt, mesures sur les données, écriture du code, des tests et des documents, relecture | Mention `Co-Authored-By: Claude Opus 5.5` dans les 20 commits hors fusions de `plein-flotte` (`git log`) |
| Agents secondaires de Claude Code | même modèle | Un agent écrit une tâche du plan, un autre la relit avant validation | Plan `docs/superpowers/plans/2026-10-20-plein-flotte.md`, rubrique « Review Focus » |
| Skills (fiches d'instructions chargées par l'assistant) | voir commits | Règles de code (`karpathy-guidelines`), SQL (`sql-database-assistant`), décisions d'architecture (`architecture-decision-records`), README (`crafting-effective-readmes`), Streamlit (`developing-with-streamlit`) | Commits `675cf1c` et `b8074bc` ; retirés du dépôt public ensuite (`3204de7`) |
| Prompts de travail préparés | — | 6 prompts types, de l'audit initial à la revue finale | `docs/prompts/00_audit_initial.md` à `05_revue_finale.md` |

Aucun autre outil d'IA (chat en ligne, générateur d'images, traduction automatique) n'est déclaré pour ce projet. [L'équipe complète cette phrase si un membre en a utilisé un.]

## 2. Règles d'usage fixées avant de commencer

Ces règles sont écrites dans le fichier d'instructions de l'assistant (`CLAUDE.md`, gardé en local) et dans les prompts de `docs/prompts/`. Elles s'appliquent à toute production de l'IA.

1. **Aucun chiffre inventé.** Toute métrique est recalculée par le pipeline sur les vraies données, avec son périmètre. Les chiffres exploratoires de la spec sont marqués « seront recalculés par le pipeline ».
2. **Aucune URL inventée.** Seules les URL lues sur une page officielle sont utilisées (ADR-0001).
3. **Hiérarchie des sources.** Le cahier des charges du formateur prime sur les propositions de l'IA. L'exemple German Credit sert pour la forme, jamais pour le fond.
4. **Décisions réservées à l'équipe.** Question business, choix du modèle de la démo, limites présentées : l'IA propose, l'équipe tranche (§ 7).
5. **Statut de chaque résultat.** L'IA distingue « implémenté », « testé », « testé partiellement » et « non vérifié ». Elle ne déclare pas une tâche terminée sans avoir lancé les tests.
6. **Données brutes intouchables.** Pas de modification des fichiers de `data/raw/`, pas de suppression sans accord.
7. **Git encadré.** Une branche par modification (`feat/…`, `fix/…`, `docs/…`, `chore/…`), fusionnée dans `plein-flotte`, jamais dans `main`.
8. **Skills relus avant installation.** Chaque skill est lu en entier, scripts compris, avant d'être installé (message du commit `675cf1c`).

## 3. Méthode de contrôle des productions de l'IA

Chaque production passe par au moins un de ces contrôles avant d'être gardée.

| Contrôle | Ce qu'il attrape | Exemple dans ce projet |
|---|---|---|
| Relecture par un second agent | Erreurs de logique, tests faibles, écarts au plan | Test du week-end incapable d'échouer (ligne 7 du § 4) |
| Tests automatiques (`python -m pytest`, 78 tests au 2026-11-15) | Régressions, variables mal calculées | Variables calculées à la main dans les tests de la table d'analyse (commit `66598c3`) |
| Mesure sur les données réelles | Hypothèses fausses | Horizon de 7 jours incohérent, Brent publié avec 8 jours de retard (spec § 2.1) |
| Comparaison entre sources | Erreurs de format | Suffixe « +00:00 » du flux comparé aux archives (ligne 13) |
| Règle « on choisit sur l'entraînement, jamais sur le test » | Fuite de données par sélection | Calibration et changement de modèle refusés (lignes 12 et 13) |
| Relecture par l'équipe | Décisions métier, formulation des limites | Choix du modèle de la démo (ligne 6) |

## 4. Journal des usages

Format imposé par le modèle du cours (`modeles/journal_ia.md`). Les catégories en gras sont celles de la checklist du TD 4.

| # | Date | Fichier ou étape | Le prompt (résumé) | Ce que l'IA a produit | Gardé | Corrigé, et pourquoi | Refusé, et pourquoi |
|---|---|---|---|---|---|---|---|
| 1 | 2026-10-20 | Cadrage du dépôt | « Respecte exactement `exemple_projet_a_suivre` » | Lecture du cahier des charges et de l'exemple, liste des écarts du dépôt (spec § 10) | La liste des écarts | | Supprimer les dossiers absents de l'exemple sans accord : refusé, laissé à l'équipe (spec § 10) |
| 2 | 2026-10-20 | Choix du client | (proposé par l'IA) | Un gestionnaire de flotte de PME | Accepté par l'équipe | | |
| 3 | 2026-10-20 | Données complémentaires | « D'autres groupes ont le même sujet ; le professeur propose de croiser avec une base complémentaire » | Brent (EIA via FRED) et euro/dollar (BCE), sources vérifiées | Brent et euro/dollar | | INSEE écarté. Le Brent sera retiré le 2026-10-21 (ligne 13) |
| 4 | 2026-10-20 | Spec, question business (§ 2.1) | « Autocritique ta question business et corrige les biais selon les données » | 9 problèmes mesurés sur les archives 2025-2026 (10 203 stations, 2,83 M relevés), avec une correction chacun | Toutes les corrections | Horizon de 7 jours ramené à 3 jours : incohérent avec un plein hebdomadaire (**décision business**) ; retard de publication du Brent mesuré, scénario à 8 jours ajouté (**validation**) ; cible « hausse > 1 c€ » remplacée par « hausse stricte » et formule du seuil corrigée (**correct**) ; plafond de gain affiché ; split temporel adapté à la crise 2026 (**validation**) ; périmètre 59/62 ; règle de report des trous ; saut du 1er janvier signalé sans cause inventée | |
| 5 | 2026-10-20 | Relecture de la spec | Relecture par un autre agent | 6 questions ouvertes | 5 tranchées par l'IA et écrites comme « à vérifier par l'équipe » (spec § 10 bis) : données figées au 2026-10-19, 4 commandes, prix avant midi et taux de la veille, 2 actions seulement, PDF exportés à la main | | |
| 6 | 2026-10-20 | Modèle de la démo | La relecture pose la question du modèle | Options présentées | | Tranché par l'équipe : modèle « Brent de la veille ». Décision remplacée le 2026-10-21 (lignes 10 et 13) | |
| 7 | 2026-10-20 | Tâches 1 à 8 du plan | Exécution du plan, chaque tâche écrite par un agent et relue par un autre | Code, tests, documents (commits `8a4ebe2` à `64388bf`) | Chargement en Python, comme l'exemple | Test du week-end incapable d'échouer (**tests**) ; 5 variables sans test de valeur (**tests**) ; station à une seule ligne qui faisait planter la segmentation (**robustesse**) ; validation croisée sans purge, qui donnait 0,674 / 0,696 / 0,651 (**fuite de données**, corrigée par des plis en jours entiers avec purge de 3 jours, commit `a27a2cb`) | `class_weight="balanced"` retiré : le seuil issu des coûts exige des probabilités non déformées (**décision business**, commit `067db64`) |
| 8 | 2026-10-21 | Analyse critique | « Analyse la question business comme un ingénieur des données publiques, trouve les goulots et une stratégie problème-solution » | 4 goulots mesurés : gain en titre non déployable (Brent payant), dépendance à la phase du marché, probabilités mal calibrées, levier « choix de la station » absent | Les 4 chantiers (lignes 9 à 12) | L'IA annonçait environ 3 500 €/an pour le choix de la station sans compter le détour : faux, voir ligne 9 (**décision business**) | |
| 9 | 2026-10-21 | Choix de la station | « Fais les 4 dans l'ordre » | Top-3 des stations à moins de 5 km, gain net du détour (carburant + chauffeur) ; coordonnées chargées (commit `3a1ec28`) | Le top-N et ses deux scénarios | 6 stations aux coordonnées inversées ou absentes dans les archives (**robustesse**) ; avec le détour, le gain tombe à environ 66 €/an, et 2 710 € seulement si la station est déjà sur la tournée (**décision business**) | |
| 10 | 2026-10-21 | Modèle sans Brent en titre | idem | Intervalle de confiance par bootstrap, valeur d'un Brent quotidien (commit `5b245d8`) | Tout | Bootstrap par jours remplacé par un bootstrap par semaines : les jours proches sont corrélés, l'intervalle par jours était trop étroit (**validation**) | |
| 11 | 2026-10-21 | Regret par mois | idem | Tableau mensuel du regret (commit `3550b70`) | Tout | | |
| 12 | 2026-10-21 | Calibration | idem | Calibration isotonique sur les plis temporels (commit `76c9f9d`) | Le diagnostic (score de Brier) | | Calibration refusée : pire sur la validation de l'entraînement (regret 0,638 → 0,888 avec Brent). Décidé sur l'entraînement, pas sur le test (**fuite de données** évitée) |
| 13 | 2026-10-21 | Nouvelle consigne : flux quotidien data.gouv.fr + BCE | Refaire la base avec le lien imposé et le taux BCE, corriger les erreurs | Analyse du flux (photo de la veille, sans historique), ADR-0001, nouveau schéma SQL (`schema.sql`), référentiel du flux (fermetures, ruptures, coordonnées), conseil du jour, 2 modèles prix seuls / prix + taux, choix en validation croisée, onglets Décision / Exploration / Le modèle (commits `d7dc815`, `7e5017a`) | Tout | Suffixe « +00:00 » du flux reconnu comme faux en comparant aux archives (**fuite de données** évitée : décalage de 2 h sur « prix connu avant midi ») ; prix du flux datant de 2009 qui faisaient remonter le calendrier, trouvés par le diagnostic qualité et corrigés avec un test (**validation**) | Changer de modèle après avoir vu que « prix seuls » fait mieux sur le test : refusé (**fuite de données** : choisir sur le test) |
| 14 | 2026-10-21 | Outillage de l'assistant | Installer des skills utiles au projet | Lecture complète de 5 skills, résumé de ce qu'ils font, installation (commits `675cf1c`, `b8074bc`) | Les 5 skills | | Garder `.claude/`, `CLAUDE.md` et le support du formateur dans le dépôt public : refusé, retirés et ignorés par Git (**sécurité et RGPD**, commits `69b3de2`, `3204de7`) |
| 15 | 2026-11-15 | Ce journal | « Construis un journal IA pro, avec les règles d'écriture conventionnelles, le plus détaillé possible » | Version 2.0 de ce fichier, reconstruite à partir de l'historique Git, de la spec, du plan et de l'ADR | [à valider par l'équipe] | | |

## 5. Détail chronologique

### 2026-10-20 : cadrage, spec et premier pipeline

- **Contexte.** Le dépôt contenait le kit de départ (cadrage, prompts, sources) mais pas encore le pipeline. Commit de départ : `48f21d5`.
- **Usage de l'IA.** Lecture du cahier des charges et de l'exemple, puis rédaction de la spec (`docs/superpowers/specs/2026-10-20-plein-flotte-design.md`) et du plan en 8 tâches (`docs/superpowers/plans/2026-10-20-plein-flotte.md`).
- **Point de contrôle clé.** L'équipe a demandé à l'IA de critiquer sa propre question business avec des mesures sur les données. Les 9 corrections sont dans la spec, § 2.1.
- **Exécution.** 8 tâches, chacune écrite par un agent puis relue par un autre. Commits `8a4ebe2` (socle, téléchargement) à `64388bf` (README et cartes).
- **Erreur majeure trouvée.** La validation croisée sans purge mélangeait des jours voisins entre entraînement et validation. Les scores étaient trop bons. Corrigé par des plis en jours entiers avec purge de 3 jours (commit `a27a2cb`).

### 2026-10-21 : analyse critique et quatre chantiers

- **Usage de l'IA.** Recherche des points faibles de la question business, puis 4 chantiers menés dans l'ordre, chacun sur sa branche `feat/…` fusionnée dans `plein-flotte`.
- **Erreur de l'IA corrigée.** Le premier chiffrage du choix de la station (environ 3 500 €/an) oubliait le coût du détour. Recalculé : environ 66 €/an avec détour, environ 2 710 €/an au plafond (station déjà sur la tournée). Les deux chiffres sont dans le README.
- **Proposition de l'IA refusée.** La calibration isotonique dégradait le regret sur la validation de l'entraînement. Elle n'a pas été gardée. Seul le score de Brier reste, comme diagnostic.

### 2026-10-21 : nouvelle consigne du professeur sur les sources

- **Contexte.** Le professeur impose le flux quotidien data.gouv.fr et le taux BCE.
- **Usage de l'IA.** Inspection du flux, constat qu'il n'a pas d'historique, rédaction de l'ADR-0001 (statut « proposé », à valider par l'équipe et le professeur), retrait du Brent, refonte du schéma SQL et des deux modèles.
- **Point de contrôle clé.** Le modèle de la démo (prix + taux BCE) a été choisi en validation croisée sur l'entraînement, **avant** de regarder le test. Sur le test, le modèle prix seuls fait un peu mieux (−0,03 c€/L d'écart, intervalle [−0,19 ; 0,12]). La règle fixée d'avance a été gardée.

### 2026-10-21 : hygiène du dépôt

- Installation des skills après lecture complète, puis retrait de `.claude/`, `CLAUDE.md`, `.python-version` et du support du formateur du dépôt public (commits `619d924`, `3204de7`, `69b3de2`). Ces fichiers restent en local.

### 2026-11-15 : rédaction de ce journal

- L'IA a reconstruit ce journal à partir de sources vérifiables : `git log`, spec, plan, ADR, README et version 1 du journal. Elle n'a ajouté aucun chiffre qui ne figure pas déjà dans ces documents.

## 6. Registre des corrections par catégorie (checklist du TD 4)

| Catégorie | Nombre | Lignes du § 4 | Exemple le plus important |
|---|---|---|---|
| correct | 1 | 4 | Formule du seuil fausse avec la cible « hausse > 1 c€ » |
| fuite de données | 4 | 7, 12, 13 (×2) | Validation croisée sans purge |
| validation | 4 | 4 (×2), 10, 13 | Bootstrap par jours, intervalle trop étroit |
| décision business | 4 | 4, 7, 8, 9 | Gain du choix de station sans le coût du détour |
| robustesse | 2 | 7, 9 | Coordonnées inversées ou absentes pour 6 stations |
| sécurité et RGPD | 1 | 14 | Fichiers d'outillage et support du formateur retirés du dépôt public |
| reproductibilité | 0 | — | — |
| dépendances | 0 | — | — |
| tests | 2 | 7 (×2) | Test du week-end incapable d'échouer |
| lisibilité | 0 | — | — |

Une catégorie à 0 veut dire qu'aucune correction de ce type n'a été notée. Cela ne prouve pas l'absence de problème.

## 7. Ce qui n'a pas été confié à l'IA

| Décision ou tâche | Qui | Où c'est écrit |
|---|---|---|
| Validation de la question business et du client fictif | Équipe | Spec § 2, ligne 2 du § 4 |
| Choix du modèle de la démo | Équipe (2026-10-20), puis règle « choix en validation croisée » (2026-10-21) | Spec § 10 bis point 5, ligne 13 |
| Validation des sources avec le professeur | Équipe | ADR-0001, statut « proposé » |
| Suppression de fichiers ou dossiers | Équipe | Spec § 10 |
| Export des PDF (note de synthèse, soutenance) | Équipe, à la main | Spec § 10 bis point 6 |
| Relecture des chiffres du README, des slides et des limites | Équipe | § 11 ci-dessous |

## 8. Données, confidentialité et sécurité

- **Données envoyées à l'IA.** Uniquement des données publiques sous Licence Ouverte (prix des carburants) et des données publiques de la BCE. Le client « Livraisons Exemple » et ses chiffres de flotte sont fictifs.
- **Données personnelles.** Aucune.
- **Secrets.** Aucune clé d'API n'est nécessaire, aucun secret n'est versionné.
- **Fichiers d'outillage.** Les instructions de l'assistant et les skills sont gardés en local et ignorés par Git.
- **Licences.** Les 4 skills du commit `675cf1c` sont sous licence MIT (message du commit).

## 9. Limites de ce journal

- Les prompts sont résumés. Leur texte exact n'a pas été conservé.
- Les sessions de travail avec l'IA ne sont pas archivées dans le dépôt. Les preuves sont les commits, la spec, le plan, l'ADR et le README.
- Les lignes 1 à 14 viennent de la version 1 de ce journal (rédigée le 2026-10-21) et de l'historique Git. Les dates des lignes 1 à 7 sont celles des commits correspondants.
- Le journal note les usages **importants**, pas chaque suggestion acceptée sans changement.
- Ce journal a lui-même été rédigé avec l'IA (ligne 15). L'équipe doit le relire et compléter les champs marqués [à compléter].

## 10. Historique des versions

| Version | Date | Changement |
|---|---|---|
| 1.0 | 2026-10-21 | Tableau des 13 premiers usages et bilan |
| 2.0 | 2026-11-15 | En-tête, outils, règles d'usage, méthode de contrôle, dates et commits par ligne, lignes 14 et 15, détail chronologique, registre par catégorie, décisions non déléguées, confidentialité, limites |

## 11. Bilan en 3 lignes

- **Ce que l'IA nous a fait gagner :** la mesure des données avant de figer la question (horizon, retard du Brent, plafond de gain), et le squelette du pipeline et des tests.
- **L'erreur qui nous aurait coûté le plus cher :** la validation croisée sans purge, qui donnait des scores trop bons parce que des jours voisins se retrouvaient de part et d'autre d'un pli.
- **Ce que nous ne lui confierions pas sans relecture :** le choix de la question, de la cible et du seuil, et l'écriture des limites. L'équipe doit relire elle-même tous les chiffres du README, les textes de la soutenance et les limites.
