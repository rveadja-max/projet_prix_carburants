# Conception : SEP Conseil et Livraisons Exemple, aide au plein de la flotte

> Document de travail (2026-10-20). Il sert à planifier le développement. Il ne fait pas partie du livrable : le retirer ou le déplacer avant le rendu.
> **Mise à jour du 2026-10-21 :** les sources ont changé (flux quotidien data.gouv.fr + BCE, Brent retiré). Voir `docs/adr/0001-sources-flux-quotidien-et-bce.md`. Les passages sur le Brent ci-dessous sont historiques.
> Règle de fond : reproduire **la forme exacte** de `exemple_projet_a_suivre/exemple_livrable/` (German Credit), avec nos données et notre question.

## 1. Intention

L'équipe veut un livrable qui ait exactement les mêmes pièces que l'exemple du formateur : base SQLite chargée en SQL, question business avec client fictif et coût, modèle supervisé comparé à une référence, seuil de décision tiré des coûts, segmentation en bonus, 3 écrans Streamlit, tests, README, cartes et note.

D'autres groupes traitent les prix des carburants. Le formateur a suggéré de **croiser avec une base complémentaire** pour se distinguer. Choix de l'équipe : **cours du Brent + taux euro/dollar**, joints sur la date.

## 2. Question business (corrigée après autocritique)

> La PME Livraisons Exemple, basée dans le Nord, fait le plein de ses 40 utilitaires diesel une fois par semaine, dans les stations de ses tournées (Nord et Pas-de-Calais). Le gestionnaire de flotte peut avancer ou décaler un plein de quelques jours. **Pour une station donnée, faut-il faire le plein aujourd'hui ou attendre 3 jours, et combien la flotte économise-t-elle en suivant le modèle ?**

Hypothèses fictives, comme la banque de l'exemple : 40 véhicules, 60 L par plein, 1 plein par semaine, soit environ 125 000 L par an. Elles sont dans `config.py`.

### 2.1 Autocritique de la première version et corrections

Mesures faites le 2026-10-20 sur les archives 2025-2026 (gazole, 10 203 stations, 2,83 M relevés, 2025-01-01 → 2026-10-19). Scripts jetables, hors dépôt : ces chiffres seront recalculés par le pipeline.

| # | Problème de la première version | Ce que disent les données | Correction |
|---|---|---|---|
| 1 | « Attendre jusqu'à 7 jours » avec un plein **par semaine** : incohérent, le réservoir ne tient pas 2 semaines | — | Horizon **H = 3 jours** (`HORIZON_JOURS` dans `config.py`) |
| 2 | Le Brent publié par l'EIA arrive **par lots hebdomadaires** : le 2026-10-20, la dernière valeur est celle du 2026-10-14 | Corrélation (variation Brent sur 7 j, variation de la pompe à venir) : 0,45 avec le Brent de la veille, **0,09 avec un retard de 8 jours** | Le décalage du Brent est un réglage (`RETARD_BRENT_JOURS`). Scénario principal : Brent de la veille, en supposant un flux quotidien en production (hypothèse écrite dans les limites). **Scénario réaliste : 8 jours de retard**, présenté aussi. Si le Brent n'apporte rien dans ce scénario, on le dit. |
| 3 | Cible « hausse > 1 c€ » : un seuil arbitraire, et la formule du seuil B / (H + B) devient fausse quand il existe un 3e cas (prix stable) | La médiane de la variation à 3 jours vaut **0** : le prix ne bouge pas dans la majorité des cas | Cible binaire : **le prix à J+3 est strictement plus haut qu'à J**. Coût d'attendre si ça monte : H = hausse moyenne quand ça monte. Coût de faire le plein si ça ne monte pas : B = baisse moyenne, **zéros compris**, quand ça ne monte pas. On fait le plein si p > B / (H + B). H et B sont mesurés sur l'entraînement seulement. |
| 4 | Enjeu annoncé par centime, sans dire combien on peut gagner au mieux | Gain maximal théorique en attendant jusqu'à 3 jours : **0,88 c€/L en moyenne**, médiane 0. Sur toute la France, 2025-2026. | Afficher ce plafond (« oracle ») dans le tableau des résultats. L'enjeu est modeste par litre : il faut le dire avec le volume (environ 1 100 €/an au plafond, hypothèse de volume). |
| 5 | Changement de régime : le gazole passe de 1,67 €/L (fév. 2026) à 2,35 €/L (oct. 2026) ; le Brent de 60 à 114 €/baril | Un split « 2025 contre 2026 » entraînerait sur une période calme et testerait sur une crise | Split temporel : **entraînement jusqu'au 2026-04-30** (qui contient déjà le pic de mars-avril 2026), **test du 2026-05-04 au dernier jour où J+3 est connu**, purge de 3 jours entre les deux. Validation croisée temporelle (`TimeSeriesSplit`) sur l'entraînement. |
| 6 | Toute la France : environ 6,7 M de lignes station-jour, lourd pour une forêt aléatoire sur portable, et sans lien avec des « tournées » | Nord (263 stations) + Pas-de-Calais (239) | Périmètre : **départements 59 et 62** (`DEPARTEMENTS`), stations hors autoroute (`pop = "R"`). Environ 500 stations × 650 jours. |
| 7 | Trous de séries : la station médiane n'envoie une mise à jour que 26 % des jours | Avec report du dernier prix sur 7 jours au plus, 79 % des station-jours ont un prix | Report du dernier prix connu, au plus `REPORT_MAX_JOURS = 7` ; au-delà, la ligne est exclue et comptée dans la Data Quality Card. Une ligne n'entre dans l'analyse que si le prix à J+3 est connu. |
| 8 | Saut au 1er janvier (médiane nationale : 1,554 → 1,599 €/L entre le 30/12/2025 et le 02/01/2026), sans lien avec le Brent | Probable changement de fiscalité, **cause non vérifiée** | Signalé dans la Data Quality Card. Pas de variable « fiscalité » inventée. |
| 9 | Seuil « tiré des coûts » peut-être sans gain face à 0,5 | Sur la France à 3 jours : H ≈ 3,76 c€, baisse moyenne ≈ 2,86 c€ (sans zéros) | On rapporte honnêtement les 2 seuils. Avec les zéros, le seuil baisse encore : à mesurer. |

