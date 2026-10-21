# SEP Conseil et Livraisons Exemple : aide au plein de la flotte

> Projet de formation (data mining). Sources imposées par le professeur : le [flux quotidien des prix des carburants](https://explore.data.gouv.fr/fr/datasets/6615d83d7d7c66d5ec00c511/#/resources/336c34b5-a527-4c35-b84d-18462daa7c51) (data.gouv.fr, Licence Ouverte), croisé avec le [taux euro/dollar de la BCE](https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?format=csvdata&startPeriod=2024-12-01). Le flux n'a pas d'historique : l'historique des prix vient des archives annuelles du même producteur ([ADR-0001](docs/adr/0001-sources-flux-quotidien-et-bce.md)). Équipe : [à compléter par l'équipe].

## Question business

La PME Livraisons Exemple (Nord) fait le plein de ses 40 utilitaires diesel une fois par semaine dans les stations de ses tournées. **Chaque matin, pour une station donnée : faire le plein aujourd'hui ou attendre 3 jours, et y a-t-il tout près une station ouverte, sans rupture et moins chère ?**

Hypothèses fictives : 40 véhicules, 60 L par plein, 1 plein par semaine, soit 124 800 L par an (réglées dans `backend/config.py`).

## Ce que l'outil donne au gestionnaire chaque matin (écran « Décision »)

- **Le conseil du jour** : la probabilité que le prix monte d'ici 3 jours, et la décision qui en découle (faire le plein ou attendre). Il est calculé à partir des prix connus à midi et du taux BCE de la veille.
- **L'état de la station dans le flux** : fermée, en rupture de gazole, prix du jour, automate 24 h/24.
- **Jusqu'à 3 stations à moins de 5 km**, moins chères aujourd'hui, une fois payé le coût du détour. Elles doivent être ouvertes, sans rupture, et leur prix doit dater de moins de 7 jours.

Le 2026-10-21, sur les 468 stations du flux dans le Nord et le Pas-de-Calais (hors autoroute) :
- 9 sont fermées ;
- 27 sont en rupture de gazole ;
- 45 n'ont pas de prix de gazole ;
- 91 ont un prix vieux de plus de 7 jours.

## Résultats (jeu de test : 55 262 lignes station-jour, du 2026-05-04 au 2026-10-16)

Regret d'une décision = prix payé − min(prix aujourd'hui, prix dans 3 jours), en c€/L.

| Stratégie | Regret moyen (c€/L) | Gain sur la situation actuelle (c€/L, IC 95 %) |
|---|---|---|
| Toujours faire le plein tout de suite (situation actuelle) | 1,24 | — |
| Toujours attendre 3 jours | 1,60 | perte |
| Modèle prix seuls, seuil issu des coûts (0,26) | 0,90 | 0,34 [0,07 ; 0,66], ≈ 420 €/an |
| Modèle prix + taux BCE, seuil 0,5 | 1,00 | — |
| **Modèle prix + taux BCE, seuil issu des coûts : modèle de la démo** | **0,94** | **0,30 [0,07 ; 0,62], ≈ 380 €/an** |
| Plafond : connaître l'avenir | 0,00 | 1,24, ≈ 1 550 €/an |

L'intervalle de confiance vient d'un bootstrap par semaines de la période de test (24 semaines), car les stations d'un même jour, et les jours proches, bougent ensemble.

**Croisement avec la BCE : pas de gain mesurable.**
- **Choix du modèle de la démo**, fait **avant de regarder le test** : le plus petit regret en validation croisée temporelle sur l'entraînement. Le modèle prix + taux BCE l'emporte (0,59 c€/L contre 0,62).
- **Sur le test**, il fait un peu moins bien que le modèle prix seuls. L'apport du taux est de −0,03 c€/L, intervalle [−0,19 ; 0,12], soit environ −40 €/an : un écart nul aux erreurs près.
- **On garde la règle fixée d'avance** : changer de modèle après avoir vu le test serait une fuite. La variation du taux sur 7 jours est la 3e variable la plus utile, mais elle n'améliore pas la décision.

