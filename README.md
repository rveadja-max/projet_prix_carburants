# Prix des carburants — Data product

## Finalité
Construire un outil d'aide à l'exploration des prix des carburants en France : profils de stations, observations atypiques et évolution temporelle, à partir du jeu de données public indiqué dans le cadrage.

**Question métier provisoire :** comment aider un utilisateur à repérer les stations dont les prix méritent une attention particulière, à comprendre les écarts et à étudier l'évolution des prix malgré les trous de séries ?

## Principes
- SQL pour extraire, joindre et construire la table d'analyse.
- Python pour la préparation, les caractéristiques, les modèles et l'évaluation.
- Backend indépendant du frontend.
- Streamlit pour la démonstration.
- Toute anomalie est un signal à examiner, pas une preuve d'erreur ou de fraude.
- Résultats et limites mesurés sur les données réellement téléchargées.

## Démarrage sous Ubuntu 24.04 / WSL2

Ouvrir ce dossier depuis Ubuntu dans VS Code. Dans le terminal WSL :

```bash
python3 --version
git --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Version de Python du projet : 3.14 (voir `.python-version`).

### Installer les dépendances

Avec le `.venv` activé :

```bash
python -m pip install -r requirements.txt
python -m pip check
```

`requirements.txt` fixe les versions de pandas, scikit-learn, statsmodels, aeon, Streamlit et pytest. Ces versions ont été vérifiées ensemble sous Python 3.14. `pip check` doit afficher « No broken requirements found. ». Toute nouvelle dépendance doit être justifiée dans `requirements.txt` puis validée par l'équipe.

### Tests et démo (à venir)

pytest et Streamlit sont installés. Ces commandes ne fonctionneront qu'une fois les tests écrits et `frontend/app.py` créé :

```bash
python -m pytest
python -m streamlit run frontend/app.py
```

Les commandes d'import et d'entraînement ne doivent être ajoutées ici qu'après leur implémentation et leurs tests.

## Source de données

Historique des prix : archives annuelles XML publiées sur https://www.prix-carburants.gouv.fr/rubrique/opendata/ (Licence Ouverte). Périmètre : 2025 et 2026 (année en cours).

```bash
python -m backend.download            # télécharge 2025 et 2026 dans data/raw/historique_xml/ (~62 Mo)
python -m backend.download --force    # retélécharge, pour rafraîchir l'année en cours
```

Les fichiers bruts ne sont jamais modifiés et ne sont pas versionnés. `data/raw/historique_xml/manifest.json` note pour chaque fichier l'URL, la date de téléchargement, la taille et l'empreinte SHA-256.

La page data.gouv.fr citée dans le cadrage n'est plus maintenue (liens en erreur 404). Voir `CLAUDE.md`, section 4.1.

## Architecture
- `backend/` : préparation, SQL, features, modèles, évaluation, service.
- `frontend/` : interface Streamlit uniquement.
- `tests/` : tests unitaires, intégration et smoke test de l'application.
- `docs/` : cadrage, qualité des données, modèle, synthèse, journal IA, soutenance.
- `data/raw/` : sources immuables ; ne pas les committer si volumineuses ou si la politique de dépôt l'interdit.

## État du projet
Ce dépôt est un kit de cadrage initial. Aucun résultat empirique n'est considéré comme établi tant que les données n'ont pas été inspectées et les analyses exécutées.