## 3. Données

| Base | Source officielle | Format | Clé de jointure |
|---|---|---|---|
| Prix des carburants 2025, 2026 | https://www.prix-carburants.gouv.fr/rubrique/opendata/ → `https://donnees.roulez-eco.fr/opendata/annee/AAAA` (Licence Ouverte) | ZIP → XML ISO-8859-1, un `pdv` par station, des `prix` horodatés | station, date |
| Brent quotidien ($/baril) | EIA (domaine public), série RBRTE, via le miroir CSV de FRED : `https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU` | CSV, `.` pour les jours sans cotation | date |
| Euro/dollar quotidien | BCE : `https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?format=csvdata` | CSV (`TIME_PERIOD`, `OBS_VALUE`) | date |

Les trois URL ont été testées le 2026-10-20 (réponse 200, données jusqu'au 2026-10-14 pour le Brent et au 2026-10-20 pour l'euro). Le flux quotidien CSV de data.gouv.fr n'est plus utilisé.

Les week-ends et jours fériés n'ont pas de cotation : le Brent et le taux sont reportés depuis le dernier jour coté **avant** la date (jamais après).

## 4. Le pipeline, fichier par fichier (calqué sur l'exemple)

Noms de code **en français**, comme l'exemple (`RACINE`, `FICHIER_BRUT`, `charger_brut_dans_sqlite`). C'est notre décision, qui découle de la consigne « respecter exactement l'exemple » ; `backend/config.py` et `backend/download.py` (aujourd'hui en anglais) sont renommés, et la règle de `CLAUDE.md` est mise à jour.