### Le gain dépend de la phase du marché (regret moyen par mois, c€/L)

| Mois | Lignes | Toujours plein | Prix seuls | Prix + taux BCE |
|---|---|---|---|---|
| 2026-05 | 9 010 | 2,93 | 2,03 | 1,81 |
| 2026-06 | 10 154 | 2,00 | 1,08 | 1,46 |
| 2026-07 | 11 217 | 0,16 | 0,21 | 0,26 |
| 2026-08 | 10 127 | 1,21 | 1,17 | 1,12 |
| 2026-09 | 10 019 | 0,46 | 0,44 | 0,43 |
| 2026-10 (jusqu'au 16) | 4 735 | 0,70 | 0,42 | 0,47 |

Presque tout le gain vient de mai et juin, quand les prix redescendent après le pic du printemps. En juillet, quand les prix montent, les deux modèles font pire que « toujours faire le plein ». Il faut donc suivre le regret chaque mois en usage réel.

- ROC-AUC sur le test : 0,68 (prix seuls) et 0,66 (prix + taux BCE). En validation croisée : 0,67 ± 0,05 et 0,66 ± 0,02.
- Les variables les plus utiles (importance par permutation) sont la variation du prix médian du département sur 7 jours, puis l'écart de la station à cette médiane.
- La segmentation K-means (3 segments) isole 67 stations chères, à 7,76 c€/L au-dessus de la médiane de leur département en moyenne.

### Choisir la station : ce que vaut le levier (mesuré sur l'historique)

Pour chaque station habituelle, on cherche les stations à moins de 5 km moins chères en moyenne sur l'entraînement, puis on mesure le gain réel sur le test (402 stations). Une station n'est retenue que si le gain par plein (écart × 60 L) dépasse le coût du détour aller-retour : carburant et temps du chauffeur, hypothèses fictives dans `backend/config.py` (route = 1,3 × vol d'oiseau, 9 L/100 km, 30 €/h, 30 km/h).

| Scénario | Stations où l'on change | Gain moyen (c€/L) | Gain net par plein | Économie annuelle (flotte fictive) |
|---|---|---|---|---|
| La station moins chère impose un détour | 14 % | 0,73 | 0,03 € | ≈ 66 € |
| Plafond : la station moins chère est sur la tournée | 72 % | 2,17 | 1,30 € | ≈ 2 710 € |

Le temps du chauffeur mange presque tout le gain d'un détour. Le levier ne vaut que pour des stations déjà sur la tournée, et c'est au gestionnaire de le vérifier, car les tournées ne sont pas dans les données. Dans l'outil, les stations proches sont comparées sur **les prix du jour du flux**.

**En résumé :** le modèle de la démo fait gagner environ 380 € par an (0,30 c€/L), un gain réel mais modeste. Le croisement avec le taux BCE n'ajoute rien de mesurable. Choisir la bonne station déjà sur la tournée pèse jusqu'à 7 fois plus (≈ 2 710 €/an), et le flux du jour évite d'envoyer un véhicule vers une station fermée ou en rupture.

## Lancer le projet

Dans un environnement virtuel (`python -m venv .venv`, puis `source .venv/bin/activate` sous WSL ou Linux) :

```bash
pip install -r requirements.txt
python -m backend.train                 # téléchargement, SQLite + table d'analyse SQL + entraînement
python -m pytest                        # tests
python -m streamlit run frontend/app.py # démonstrateur
```

Le premier lancement télécharge environ 150 Mo (flux quotidien 85 Mo, archives 62 Mo) et a besoin du réseau (le premier `pytest` d'un clone vide aussi, s'il doit entraîner le modèle). SQLite 3.35 ou plus est nécessaire (le Python 3.14 du projet l'embarque). Les métriques sont figées au 2026-10-19 (`DATE_FIN_DONNEES`) : un nouveau téléchargement ne change pas les chiffres. Pour le conseil du jour, chaque matin : `python -m backend.download --forcer`, puis `python -m backend.train`.

## Architecture : backend et frontend séparés

```
backend/                 logique métier (aucun import de streamlit)
  config.py              chemins, seed, sources, périmètre, hypothèses de flotte
  download.py            téléchargement du flux quotidien, du taux BCE et des archives + manifeste
  sql/schema.sql         schéma de la base SQLite
  sql/table_analyse.sql  table d'analyse construite en SQL (jointure prix × taux BCE, sans fuite)
  data.py                fichiers bruts -> SQLite -> table d'analyse et table du jour
  model.py               Random Forest, seuil, regret, K-means, choix de la station (top-3 net du détour)
  train.py               entraînement des 2 modèles, choix en validation croisée, sauvegarde
  service.py             SEULE interface appelée par le frontend
frontend/
  app.py                 Streamlit : affichage uniquement (Décision, Exploration, Le modèle)
tests/                   tests du backend et démarrage de l'appli
docs/                    ADR, note de cadrage, Data Quality Card, Model Card, note de synthèse, journal IA, plan de soutenance
data/raw/                données brutes (jamais modifiées, ignorées par Git)
models/                  modèle et métriques produits par l'entraînement (ignorés par Git)
```

**Règle :** le frontend n'importe que `backend.service`. On pourrait remplacer Streamlit par une API FastAPI ou un autre front sans toucher au backend.

## Limites

- **Le flux data.gouv.fr est une photo de la veille, sans historique.** L'historique vient des archives annuelles de donnees.roulez-eco.fr, que la page data.gouv.fr cite comme source du flux. Ce choix est à valider par le professeur ([ADR-0001](docs/adr/0001-sources-flux-quotidien-et-bce.md)).
- **Les horodatages du flux portent un « +00:00 » trompeur** : ils sont en heure locale, comme les archives (vérifié sur les mêmes prix). Le suffixe est retiré au chargement.
- **Le croisement avec le taux BCE n'améliore pas la décision sur le test** : −0,03 c€/L [−0,19 ; 0,12]. Le Brent, que le professeur ne demande pas, a été retiré. Le Brent de la veille apportait environ 310 €/an dans la version précédente, mais il supposait un flux payant.
- **Le gain a un plafond** : 1,24 c€/L en connaissant l'avenir, soit environ 1 550 € par an pour la flotte fictive. Le modèle de la démo en capte 0,30 c€/L.
- **Le modèle de la démo conseille de faire le plein dans 80 % des cas.**
- **Le gain se concentre sur mai et juin 2026.** En juillet, les deux modèles font pire que « toujours faire le plein » (tableau par mois ci-dessus).
- **Une seule période de test** (2026-05-04 → 2026-10-16), pendant une crise des prix. La validation croisée varie d'un pli à l'autre.
- **Calibration** : les probabilités sont imparfaitement calibrées. Une calibration isotonique a été testée dans la version précédente, puis rejetée sur la validation de l'entraînement (détail dans la Model Card).
- **Le 1er janvier 2026, la médiane nationale saute de 1,554 à 1,599 €/L en deux jours.** La cause n'est pas vérifiée.
- **Hypothèses fictives** : les volumes de la flotte et les coûts de détour sont fictifs, et les euros par an en dépendent directement.
- **Périmètre** : gazole seulement, départements 59 et 62, stations hors autoroute. Aucun calcul d'itinéraire : la distance est à vol d'oiseau × 1,3, et les tournées réelles sont inconnues.
- Le modèle est une aide à la décision : le gestionnaire décide.

## Retours du COMEX et ce que nous avons changé

| Retour | Ce que nous avons changé |
|---|---|
| à remplir après le J3 | à remplir après le J3 |

La note de synthèse est écrite en Markdown (`docs/note_synthese.md`), puis exportée en PDF (`docs/note_synthese.pdf`) à la main par l'équipe. Les slides sont exportées de la même façon en `docs/soutenance.pdf`.
