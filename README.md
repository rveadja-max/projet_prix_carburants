# SEP Conseil et Livraisons Exemple : aide au plein de la flotte

> Projet de formation (data mining). Datasets : [prix des carburants en France](https://www.data.gouv.fr/fr/datasets/prix-des-carburants-en-france-flux-quotidien-1/) (Licence Ouverte), cours du Brent de l'EIA via [FRED](https://fred.stlouisfed.org/series/DCOILBRENTEU) (domaine public) et taux euro/dollar de la [BCE](https://data.ecb.europa.eu/). Équipe : [à compléter par l'équipe].

## Question business

La PME Livraisons Exemple, basée dans le Nord, fait le plein de ses 40 utilitaires diesel une fois par semaine dans les stations de ses tournées (Nord et Pas-de-Calais). Le gestionnaire de flotte peut avancer ou décaler un plein de quelques jours. **Pour une station donnée, faut-il faire le plein aujourd'hui ou attendre 3 jours, et combien la flotte économise-t-elle en suivant le modèle ?**

Hypothèses fictives : 40 véhicules, 60 L par plein, 1 plein par semaine, soit 124 800 L par an (réglées dans `backend/config.py`).

## Résultats (jeu de test : 55 262 lignes station-jour, du 2026-05-04 au 2026-10-16)

Regret d'une décision = prix payé − min(prix aujourd'hui, prix dans 3 jours), en c€/L.

| Stratégie | Regret moyen (c€/L) | Gain sur la situation actuelle (c€/L, IC 95 %) |
|---|---|---|
| Toujours faire le plein tout de suite (situation actuelle) | 1,24 | — |
| Toujours attendre 3 jours | 1,60 | perte |
| **Modèle sans Brent, seuil issu des coûts (0,26) : utilisable aujourd'hui** | **0,90** | **0,34 [0,07 ; 0,66], ≈ 420 €/an** |
| Modèle avec Brent de la veille, seuil 0,5 | 0,86 | — |
| Modèle avec Brent de la veille, seuil issu des coûts : suppose un flux quotidien payant | 0,66 | 0,58 [0,20 ; 1,04], ≈ 730 €/an |
| Modèle avec Brent à 8 jours de retard (source gratuite), seuil issu des coûts | 0,93 | 0,31 [0,10 ; 0,58] |
| Plafond : connaître l'avenir | 0,00 | 1,24, ≈ 1 550 €/an |

L'intervalle de confiance vient d'un bootstrap par semaines de la période de test (24 semaines) : les stations d'un même jour, et les jours proches, bougent ensemble. Il est large : le gain est positif, mais sa taille est incertaine.

### Le gain dépend de la phase du marché (regret moyen par mois, c€/L)

| Mois | Lignes | Toujours plein | Sans Brent | Brent de la veille | Brent à 8 jours |
|---|---|---|---|---|---|
| 2026-05 | 9 010 | 2,93 | 2,03 | 1,10 | 1,88 |
| 2026-06 | 10 154 | 2,00 | 1,08 | 0,90 | 1,63 |
| 2026-07 | 11 217 | 0,16 | 0,21 | 0,36 | 0,18 |
| 2026-08 | 10 127 | 1,21 | 1,17 | 0,69 | 0,93 |
| 2026-09 | 10 019 | 0,46 | 0,44 | 0,25 | 0,43 |
| 2026-10 (jusqu'au 16) | 4 735 | 0,70 | 0,42 | 0,79 | 0,49 |

Presque tout le gain du modèle sans Brent vient de mai et juin, quand les prix redescendent après le pic du printemps. En juillet, quand les prix montent, il fait pire que « toujours faire le plein ». Le modèle avec le Brent de la veille fait pire en juillet et en octobre. Il faut donc suivre le regret chaque mois en usage réel.

- ROC-AUC de 0,70 sur le test, et de 0,69 ± 0,01 en validation croisée (modèle avec Brent de la veille).
- La variable la plus utile est la variation du Brent sur 7 jours (importance par permutation).
- La segmentation K-means (3 segments) isole 67 stations chères, à 7,76 c€/L au-dessus de la médiane de leur département en moyenne.

### Choisir la station : top-3 des stations moins chères à moins de 5 km

Pour chaque station habituelle, le modèle propose jusqu'à 3 stations à moins de 5 km (vol d'oiseau) moins chères en moyenne sur l'entraînement. Une station n'est proposée que si le gain par plein (écart × 60 L) dépasse le coût du détour aller-retour : carburant et temps du chauffeur (hypothèses fictives dans `backend/config.py` : route = 1,3 × vol d'oiseau, 9 L/100 km, 30 €/h, 30 km/h). Gain mesuré sur la période de test, sur 402 stations :

| Scénario | Stations où l'on change | Gain moyen (c€/L) | Gain net par plein | Économie annuelle (flotte fictive) |
|---|---|---|---|---|
| La station moins chère impose un détour | 14 % | 0,73 | 0,03 € | ≈ 66 € |
| Plafond : la station moins chère est sur la tournée | 72 % | 2,17 | 1,30 € | ≈ 2 710 € |

Le temps du chauffeur mange presque tout le gain d'un détour. Le levier ne vaut que pour des stations déjà sur la tournée : c'est au gestionnaire de le vérifier, car les tournées ne sont pas dans les données.

**En titre : le modèle sans Brent**, le seul utilisable avec les sources gratuites, fait gagner 0,34 c€/L sur la situation actuelle, soit environ 420 € par an pour la flotte fictive (124 800 L). Un cours du Brent de la veille ajoute 0,25 c€/L [0,04 ; 0,48], soit environ 310 € par an : un abonnement au cours quotidien ne vaut la peine que s'il coûte moins. Le plafond (connaître l'avenir) vaut 1,24 c€/L, soit environ 1 550 € par an : l'enjeu du jour du plein est modeste.

