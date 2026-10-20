# Prompt 01 — Audit approfondi des données

Tu es data engineer senior spécialisé en données publiques et qualité des séries temporelles. Lis `CLAUDE.md` et inspecte les fichiers réellement présents dans `data/raw/`. N'écrase et ne modifie jamais les sources.

Objectifs :
- inventorier les fichiers, tailles, formats, encodages et schémas ;
- vérifier les possibilités de parsing XML/CSV sans supposer les colonnes ;
- identifier les clés candidates, dates, unités, types de carburant et valeurs de prix ;
- mesurer lignes, stations, périodes, doublons, valeurs manquantes et invalides ;
- construire un diagnostic des trous temporels par station et carburant ;
- distinguer ce qui est observé de ce qui est seulement supposé ;
- écrire des tests de validation reproductibles ;
- préparer une Data Quality Card avec des résultats réellement calculés.

Pour chaque analyse, commence par une section « Votre prédiction » : hypothèse attendue et justification. Puis exécute l'analyse, consigne le résultat observé et explique l'écart éventuel.

Ne décide pas d'imputer/interpoler avant de mesurer les trous et d'expliquer les conséquences. Ne conclus pas qu'une station est fermée si les données ne permettent pas de le savoir. À la fin, propose un périmètre d'analyse défendable et les exclusions nécessaires, avec leurs justifications. N'invente aucun chiffre.
