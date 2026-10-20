# Cahier des charges du projet d'équipe

> Présenté en J1 (accueil), avec la démo de `projet/exemple_livrable/`. Ce qui est noté : **N2** = soutenance (J3), **N3** = dépôt Git (J3 + 7 jours). Les critères sont dans la partie 7.
> L'exemple (German Credit) montre **la forme** attendue. Il est réservé : aucune équipe ne le prend comme projet.

## 1. Ce que vous rendez

| Élément | Où | Pour quelle note |
|---|---|---|
| Dépôt Git : backend et frontend séparés | lien envoyé au formateur | N3 |
| Démonstrateur Streamlit | `frontend/app.py` | N2 (démo) et N3 |
| Data Quality Card, Model Card | `docs/` | N3 |
| Note de synthèse de 2 pages pour le client | `docs/note_synthese.pdf` | N3 |
| Slides de soutenance (PDF) | `docs/soutenance.pdf` | N2 |
| Journal d'usage de l'IA | `docs/journal_ia.md` | N3 |

**Partez des modèles :** `projet/modeles/` contient la note de cadrage, la Data Quality Card, la Model Card, la note de synthèse et le journal IA, à copier dans votre `docs/`. Avant d'écrire du code, lisez la fiche [Notebook ou logiciel ?](notebook_ou_logiciel.md) et la [checklist clean code](checklist_clean_code.md).

> `projet/exemple_livrable/` fait **les deux** familles de méthodes : c'est
> volontairement plus que l'exigence, pour vous montrer la forme attendue dans les
> deux cas. Une seule famille suffit pour votre projet.

## 2. Structure imposée du dépôt

```
backend/            logique métier : AUCUN import de streamlit
  config.py         chemins, seed, paramètres métier (coûts, capacité…)
  sql/*.sql         requêtes SQL versionnées (chargement, table d'analyse)
  data.py           données brutes -> SQLite -> table d'analyse
  model.py          le ou les modèles, le seuil, les métriques
  train.py          python -m backend.train : entraîne et sauvegarde
  service.py        SEULE interface appelée par le frontend
frontend/app.py     Streamlit : affichage et saisie uniquement
tests/              tests pytest
docs/               cartes, note, slides, journal IA
data/raw/           données brutes, jamais modifiées (ou script de téléchargement si trop gros)
requirements.txt    versions fixées
README.md
```

**Règle de séparation :** si on supprime `frontend/`, le backend doit encore tout faire en ligne de commande. Si on remplace Streamlit par une autre interface, on ne touche pas au backend.

## 3. Exigences

**Backend**
- **SQL imposé** pour charger les données dans SQLite et pour les **jointures
  simples**, dans un fichier `.sql` versionné. La table d'analyse complète se fait
  ensuite en **pandas ou en SQL, au choix**.
- **Au moins une méthode**, supervisée *ou* non supervisée :
  - si **supervisée** : comparée à une **référence (baseline)**, avec une
    validation propre — split stratifié ou temporel, validation croisée, pas de
    fuite ;
  - si **non supervisée** (clustering ou ACP) : interprétée en langage métier
    (personas, profils), et confrontée à une description simple des données.
- **Le supervisé est le choix par défaut**, parce que c'est lui qui est travaillé
  en TD guidé au J2. Le non supervisé seul est réservé aux datasets sans cible
  exploitable, et doit être validé par le formateur au J1.
- **Une décision** : seuil, top-N ou règle d'action, justifiés par un coût, une
  capacité ou une valeur attendue. **Obligatoire dans les deux cas.**
- Seed fixée, chemins dans `config.py`, pas de secret dans le code.
- Bonus : la seconde famille de méthodes, les règles d'association, la détection
  d'anomalies.

**Frontend Streamlit (au minimum 3 écrans)**
1. **Décision** : l'utilisateur métier saisit ou choisit un cas et voit la recommandation.
2. **Exploration** : les segments, les profils ou les graphiques clés.
3. **Le modèle** : les performances, les variables importantes et les limites, écrites en clair.

**Tests (au moins 5, et utiles)**
- Des tests sur les données, par exemple « une ligne par individu après jointure », « la cible est binaire », « aucune variable interdite ».
- Au moins un test sur la logique métier, par exemple le seuil ou le coût.
- Un test de démarrage de l'application : `streamlit.testing.v1.AppTest`, voir l'exemple.
- `assert True` et les tests qui ne peuvent pas échouer ne comptent pas.

