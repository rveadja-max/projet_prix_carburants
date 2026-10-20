# Note de cadrage : [nom du projet]

> Modèle à copier dans `docs/note_cadrage.md`. Une page au plus. À rendre le soir du J1 (jalon non noté : le formateur vous répond par écrit).
> Remplacez chaque ligne en italique. Les exemples viennent de l'exemple de livrable (German Credit).

**Équipe :** [prénoms] · **Dataset :** [nom et lien] · **Client imaginé :** [entreprise, service, personne qui décide]

## 1. La question business, en 2 lignes

*Exemple : la banque accorde des crédits à la consommation. Quelles demandes faut-il accorder, et lesquelles faut-il étudier de plus près ?*

## 2. Les 5 questions du cours 1

| Question | Votre réponse |
|---|---|
| Qu'appelle-t-on exactement la cible ? | *Un défaut = un crédit mal remboursé (cible = 2 dans le fichier)* |
| Que fera le client du résultat ? | *Le conseiller accorde, ou envoie le dossier en étude approfondie* |
| Combien de cas peut-il traiter ? | *Toutes les demandes sont scorées, pas de limite de capacité* |
| Combien coûte une erreur, combien rapporte une bonne décision ? | *Accorder à un mauvais payeur coûte 5, refuser un bon client coûte 1* |
| Quelles données, depuis quand, et qui les connaît ? | *1 000 demandes, banque allemande, années 1990, fichier UCI documenté* |

## 3. Les familles de méthodes prévues

| Famille (carte du data mining) | Pour répondre à quelle question du client ? |
|---|---|
| Supervisé : *classification* ou *régression* | *Qui va faire défaut ?* |
| Non supervisé : *clustering*, *ACP* (si vous le faites) | *Quels profils d'emprunteurs avons-nous ?* |
| Bonus (associations, anomalies), si le dataset s'y prête | |

## 4. Comment saura-t-on que ça marche ?

- **Baseline** (ce qu'on fait sans modèle) : *tout accepter, coût moyen de 1,50 par demande*
- **Métrique qui compte pour le client** : *le coût moyen par demande, pas l'accuracy*
- **Succès** : *un coût moyen nettement plus bas que la baseline sur le jeu de test*

## 5. Les risques déjà vus

*Exemples : variables sensibles (sexe, nationalité), biais de sélection (on ne connaît l'issue que des crédits accordés), petit échantillon.*

## 6. Qui fait quoi

| Membre | Rôle principal (SQL et données, modèle, application, documents et soutenance) |
|---|---|
| | |
