# Data Quality Card : German Credit

| Question | Réponse |
|---|---|
| Unité d'observation | Une demande de crédit |
| Source et licence | UCI Machine Learning Repository, Hofmann (1994), CC BY 4.0 |
| Période, population | Banque allemande, années 1990 ; population non décrite (biais de sélection possible : seuls les crédits **accordés** ont une issue connue) |
| Taille | 1 000 lignes × 20 variables + cible |
| Cible | `defaut` = 1 si mauvais payeur (30 %), construite en SQL depuis `cible = 2` |
| Valeurs manquantes | Aucune dans le fichier, mais la modalité « inconnue / pas de compte » en joue le rôle (`epargne` = A65, `statut_compte` = A14) |
| Doublons | Aucun (vérifié : `client_id` unique après chargement) |
| Codage | Variables catégorielles codées `A11`… ; décodées en SQL pour les variables affichées |
| Variables sensibles | `statut_personnel_sexe`, `travailleur_etranger` : exclues du modèle ; `age` est conservé, voir Model Card |
| Risque de fuite | Faible : toutes les variables sont connues au moment de la demande |
| Variables utiles attendues | Statut du compte, durée, historique de crédit, épargne |
