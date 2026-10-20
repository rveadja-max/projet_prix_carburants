# Prompt 05 — Revue contradictoire avant livraison

Agis comme un jury exigeant, un reviewer logiciel et un data scientist sceptique. Ne réécris pas le projet immédiatement : réalise d'abord un audit contradictoire.

Vérifie :
- chaque exigence de `docs/cadrage/exigences_professeur.md` ;
- l'isolation backend/frontend ;
- l'utilisation réelle de SQL pour les jointures et la table d'analyse ;
- les trous de séries et formats XML/CSV ;
- la reproductibilité depuis un clone propre ;
- la présence et la qualité des tests ;
- les baselines, fuites temporelles et limites des modèles ;
- la cohérence des résultats dans le code, les documents et les diapositives ;
- la Data Quality Card, la Model Card, la note de deux pages, le journal IA et le plan de soutenance ;
- les risques d'affirmations trop fortes ou de résultats non vérifiés.

Classe les problèmes en bloquants, majeurs, mineurs. Pour chaque problème, indique preuve, impact, correctif proposé et test de validation. Distingue les exigences explicites du professeur des recommandations de l'équipe.

Après validation humaine du plan, corrige par petits lots, exécute les tests et fournis un tableau final : exigence, preuve, statut, limite restante. Ne déclare pas « parfait » ou « prêt » sans preuves.
