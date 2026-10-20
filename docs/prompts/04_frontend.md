# Prompt 04 — Démonstrateur Streamlit orienté décision

Construis le frontend Streamlit seulement après stabilisation des contrats de `backend.service`. Le frontend ne doit importer aucun autre module backend ni manipuler directement les fichiers de données.

Créer trois vues :
1. **Décision** : un cas sélectionné, un signal ou une recommandation prudente, les raisons, le contexte et la qualité de couverture.
2. **Exploration** : profils, filtres, comparaisons et visualisations descriptives.
3. **Le modèle** : méthode, baselines, métriques réellement calculées, limites et date/version des données.

Exigences :
- utiliser un langage compréhensible pour un utilisateur métier ;
- afficher les unités, dates et périmètres ;
- expliquer les signaux d'anomalie sans les assimiler à des erreurs ou fraudes ;
- afficher « données insuffisantes » lorsqu'une sortie n'est pas justifiée ;
- fournir des états vides et des messages d'erreur utiles ;
- ne pas exposer de chiffre non vérifié ;
- tester le démarrage de l'application et les parcours principaux.

Avant de modifier, inspecte le code existant et présente les fichiers à changer. Après modification, lance les tests et le smoke test, puis résume ce qui a été réellement vérifié.