**README**
- La question business, en 2 lignes.
- Les résultats chiffrés, dans un petit tableau comparé à la baseline.
- Comment lancer le projet, en 4 commandes au maximum.
- L'architecture du dépôt.
- Les limites.

**Journal d'usage de l'IA**
- Les prompts importants.
- Ce que l'IA a produit, ce que vous avez gardé, corrigé ou refusé, et pourquoi (checklist du TD 4).

## 4. Une présentation de qualité (N2)

**Format** : 12 min de pitch, dont 2 min de démo, puis 6 min de questions du COMEX. **Chaque membre prend la parole.**

**Structure conseillée (10 slides)** : voir `projet/exemple_livrable/docs/plan_soutenance.md`.

> Enjeu chiffré → question business → données et qualité → *segments, si vous en
> avez* → modèle contre référence → décision et seuil → variables clés → **démo**
> → limites → recommandation.

**Les 8 règles**
1. **Le titre de chaque slide est une conclusion** (« Le bon seuil est 1/6, pas 0,5 »), pas un sujet (« Résultats »).
2. **Une idée par slide**, au plus 3 chiffres.
3. **Parlez au COMEX** : la valeur en euros, en clients ou en coût, avant la ROC-AUC.
4. **Aucun code sur les slides**, sauf éventuellement une requête SQL courte si elle éclaire le propos.
5. **Des graphiques lisibles du fond de la salle** : axes titrés, unités, police de 18 pt au moins, une couleur pour le message.
6. **La démo est scénarisée** : un cas métier, une action, un résultat. Ayez une **vidéo de secours** si la démo plante.
7. **Dites les limites vous-mêmes**, avant qu'on vous les demande.
8. **Finissez par une décision demandée** (« Nous recommandons de… pendant 3 mois, en suivant tel indicateur »), pas par « Merci, des questions ? ».

**Questions typiques du COMEX** (cartes rôles) :
- DAF : « Combien ça rapporte, combien ça coûte ? »
- Marketing : « Qu'est-ce que je fais lundi matin ? »
- DSI : « Comment on le met en production, qui le maintient ? »
- DPO : « Quelles données personnelles, et est-ce équitable ? »

**Recommandé, pas exigé :** répétez votre pitch en vous chronométrant. Le format
est serré — 12 minutes, et chaque membre prend la parole — et le temps tenu est
noté (N2, critère 4). Il n'y a pas de créneau de répétition le J3 : l'après-midi
démarre directement par le tirage au sort.

## 5. Checklist avant rendu

- [ ] Cloner le dépôt dans un **dossier vide**, puis `pip install -r requirements.txt`, `python -m backend.train`, `python -m pytest`, `python -m streamlit run frontend/app.py` : tout fonctionne.
- [ ] Aucun fichier de données personnelles, de secret ou de modèle de plus de 50 Mo n'est versionné (`.gitignore`).
- [ ] `frontend/` n'importe que `backend.service`.
- [ ] Le README donne les chiffres, et ce sont les mêmes que dans les slides.
- [ ] Les retours du COMEX (J3) sont intégrés et listés dans le README (N3, critère 5).

## 6. Équipe de 3

Mêmes exigences. Les bonus (seconde famille de méthodes, associations, anomalies)
ne sont pas attendus, et le formateur en tient compte dans la grille.

## 7. Comment c'est noté

Chaque note est sur 20 : 5 critères notés de 0 à 4 (0 ou 1 insuffisant, 2 ou 3 attendu, 4 excellent).

| Critère | N2 : soutenance (J3) | N3 : dépôt Git (J3 + 7 jours) |
|---|---|---|
| 1 | Problème business clair, client identifié, enjeu chiffré dès la première minute | Cadrage et Data Quality Card chiffrée |
| 2 | Choix de la méthode justifié, modèle comparé à une référence | Chargement et jointures en SQL, méthode choisie bien appliquée et interprétée |
| 3 | Résultats et limites dits honnêtement, par l'équipe elle-même | Validation propre, interprétation prudente, Model Card complète |
| 4 | Clarté, temps tenu, les 8 règles, démo scénarisée | Backend et frontend séparés, code propre, tests utiles, dépôt qui tourne depuis un clone vide, journal IA |
| 5 | Réponses courtes et adaptées au rôle qui pose la question | Retours du COMEX intégrés et listés, recommandation chiffrée avec un plan de suivi |

**Ce qui fait perdre le plus de points :** un dépôt qui ne tourne pas depuis un clone vide, `import streamlit` dans le backend, un secret versionné, une fuite de données, ou un modèle choisi sur le jeu de test.
