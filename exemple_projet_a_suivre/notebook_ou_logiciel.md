# Notebook ou logiciel ?

> Fiche de la classe inversée, à lire le soir du J2. Lecture : 10 minutes. Ensuite, la [checklist clean code](checklist_clean_code.md), puis l'[exemple de livrable](exemple_livrable/README.md).

## L'histoire

Mardi soir, Mohamed a un notebook qui marche. La forêt aléatoire bat la baseline, la liste des clients à appeler est prête. Il envoie le fichier à Ousmane, le DSI de DATAFLOW : « Tu peux le lancer chaque lundi ? »

Lundi matin, Ousmane répond :

> « Ligne 1 : le fichier `C:\Users\mohamed\Desktop\telco.csv` n'existe pas. J'ai corrigé le chemin. Cellule 14 : `df_clean2` n'est pas défini. J'ai tout relancé dans l'ordre : le score n'est plus le même. Et où est le seuil ? Je vois 0.3 à trois endroits et 0.35 à un quatrième. »

Le notebook marchait. Mais il ne marchait que **chez Mohamed**, **dans l'ordre où Mohamed avait cliqué**. Linh résume : « Un notebook, c'est un cahier de brouillon. Ousmane a besoin d'une machine. »

## La différence en un tableau

| | Notebook | Logiciel |
|---|---|---|
| Fait pour | **Explorer** : essayer, regarder, recommencer | **Livrer** : tourner sans vous, chaque lundi |
| Ordre d'exécution | Celui que vous avez suivi, souvent dans le désordre | Toujours le même, du début à la fin |
| Réglages | Éparpillés dans les cellules | Dans un seul fichier : `config.py` |
| Vérifications | Vos yeux, sur les sorties | Des **tests** qui tournent seuls |
| Réutilisation | Copier-coller de cellules | Des **fonctions** qu'on importe |

Le notebook n'est pas un mauvais outil. C'est le bon outil pour **chercher**. On ne le livre pas.

## Les 4 pièges du notebook livré

1. **L'état caché.** Une variable existe parce que vous avez exécuté une cellule, puis l'avez supprimée. Le test : « Redémarrer, puis Tout exécuter ». Si ça casse, le notebook ment.
2. **Les chemins de votre ordinateur.** `C:\Users\...` n'existe que chez vous. Un logiciel part de la racine du dépôt.
3. **Les réglages dupliqués.** Le seuil écrit à quatre endroits finit par avoir deux valeurs. Un réglage vit à un seul endroit.
4. **Rien ne vérifie rien.** Si demain la table a des doublons, personne ne le voit. Un test, si.

## Le passage du notebook au dépôt

Vous gardez vos notebooks pour chercher. Quand un morceau marche, vous le **déménagez** :

| Dans le notebook | Devient, dans le dépôt |
|---|---|
| La requête SQL qui construit la table | `backend/sql/table_analyse.sql` |
| Les cellules de chargement et de nettoyage | Une fonction dans `backend/data.py` |
| L'entraînement, le seuil, les métriques | Des fonctions dans `backend/model.py` |
| Le « je relance tout » | `python -m backend.train` |
| Les chiffres que vous regardiez à l'œil | Des tests dans `tests/` |
| Les graphiques pour Claire | Un écran de `frontend/app.py` |

## Une question pour savoir où vous en êtes

> Si Ousmane clone votre dépôt dans un dossier vide et tape les 4 commandes du README, obtient-il le même résultat que vous, sans vous appeler ?

Si la réponse est non, vous avez encore un notebook. Au J3, le cours 6 et le TD 4 vous montrent comment faire la différence.
