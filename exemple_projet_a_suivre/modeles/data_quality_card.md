# Data Quality Card : [nom du dataset]

> Modèle à copier dans `docs/data_quality_card.md`. Première version le soir du J1, version finale dans N3.
> Inspirée de Gebru et al. (2021), *Datasheets for Datasets*. Exemple rempli : `projet/exemple_livrable/docs/data_quality_card.md`.
> Règle : **chaque défaut a un chiffre et un traitement.** « Quelques manquants » ne suffit pas : on écrit « 11 manquants sur 7 043 (0,2 %), lignes retirées ».

## Identité

| Question | Réponse |
|---|---|
| Unité d'observation (une ligne = ?) | |
| Source, licence, lien | |
| Période et population couvertes | |
| Taille (lignes × colonnes) | |
| Cible : définition, construction, répartition | *Exemple : `defaut` = 1 si mauvais payeur, 30 % des lignes, construite en SQL* |

## Défauts trouvés et ce qu'on en fait

| Défaut | Combien (chiffre et %) | Comment on l'a vu | Ce qu'on en fait, et pourquoi |
|---|---|---|---|
| Valeurs manquantes | | *requête SQL, `isna().sum()`* | |
| Doublons | | *`GROUP BY ... HAVING COUNT(*) > 1`* | |
| Valeurs aberrantes ou impossibles | | | |
| Modalités qui jouent le rôle d'un manquant (« inconnu », 0, -1) | | | |
| Classes déséquilibrées | | | |

## Les pièges pour le modèle

| Question | Réponse |
|---|---|
| Variables à risque de **fuite** (connues seulement après la décision) | *Nommer chaque variable et dire si elle est exclue* |
| Variables sensibles (sexe, origine, santé, âge...) | *Exclues, ou gardées avec une vérification d'équité : dire laquelle* |
| Biais de sélection (qui manque dans les données ?) | |
| Données personnelles : base légale, anonymisation | |

## Ce qu'on attend des données

- Les variables qui devraient être les plus utiles, et pourquoi : 
- Ce que les données ne permettent **pas** de dire : 
