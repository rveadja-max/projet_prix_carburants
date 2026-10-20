# Répartition de l'équipe

Adapter à la taille réelle de l'équipe ; une personne peut porter plusieurs rôles, mais chaque livrable a un responsable identifié.

| Rôle | Responsabilités | Preuve attendue |
|---|---|---|
| Responsable produit / coordination | question métier, critères d'acceptation, décisions et synchronisation | cadrage validé, tableau de suivi |
| Data engineer / SQL | inventaire, parsing, schéma, jointures, table d'analyse | scripts reproductibles, tests SQL |
| Data scientist | exploration, prédictions, clustering, anomalies, séries temporelles | protocoles, baselines, métriques et interprétations |
| Ingénieur backend / qualité | service, tests, intégration, packaging, CI si possible | tests et exécution reproductible |
| Frontend / storytelling | Streamlit, visualisations, parcours de démo, supports | trois vues et démonstration |
| Responsable documentation / revue | Data Quality Card, Model Card, note, journal IA, soutenance | documents cohérents et revue croisée |

## Règles d'équipe
- Toute tâche possède un responsable, un relecteur et un critère d'acceptation.
- Les pull requests sont petites et relues par un autre membre.
- Ne pas merger une fonctionnalité non testée ou une analyse non reproductible.
- La personne qui a produit un résultat ne doit pas être la seule à pouvoir l'expliquer.
- Faire une courte réunion à chaque porte de validation : terminé, bloqué, risque, prochaine décision.
