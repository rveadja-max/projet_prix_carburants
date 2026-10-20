# Checklist clean code

> À lire le soir du J2, puis à passer sur votre dépôt au J3 avant les soutenances, et avant le rendu N3. Elle reprend les 4 règles du cours 6. Pour relire du code écrit par une IA, ajoutez la checklist d'audit du TD 4.

Ousmane, le DSI de DATAFLOW, reprendra votre code sans vous. Chaque case cochée, c'est une question qu'il n'aura pas à vous poser.

## 1. Des noms qui disent ce qu'ils contiennent

- [ ] Pas de `df2`, `tmp`, `x`, `res` ou `data_final_v3` : on lit `clients_actifs`, `proba_depart`, `a_appeler`.
- [ ] Une fonction porte un verbe : `construire_table_analyse()`, `choisir_seuil()`.
- [ ] Les nombres ont un nom : `SEUIL`, `COUT_APPEL`, pas `0.3` ou `50` perdus dans le code.
- [ ] Une seule langue pour les noms, français ou anglais, dans tout le dépôt.

## 2. Une fonction, une responsabilité

- [ ] Chaque fonction fait une chose, et son nom le dit. Si vous écrivez « et » pour la décrire, coupez-la en deux.
- [ ] Une fonction tient sur un écran.
- [ ] Une fonction reçoit ses données en paramètre et renvoie un résultat. Elle ne lit pas une variable globale.
- [ ] Pas de code copié-collé : un morceau répété deux fois devient une fonction.
- [ ] Pas de code mort : les cellules d'essai, les `print` de débogage et les fonctions jamais appelées sont supprimés.

## 3. Les réglages à un seul endroit

- [ ] Chemins, seed, seuil, coûts métier : tout est dans `backend/config.py`.
- [ ] Les chemins partent de la racine du dépôt (`Path(__file__)`), jamais de `C:\Users\...`.
- [ ] La seed est fixée : deux lancements donnent le même résultat.
- [ ] Aucun secret dans le code ni dans Git : mots de passe, clés d'API et jetons restent dans des variables d'environnement.
- [ ] `requirements.txt` fixe les versions (`pandas==2.3.*`), et chaque paquet listé sert vraiment.

## 4. Des tests qui peuvent échouer

- [ ] Au moins 5 tests, qui tournent avec `python -m pytest`.
- [ ] Au moins un test sur les données : une ligne par individu, cible binaire, pas de variable interdite.
- [ ] Au moins un test sur la logique métier : le seuil, le coût, la liste d'action.
- [ ] Un test de démarrage de l'application Streamlit (`AppTest`, voir l'exemple de livrable).
- [ ] Pour chaque test, vous savez dire quelle erreur il attraperait. Un test qui ne peut pas échouer ne compte pas.

## 5. Backend et frontend : deux pièces, une seule porte

- [ ] `backend/` n'importe jamais `streamlit`. Vérification : `grep -rn "import streamlit" backend/` ne renvoie rien.
- [ ] Dans le projet, `frontend/app.py` n'importe que `backend.service` (pandas ou streamlit, oui ; `backend.model`, non).
- [ ] Le frontend affiche et fait saisir. Il ne calcule ni seuil, ni coût, ni score.
- [ ] Sans le frontend, `python -m backend.train` fait encore tout le travail.

## 6. Le test final : le clone dans un dossier vide

- [ ] `git clone` du dépôt dans un dossier vide.
- [ ] `pip install -r requirements.txt`, `python -m backend.train`, `python -m pytest`, `python -m streamlit run frontend/app.py` : tout marche du premier coup.
- [ ] Les chiffres affichés sont les mêmes que dans le README et dans les slides.
- [ ] `.gitignore` exclut les données personnelles, les secrets, les modèles lourds, `__pycache__/` et `.venv/`.

Si une case reste vide, notez pourquoi dans le README, partie « Limites ». Dire une limite vaut mieux que la cacher.
