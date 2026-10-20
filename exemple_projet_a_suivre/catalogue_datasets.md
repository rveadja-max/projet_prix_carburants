# Catalogue des datasets par secteur

> Liens vérifiés le 2026-09-30. Chaque équipe choisit **un** dataset dans son secteur, ou apporte le sien (voir la checklist en bas).
> Ce catalogue sert au grand bain et au projet. Les TD/TP utilisent le dataset imposé DATAFLOW (Telco Churn).

**Légende**
- **Tâche** : C = classification, R = régression, K = clustering, A = règles d'association, D = détection d'anomalies, T = série temporelle.
- **Niveau** : simple (un fichier propre) · nettoyage réel · gros volume ou plusieurs tables (SQL très utile).
- **Licence** : UCI = CC BY 4.0.

## Banque

| Dataset | Tâche | Taille | Piège à trouver | Niveau |
|---|---|---|---|---|
| [Bank Marketing (UCI)](https://archive.ics.uci.edu/dataset/222/bank+marketing) | C | 45 211 × 16 | `duration` fuit la cible ; ~11 % de oui | |
| [Default of Credit Card Clients (UCI)](https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients) | C, K | 30 000 × 23 | Codes non documentés dans `EDUCATION` et `PAY_x` | |
| [Credit Card Fraud (Kaggle)](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud) | D, C | 284 807 × 31 | 0,17 % de fraudes ; variables anonymisées (issues d'une ACP) | |
| [Give Me Some Credit (Kaggle)](https://www.kaggle.com/competitions/GiveMeSomeCredit) | C | 150 000 × 11 | Revenu manquant ; outliers sur les retards | |

## Assurance

| Dataset | Tâche | Taille | Piège à trouver | Niveau |
|---|---|---|---|---|
| [freMTPL2freq : assurance auto française (OpenML)](https://www.openml.org/d/41214) | R (fréquence de sinistres) | 678 013 × 12 | Beaucoup de zéros ; il faut gérer l'exposition | |
| [COIL 2000 : Caravan (UCI)](https://archive.ics.uci.edu/dataset/125/insurance+company+benchmark+coil+2000) | C | 9 822 × 86 | ~6 % de positifs ; variables socio-démographiques codées | |
| [Medical Cost (Kaggle)](https://www.kaggle.com/datasets/mirichoi0218/insurance) | R | 1 338 × 7 | Petit ; interaction fumeur × IMC | |
| [Health Insurance Cross Sell (Kaggle)](https://www.kaggle.com/datasets/anmolkumar/health-insurance-cross-sell-prediction) | C | 381 109 × 12 | ~12 % de positifs ; codes région/canal anonymisés | |

## Marketing, retail, e-commerce

| Dataset | Tâche | Taille | Piège à trouver | Niveau |
|---|---|---|---|---|
| [Online Retail (UCI)](https://archive.ics.uci.edu/dataset/352/online+retail) | A, K (segmentation RFM) | 541 909 × 8 | Factures d'annulation (« C ») ; ~25 % de `CustomerID` manquants | |
| [Online Retail II (UCI)](https://archive.ics.uci.edu/dataset/502/online+retail+ii) | A, K | 1 067 371 × 8 | Idem, sur 2 onglets Excel | |
| [Customer Personality Analysis (Kaggle)](https://www.kaggle.com/datasets/imakash3011/customer-personality-analysis) | K, C | 2 240 × 29 | Séparateur tabulation ; années de naissance aberrantes | |
| [Olist Brazilian E-Commerce (Kaggle)](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) | K, R, C | ~100 000 commandes, 9 tables | Jointures multiples, **idéal pour SQL** ; licence non commerciale | |
| [Instacart Market Basket (miroir Kaggle)](https://www.kaggle.com/datasets/psparks/instacart-market-basket-analysis) | A | 3,4 M commandes | 713 Mo ; échantillonner avant Apriori | |

## Industrie

| Dataset | Tâche | Taille | Piège à trouver | Niveau |
|---|---|---|---|---|
| [AI4I 2020 : maintenance prédictive (UCI)](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset) | C, D | 10 000 × 14 | Les sous-labels TWF/HDF/PWF/OSF/RNF fuitent la cible ; données synthétiques | |
| [SECOM : semi-conducteurs (UCI)](https://archive.ics.uci.edu/dataset/179/secom) | C, D | 1 567 × 591 | ~7 % d'échecs ; beaucoup de valeurs manquantes et de colonnes constantes | |
| [Steel Plates Faults (UCI)](https://archive.ics.uci.edu/dataset/198/steel+plates+faults) | C (multiclasse), K | 1 941 × 27 | 7 colonnes one-hot à fusionner en une cible | |
| [NASA C-MAPSS : moteurs d'avion](https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data) | R, T (durée de vie restante) | 4 sous-jeux, 26 colonnes | Cible à construire ; split par moteur, pas par ligne | |

## Écologie, environnement, énergie

| Dataset | Tâche | Taille | Piège à trouver | Niveau |
|---|---|---|---|---|
| [Air Quality (UCI)](https://archive.ics.uci.edu/dataset/360/air+quality) | R, T, D | 9 358 × 15 | Valeurs manquantes codées -200 ; séparateur `;` et virgule décimale | |
| [Beijing PM2.5 (UCI)](https://archive.ics.uci.edu/dataset/381/beijing+pm2+5+data) | R, T | 43 824 × 11 | Valeurs manquantes ; split temporel obligatoire | |
| [Forest Fires (UCI)](https://archive.ics.uci.edu/dataset/162/forest+fires) | R | 517 × 12 | Majorité de zéros ; transformation log | |
| [Covertype : couvert forestier (UCI)](https://archive.ics.uci.edu/dataset/31/covertype) | C | 581 012 × 54 | Volume ; classes déséquilibrées | |
| [DPE logements existants (ADEME)](https://data.ademe.fr/datasets/dpe03existant) | C, R, K | 15,6 M × 230 | Filtrer par département via l'API ; l'étiquette est calculée à partir d'autres colonnes (fuite) | |
| [Household Power Consumption (UCI)](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption) | T, K, D | 2 075 259 × 9 | `?` pour les manquants ; données à la minute, à ré-échantillonner | |
| [Appliances Energy (UCI)](https://archive.ics.uci.edu/dataset/374/appliances+energy+prediction) | R | 19 735 × 28 | `rv1` et `rv2` sont du bruit aléatoire : bon test pour l'importance des variables | |

## Open data de l'État

| Dataset | Tâche | Taille | Piège à trouver | Niveau |
|---|---|---|---|---|
| [DVF : Demandes de valeurs foncières (data.gouv.fr)](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/) | R (prix), K | Millions de lignes par an, ~40 colonnes | Une vente peut occuper plusieurs lignes (doublons) | |
| [Accidents corporels de la route : BAAC (data.gouv.fr)](https://www.data.gouv.fr/fr/datasets/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2023/) | C (gravité), K | 4 tables par an | Jointures sur `Num_Acc`, **idéal pour SQL** ; codages qui changent selon les années | |
| [Prix des carburants (data.gouv.fr)](https://www.data.gouv.fr/fr/datasets/prix-des-carburants-en-france-flux-quotidien/) | T, D, K | Flux quotidien | Formats XML/CSV ; trous dans les séries par station | |
| [INSEE : données locales](https://www.insee.fr/fr/information/2410988) | K | Variable | Beaucoup de fichiers : il faut choisir une maille (commune, département) | |
| [Hub'Eau : qualité des cours d'eau (API)](https://hubeau.eaufrance.fr/page/api-qualite-cours-deau) | T, D | API | API paginée ; mesures hétérogènes | |

Portail général : [data.gouv.fr/datasets](https://www.data.gouv.fr/fr/datasets/).

## Santé

| Dataset | Tâche | Taille | Piège à trouver | Niveau |
|---|---|---|---|---|
| [Heart Disease (UCI)](https://archive.ics.uci.edu/dataset/45/heart+disease) | C | 303 × 13 | Petit ; valeurs `?` dans `ca` et `thal` | |
| [Diabetes 130-US Hospitals (UCI)](https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008) | C (réadmission) | 101 766 × 47 | Un même patient apparaît plusieurs fois (fuite si split aléatoire) ; `weight` presque vide | |
| [Breast Cancer Wisconsin (UCI)](https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic) | C, K | 569 × 30 | Variables très corrélées ; trop facile seul, à réserver à l'ACP | |

## Ressources humaines

| Dataset | Tâche | Taille | Piège à trouver | Niveau |
|---|---|---|---|---|
| [IBM HR Analytics Attrition (Kaggle)](https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset) | C, K | 1 470 × 35 | Données fictives ; ~16 % de départs ; colonnes constantes ; question d'équité | |

## Transport et mobilité

| Dataset | Tâche | Taille | Piège à trouver | Niveau |
|---|---|---|---|---|
| [Bike Sharing (UCI)](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset) | R, T | 17 389 × 13 | `casual + registered = cnt`, donc fuite | |
| [NYC Taxi Trips (TLC)](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) | R, K, D | Millions de lignes par mois (Parquet) | Tarifs négatifs ou nuls ; prendre un seul mois | |

## Réservés (non disponibles pour le projet)

- [German Credit (UCI)](https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data) : sert d'exemple de livrable (`projet/exemple_livrable/`).

## Télécom (réservé aux TD/TP)

[IBM Telco Customer Churn](https://github.com/IBM/telco-customer-churn-on-icp4d) (7 043 × 21) est le dataset imposé DATAFLOW des TD et TP. Il ne peut pas servir au projet.

---

## Apporter son propre dataset : checklist de validation (fin de J1)

Le formateur valide le dataset de chaque équipe, qu'il vienne du catalogue ou non, avec ces 7 questions :

1. **Question business** : quel client fictif, quelle décision ?
2. **Taille** : au moins 1 000 lignes, et un volume qui tient sur un ordinateur portable (échantillonner si besoin).
3. **Famille couverte** : au moins une méthode est-elle possible — supervisée (il
   y a une cible exploitable) ou non supervisée (il y a de quoi faire des groupes
   utiles) ? Le supervisé est préférable : c'est celui travaillé en TD.
4. **SQL** : les données peuvent-elles être chargées dans SQLite et jointes ou filtrées en SQL ?
5. **Licence** : l'usage pédagogique est-il autorisé ?
6. **RGPD** : aucune donnée personnelle identifiante. Les données d'entreprise doivent être anonymisées et accompagnées de **l'accord écrit du tuteur**.
7. **Pas déjà « résolu »** : si un notebook Kaggle traite déjà exactement la même question, l'équipe doit poser une question différente.

**Règle :** deux équipes ne prennent pas le même dataset.