## Lancer le projet

Dans un environnement virtuel (`python -m venv .venv`, puis `source .venv/bin/activate` sous WSL ou Linux) :

```bash
pip install -r requirements.txt
python -m backend.train                 # téléchargement, SQLite + table d'analyse SQL + entraînement
python -m pytest                        # 66 tests
python -m streamlit run frontend/app.py # démonstrateur
```

Le premier lancement télécharge environ 62 Mo et a besoin du réseau (le premier `pytest` d'un clone vide aussi, s'il doit entraîner le modèle). SQLite 3.35 ou plus est nécessaire (le Python 3.14 du projet l'embarque). Les données sont figées au 2026-10-19 (`DATE_FIN_DONNEES`) : un nouveau téléchargement ne change pas les chiffres.

## Architecture : backend et frontend séparés

```
backend/                 logique métier (aucun import de streamlit)
  config.py              chemins, seed, sources, périmètre, hypothèses de flotte
  download.py            téléchargement des archives, du Brent et du taux de change + manifeste
  sql/table_analyse.sql  table d'analyse construite en SQL (prix, stations, Brent, taux)
  data.py                fichiers bruts -> SQLite -> table d'analyse
  model.py               Random Forest, seuil, regret, K-means, choix de la station (top-3 net du détour)
  train.py               entraînement des 3 modèles et sauvegarde
  service.py             SEULE interface appelée par le frontend
frontend/
  app.py                 Streamlit : affichage uniquement (3 onglets)
tests/                   tests du backend et démarrage de l'appli
docs/                    note de cadrage, Data Quality Card, Model Card, note de synthèse, journal IA, plan de soutenance
data/raw/                données brutes (jamais modifiées, ignorées par Git)
models/                  modèle et métriques produits par l'entraînement (ignorés par Git)
```

**Règle :** le frontend n'importe que `backend.service`. On pourrait remplacer Streamlit par une API FastAPI ou un autre front sans toucher au backend.

## Limites

- Le Brent de la veille suppose un flux quotidien. La source gratuite (EIA via FRED) arrive par lots : le 2026-10-20, la dernière valeur datait du 2026-10-14. En usage réel, il faut un cours quotidien (abonnement ou relevé manuel le matin).
- Avec le retard réel de 8 jours, le modèle fait pire que sans Brent : regret de 0,93 c€/L contre 0,90, et ROC-AUC de 0,67 contre 0,68. Le gain annoncé ne vaut que si le Brent de la veille est disponible.
- Le gain a un plafond : 1,24 c€/L en connaissant l'avenir, environ 1 550 € par an pour la flotte fictive. Le modèle en capte 0,58 c€/L.
- Le modèle conseille de faire le plein dans 62 % des cas. Il ne dit « attendre » que dans une minorité de situations.
- Le gain se concentre sur mai et juin 2026 (baisse après le pic). Le modèle sans Brent fait pire que « toujours faire le plein » en juillet, et le modèle avec Brent en juillet et en octobre (tableau par mois ci-dessus).
- Une seule période de test (2026-05-04 → 2026-10-16), pendant une crise des prix (gazole et Brent en forte hausse en 2026). Les résultats ne sont pas garantis hors de ce contexte, et la validation croisée varie d'un pli à l'autre (écart-type de 0,01 à 0,06 selon le modèle).
- Le 1er janvier 2026, la médiane nationale saute de 1,554 à 1,599 €/L en deux jours. La cause n'est pas vérifiée (une évolution de fiscalité est probable, non confirmée).
- Les volumes de la flotte (40 véhicules, 60 L, 1 plein par semaine) sont fictifs. Les euros par an en dépendent directement.
- Gazole seulement, départements 59 et 62, stations hors autoroute. Aucun calcul d'itinéraire : le détour vers une autre station est estimé à vol d'oiseau × 1,3, et les tournées réelles sont inconnues.
- Le modèle est une aide à la décision : le gestionnaire décide.

## Retours du COMEX et ce que nous avons changé

| Retour | Ce que nous avons changé |
|---|---|
| à remplir après le J3 | à remplir après le J3 |

La note de synthèse est écrite en Markdown (`docs/note_synthese.md`), puis exportée en PDF (`docs/note_synthese.pdf`) à la main par l'équipe. Les slides sont exportées de la même façon en `docs/soutenance.pdf`.
