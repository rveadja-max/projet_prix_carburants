# Exigences du projet issues du document fourni

## Exigences explicites
1. Le livrable est un **data product**, et non un notebook seul.
2. Dépôt Git avec backend et frontend Streamlit séparés.
3. Une démonstration où un utilisateur choisit un cas et voit une recommandation.
4. Livrables documentaires :
   - Data Quality Card ;
   - Model Card ;
   - note de synthèse de deux pages ;
   - journal d'utilisation de l'IA ;
   - plan de soutenance.
5. Dataset : « Prix des carburants en France — flux quotidien », page data.gouv.fr : https://www.data.gouv.fr/datasets/prix-des-carburants-en-france-flux-quotidien
6. Techniques citées : clustering, détection d'anomalies, séries temporelles.
7. Difficultés à traiter : formats XML/CSV et trous dans les séries par station.
8. SQL est imposé pour extraire les données, joindre les tables et construire la table d'analyse.
9. Outils cités ensuite : pandas ou SQL pour l'exploration, scikit-learn pour les modèles, Streamlit pour la démo.
10. Architecture attendue :
    - `backend/` effectue le travail métier ;
    - `frontend/app.py` affiche et appelle uniquement `backend.service` ;
    - le backend doit continuer à fonctionner si l'on retire le frontend.
11. Démonstrateur comprenant au minimum trois écrans ou sections :
    - « Décision » ;
    - « Exploration » ;
    - « Le modèle ».
12. La soutenance doit raconter une décision, parler en unités métier avant les métriques techniques, annoncer les limites et finir par une décision demandée.
13. Chaque étape analytique du notebook doit contenir une cellule « Votre prédiction » : prédiction préalable, exécution, surprise éventuelle et apprentissage.

## Éléments d'exemple à ne pas reprendre comme résultats du projet
Le cas de crédit bancaire et ses chiffres sont explicitement un exemple réservé à l'illustration. Ne pas transposer ses données, ses coûts, ses modèles, ses métriques ou sa recommandation au projet carburants.

## À confirmer auprès du professeur ou dans le cahier des charges complet
- Barème officiel et pondération des critères.
- Date limite, durée de soutenance et format des supports.
- Taille maximale du rapport et éventuelles contraintes de pages.
- Périmètre géographique et temporel attendu.
- Niveau minimal de performance ou de comparaison exigé pour les modèles.
- Modalités exactes de remise du dépôt et des données.
- Si les trois familles de modèles sont obligatoires à part entière ou si une comparaison approfondie de certaines d'entre elles est attendue.

Ne pas présenter ces points inconnus comme des exigences déjà établies.