| Exemple | Notre fichier | Contenu |
|---|---|---|
| `config.py` | `backend/config.py` | `RACINE`, chemins, URL des 3 sources, `ANNEES`, `DEPARTEMENTS`, `CARBURANT = "Gazole"`, `HORIZON_JOURS = 3`, `RETARD_BRENT_JOURS`, `REPORT_MAX_JOURS = 7`, `DATE_FIN_ENTRAINEMENT`, `SEED = 42`, hypothèses de flotte |
| (ajout justifié) | `backend/download.py` | `python -m backend.download` : 2 archives XML + Brent + euro/dollar, manifeste (URL, date, taille, SHA-256). Seul ajout à la structure de l'exemple. |
| `sql/table_analyse.sql` | `backend/sql/table_analyse.sql` | Jointure **prix ↔ stations ↔ brent ↔ taux_change** sur la station et la date. Brent converti en €/baril. |
| `data.py` | `backend/data.py` | `charger_brut_dans_sqlite()` : XML (iterparse) → tables `stations`, `prix` ; CSV → `brent`, `taux_change`. `lire_table_analyse()` : exécute le SQL puis construit la grille station-jour, le report de prix et les variables en pandas (le cahier des charges autorise pandas pour la table d'analyse complète). |
| `model.py` | `backend/model.py` | `creer_pipeline()` (Random Forest, `class_weight="balanced"`), `seuil_optimal(H, B)`, `cout_moyen()`, `evaluer()` (ROC-AUC, coûts des stratégies, importance par permutation), `segmenter()` (K-means sur les profils de stations) |
| `train.py` | `backend/train.py` | Chargement, split temporel, CV temporelle, entraînement **avec et sans Brent**, sauvegarde `models/modele.joblib` + `models/metriques.json` |
| `service.py` | `backend/service.py` | `lister_stations()`, `conseiller(station, date)`, `metriques()`, `profils_segments(k)` |
| `frontend/app.py` | `frontend/app.py` | 3 onglets : **Conseil de plein** (choisir une station et une date du test → probabilité de hausse, seuil, recommandation, prix du jour), **Segments** (profils K-means), **Le modèle** (tableau des stratégies, avec ou sans Brent, importance des variables, limites) |

Variables candidates pour une ligne station-jour, toutes connues au plus tard le jour J : prix du jour ; écart au prix médian du département le même jour ; variation du prix de la station sur 1, 3 et 7 jours ; variation de la médiane départementale sur 7 jours ; jours depuis le dernier changement de prix ; variation du Brent en €/baril sur 7 jours, décalée de `RETARD_BRENT_JOURS` ; variation de l'euro/dollar sur 7 jours ; jour de la semaine. La liste finale est laissée au développeur, sous la contrainte « rien après J ».

## 5. Résultats attendus (format du README de l'exemple)

| Stratégie (jeu de test) | Coût moyen par plein, c€/L de regret |
|---|---|
| Toujours faire le plein tout de suite (situation actuelle) | à calculer |
| Toujours attendre 3 jours | à calculer |
| Modèle sans Brent, seuil tiré des coûts | à calculer |
| Modèle avec Brent (veille), seuil 0,5 | à calculer |
| **Modèle avec Brent (veille), seuil tiré des coûts** | **à calculer** |
| Modèle avec Brent (8 jours de retard), seuil tiré des coûts | à calculer |
| Plafond : connaître l'avenir (oracle) | à calculer |

Regret d'une décision = prix payé − min(prix à J, prix à J+3), en c€/L. Le README convertit le meilleur écart en euros par an avec les hypothèses de flotte.

**Succès** : la ligne en gras est plus basse que la situation actuelle sur le test, et plus basse que le modèle sans Brent. Sinon, on l'écrit en limite.

## 6. Tests (au moins 8, comme l'exemple)

1. Une seule ligne par station et par jour dans la table d'analyse.
2. Les prix sont dans [0,8 ; 3,5] €/L et la cible vaut 0 ou 1.
3. La jointure avec le Brent et l'euro ne change pas le nombre de lignes.
4. Pas de fuite : sur un petit jeu construit à la main, la variable Brent du jour J n'utilise que des cotations ≤ J − `RETARD_BRENT_JOURS`.
5. Split temporel : la dernière date d'entraînement + la purge est avant la première date de test.
6. `seuil_optimal(H, B)` = B / (H + B) (cas à la main).
7. `cout_moyen()` sur 4 cas calculés à la main.
8. `service.conseiller()` refuse une station inconnue et renvoie une décision valide sinon.
9. `AppTest` : l'application démarre sans erreur et a 3 onglets.

Les tests de données utilisent un **petit extrait XML et CSV fabriqué dans `tests/`** (quelques stations, quelques jours), pour tourner vite et sans réseau. Les tests 8 et 9 utilisent le modèle entraîné, comme `conftest.py` dans l'exemple.

## 7. Documents (copiés des modèles, remplis avec nos chiffres)

`docs/note_cadrage.md`, `docs/data_quality_card.md`, `docs/model_card.md`, `docs/note_synthese.md` (+ PDF), `docs/journal_ia.md`, `docs/plan_soutenance.md` (10 slides, titres = conclusions), README en 6 parties identiques à l'exemple.

## 8. Objectifs, non-objectifs, anti-objectifs

- **Objectifs** : les 4 commandes du README marchent depuis un clone vide (+ `python -m backend.download`) ; tous les chiffres du README viennent de `metriques.json`.
- **Non-objectifs** : autres carburants que le gazole ; calcul d'itinéraires ou de détours ; prévision du prix en euros (régression) ; toute la France.
- **Anti-objectifs** (échec même si ça tourne) : un chiffre affiché qui ne sort pas du pipeline ; un Brent utilisé avant sa date de publication sans le dire ; un modèle ou un seuil choisi sur le test ; `import streamlit` dans `backend/`.

## 9. Contraintes

- Python 3.14 (`.venv` WSL), versions fixées. `requirements.txt` final : pandas, scikit-learn, joblib, streamlit, pytest. **`statsmodels` et `aeon` sont retirés** (non utilisés).
- `frontend/` n'importe que `backend.service`.
- Seed 42, tous les réglages dans `config.py`.
- `.gitignore` comme l'exemple (+ `data/raw/*`, la base SQLite, `models/`).

## 10. Ce qui reste à l'équipe

- **Ménage du dépôt** : `data/interim`, `data/processed`, `artifacts/`, `scripts/`, `docs/cadrage`, `docs/prompts`, `docs/sources`, `docs/architecture.md`, `docs/plan_execution.md`, `docs/roles_equipe.md`, `docs/qualite_et_tests.md`, `docs/README.md`, `ECC-main/` n'existent pas dans l'exemple. Aucun fichier n'est supprimé sans l'accord de l'équipe.
- Valider avec le formateur au J1 le changement de source (archives XML au lieu de la page data.gouv.fr citée, en 404).

## 10 bis. Décisions prises après relecture (choix de Claude, à vérifier par l'équipe)

1. **Données figées** : `DATE_FIN_DONNEES = "2026-10-19"` dans `config.py`. Toute ligne après cette date est ignorée, même si l'archive 2026 est retéléchargée plus tard : les chiffres du README, des slides et de `metriques.json` restent identiques. Le manifeste garde le SHA-256 de l'archive utilisée.
2. **4 commandes, comme l'exemple** : `pip install -r requirements.txt`, `python -m backend.train`, `python -m pytest`, `python -m streamlit run frontend/app.py`. `backend.train` lance lui-même le téléchargement si les fichiers bruts manquent ; `python -m backend.download` reste disponible seul. `conftest.py` fait comme l'exemple : il entraîne le vrai modèle s'il est absent (le premier `pytest` d'un clone vide a donc besoin du réseau, c'est écrit dans le README).
3. **Prix du jour J** = dernier prix enregistré **avant midi** le jour J (`HEURE_DECISION = 12`), c'est-à-dire celui que voit le gestionnaire au moment du plein. Prix à J+3 : même règle. Brent : clôture de la veille au plus tôt. Euro/dollar : publié par la BCE vers 16 h, donc **taux de la veille**.
4. **Deux actions seulement** : plein à J, ou plein à J+3. Regret = prix payé − min(prix J, prix J+3). L'oracle et « toujours attendre » utilisent la même définition. Le chiffre de 0,88 c€/L cité en 2.1 mesurait min(J … J+3) sur toute la France : il sera remplacé par la valeur recalculée par le pipeline.
5. **Modèle de la démo (décision de l'équipe)** : l'écran « Conseil de plein » et `service.conseiller()` utilisent le **modèle avec le Brent de la veille**, sauvegardé dans `models/modele.joblib` (un seul modèle, comme l'exemple). Les deux autres (sans Brent, Brent à 8 jours) ne servent qu'à la comparaison : leurs résultats sont dans `metriques.json` et l'onglet « Le modèle ». L'écran Décision rappelle qu'en usage réel il faut un cours du Brent quotidien (abonnement ou relevé manuel du matin).
6. **PDF** : `note_synthese.pdf` et `soutenance.pdf` sont exportés à la main par l'équipe (depuis le Markdown et l'outil de slides). Aucune dépendance ajoutée pour ça.

## 11. Laissé au développeur

Hyperparamètres de la forêt (dans l'esprit de l'exemple), liste finale des variables, nombre de segments par défaut (3, réglable dans l'écran), mise en page Streamlit, structure interne des fonctions de `data.py`.
