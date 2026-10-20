# Model Card : [nom du modèle]

> Modèle à copier dans `docs/model_card.md`. Pour N3.
> Inspirée de Mitchell et al. (2019), *Model Cards for Model Reporting*. Exemple rempli : `projet/exemple_livrable/docs/model_card.md`.
> Écrivez pour le client, pas pour le formateur : Claire doit pouvoir lire chaque ligne. Les chiffres doivent être ceux du README et des slides.

| Rubrique | Contenu |
|---|---|
| **Usage prévu** | Qui l'utilise, pour quelle décision. *Exemple : aider un conseiller à accorder ou à étudier une demande.* |
| **Usages à éviter** | *Exemple : pas de refus automatique, pas d'usage sur une autre population.* |
| **Modèle** | Algorithme, réglages principaux, `random_state`. |
| **Données** | Dataset, taille, split (stratifié ou temporel, et proportions). Renvoi vers `data_quality_card.md`. |
| **Baseline** | Ce qu'on fait sans modèle, et son score. |
| **Performances** | Métrique métier et métrique technique, sur le test **et** en validation croisée (moyenne ± écart-type). |
| **Décision** | Seuil ou top N retenu, et le calcul qui le justifie (coût, capacité, valeur). |
| **Variables importantes** | Importance par permutation. Rappel : une variable importante n'est pas une cause. |
| **Segments** (non supervisé) — *à remplir seulement si vous en avez* | Méthode, nombre de segments, un nom métier et un chiffre par segment. |
| **Équité** | Variables sensibles exclues, et ce qui a été vérifié (taux d'erreur par groupe). Ce qui reste à vérifier. |
| **Limites** | Taille, ancienneté, biais de sélection, ce que le modèle ne voit pas. |
| **Maintenance** | Quel indicateur suivre, et à quel moment réentraîner. |
