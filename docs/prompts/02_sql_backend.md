# Prompt 02 — Pipeline SQL et backend

À partir du rapport d'audit réellement produit, conçois et implémente le pipeline de données. SQL est obligatoire pour les extractions, jointures et la table d'analyse.

Avant de coder :
- présente le schéma proposé et les clés ;
- explique les cardinalités attendues ;
- définis les critères d'acceptation et les tests qui détecteront les pertes ou multiplications de lignes.

Puis implémente en petites étapes :
1. parsing des formats réellement présents ;
2. validation et normalisation ;
3. chargement idempotent en base SQL ;
4. requêtes SQL versionnées dans `backend/sql/` ;
5. construction de la table d'analyse ;
6. service métier indépendant de Streamlit.

Ajoute tests unitaires et d'intégration : fichier vide, colonnes absentes, XML invalide, doublons, date invalide, jointure non unique et réexécution du pipeline. Ne laisse pas le frontend lire directement les sources ou la base. `frontend/app.py` doit importer uniquement `backend.service`.

Exécute les tests pertinents et rapporte les résultats réels. Ne prétends pas qu'une étape est validée sans test.
