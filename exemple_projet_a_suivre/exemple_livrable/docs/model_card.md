# Model Card : aide à l'octroi de crédit

> D'après Mitchell et al. (2019), *Model Cards for Model Reporting*.

| Rubrique | Contenu |
|---|---|
| **Usage prévu** | Aider un conseiller à décider d'accorder une demande de crédit ou de l'étudier de plus près. **Pas** de refus automatique. |
| **Usages à éviter** | Refuser automatiquement ; noter une population différente (autre pays, autre époque, crédit immobilier) sans réentraîner et revalider. |
| **Modèle** | Random Forest (300 arbres, `min_samples_leaf=3`, `class_weight="balanced"`), dans un `Pipeline` avec un encodage one-hot. `random_state=42`. |
| **Données** | German Credit (UCI), 1 000 demandes ; split stratifié 75/25 ; voir `data_quality_card.md` |
| **Baseline** | Tout accepter, comme aujourd'hui : coût moyen de 1,50 par demande sur le test. |
| **Métriques** | ROC-AUC de 0,79 sur le test et de 0,79 ± 0,03 en validation croisée (5 plis) ; coût moyen par demande de 0,58, contre 1,50 si on accepte tout |
| **Seuil** | 1/6 : c'est le point où le coût attendu d'accepter une demande (5 × p) dépasse celui de la refuser (1 × (1 − p)) |
| **Variables importantes** | Importance par permutation : statut du compte courant, loin devant la durée, l'épargne et l'historique |
| **Segments** | K-means, k = 3, sur la durée, le montant, l'âge et le taux d'effort standardisés. « Gros crédits longs » : 169 demandes, 40 mois et 7 970 en moyenne, 47 % de défaut. « Petits crédits légers » : 287 demandes, taux d'effort faible, 22 % de défaut. « Petits crédits lourds » : 544 demandes, taux d'effort élevé, 29 % de défaut. |
| **Équité** | Sexe et nationalité exclus. **À faire :** comparer les taux de refus par tranche d'âge, car l'âge peut jouer le même rôle. |
| **Limites** | Petit échantillon ; données anciennes ; biais de sélection (issue connue seulement pour les crédits accordés) ; le modèle n'est pas recalibré |
| **Maintenance** | Réentraîner si le taux de défaut observé s'écarte de plus de 5 points de 30 %. |
