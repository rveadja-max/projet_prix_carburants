# Transcription du LLM Council — revue globale du projet

**Date :** 2026-10-31 · **Méthode :** LLM Council (5 conseillers indépendants → relecture croisée anonymisée → synthèse du chairman), d'après la méthode d'Andrej Karpathy.

## Question d'origine

> Revue de tout le projet avec précision et qualité : la logique métier et les fonctionnalités sont-elles défendables, et le rendu est-il raisonnablement calibré sur les données ?

## Question cadrée (enrichie du contexte du dépôt)

Projet de formation en data mining à rendre. Client fictif « Livraisons Exemple » : 40 utilitaires diesel, Nord/Pas-de-Calais (59/62), gazole, un plein/semaine (60 L), 124 800 L/an. Question business : pour une station donnée, faire le plein aujourd'hui ou attendre 3 jours, et combien la flotte économise en suivant le modèle ?

Données : 475 stations, 207 958 lignes station-jour. Prix carburants (flux quotidien data.gouv.fr + archives XML), Brent (EIA/FRED), EUR/USD (BCE). Split temporel (entraînement ≤ 2026-04-30, test 2026-05-04→2026-10-16, 55 262 lignes, purge 3 j). Modèles : 3 forêts aléatoires (sans Brent / Brent veille / Brent 8 j), seuil 0,26 issu des coûts (H=3,25, B=1,16). Baseline « toujours plein » = regret 1,24 c€/L. Résultats test : sans Brent 0,90 (gain 0,34 c€/L, IC95% [0,07;0,66], ≈420 €/an) ; Brent veille 0,66 ; Brent 8j 0,93. ROC-AUC 0,68/0,70/0,67. K-means 3 segments (67 stations chères +7,76 c€/L). Levier « choix station » : 14 % alternatives rentables (≈66 €/an), plafond si sur tournée ≈2 710 €/an. Limites revendiquées : gain concentré mai-juin, crise des prix, volumes fictifs, plafond oracle 1 550 €/an, Brent gratuit en retard, gazole seul, pas d'itinéraire réel.

Enjeu : rendre un projet dont la logique métier, les fonctionnalités et la qualité sont défendables devant le formateur (soutenance), calibré sur les données.

---

## Réponses des 5 conseillers

### The Contrarian (A)
Le vrai problème : quel modèle est livrable ? Brent veille gagne (0,66 vs 0,90) mais le Brent gratuit arrive avec 8 jours de retard, et Brent 8j (0,93) fait pire que sans Brent (0,90). Seule la version sans Brent est déployable : trois modèles entraînés pour rien. Si « Brent veille » est retenu pour son regret test, c'est un choix de modèle sur le jeu de test — ce que la grille pénalise le plus. Où est le jeu de validation ? Les 420 €/an sont gonflés : gain concentré sur mai-juin, juillet négatif ; annualiser extrapole les meilleurs mois. La borne basse de l'IC [0,07 ; 0,66] donne ~87 €/an. L'IC est probablement trop étroit : 55 262 lignes corrélées (stations voisines, semaines) = pseudo-réplication, vrai N ~24 semaines → refaire clusterisé par semaine. Questions évitées : purge de 3 j suffisante avec fenêtres 7-30 j (fuite) ? saut du 1er janv 2026 = aveu d'échec sur un critère noté ? H/B fictifs, pas d'analyse de sensibilité du seuil. 420 € sur ~212 k€ de carburant = 0,2 %, 20 c€/plein : défendre la matérialité métier ou assumer la démo pédagogique.

### The First Principles Thinker (B)
La vraie question n'est pas « prédire une hausse à J+3 » : la flotte ne gagne que si la variance du prix sur 3 j dépasse le coût de la décision. Oracle 1 550 €, modèle 420 € → on capture 27 % d'un gâteau qui vaut 0,2 % du budget. La question first-principles : fallait-il un modèle ? La meilleure réponse de soutenance est peut-être « non, pas pour le timing — voici la preuve chiffrée ». Trois hypothèses : (1) la cible « hausse stricte » jette l'économie (+0,1 et +5 c€ pareils) ; la décision dépend de l'espérance P(baisse)×E[baisse]−P(hausse)×E[hausse] ; prédire le delta ? (2) le seuil 0,26 suppose une asymétrie de coûts absente des prix ; si elle vient des taux de base, le dire. (3) le levier est ailleurs : le choix de station (>5 c€/L) domine le timing (0,9 c€/L). Reformulation : « quel levier — station, jour, ou les deux — vaut combien ? »

### The Expansionist (C)
Le levier enterré : le « où » pèse 6× le « quand » (2 710 € plafond station vs 420 € timing) — et on présente le timing en héros. Fusionner en « ici + aujourd'hui » ≈3 100 €/an = chiffre de titre. Rendre la valeur visible : compteur d'économies cumulées, export PDF hebdo, job quotidien backend.run_daily → de la démo au produit. Démo vivante le jour J (donnée d'hier). Bonus gratuit : détection d'anomalies (résidus → stations bon marché = « bonnes affaires », écran « Opportunités »). Simulateur what-if (« si le Brent monte de 5 $ ? »). Pitch de réplicabilité (une ligne de config → essence/autre département). Benchmark externe vs baromètre national. Tout réutilise l'existant : monétiser, automatiser, généraliser.

### The Outsider (D)
Clair : la question « aujourd'hui ou dans 3 jours » est immédiatement compréhensible ; les 3 onglets répondent au brief ; cartes + journal IA inspirent confiance ; plafond et volumes fictifs = honnêteté. Flou : « regret de 1,24 c€/L » = jargon non défini ; on ne sait pas si 0,90 est spectaculaire ou marginal sans ancre (prix moyen du litre ? règle naïve « plein le lundi » ?) — le formateur posera la question en 30 s. Inquiète : 420 €/an sur volumes fictifs dérisoire (10 €/an/véhicule) ; gain venu de 2 mois de crise sur une seule période (chance ?) ; Brent « payant » pour 0,24 c€/L = incohérence coût/bénéfice. Verdict : démarche sérieuse mais cas métier économiquement faible, récit qui ne l'assume pas — mettre l'honnêteté en titre, pas en note de bas de page.

### The Executor (E)
Livrable, mais le seul critère qui compte — « tourne du premier coup depuis un clone vide » — n'a jamais été validé de bout en bout avec réseau = LE blocage. (1) Test du clone vide sur machine avec réseau (clone → pip install → backend.train → pytest → streamlit), chronométré. (2) Marquer les 14 tests réseau (skip si données absentes) pour un pytest hors-ligne vert. (3) Conflit chiffres README / drift : (a) figer la date + documenter, ou (b) relancer le train la veille et recopier metriques.json — recommandé (b) avec (a) en garde-fou. (4) Avant remise : versions pinnées Ubuntu 24.04, aucun chemin absolu, AppTest sans réseau, PDF régénérés si chiffres bougent, git propre. Risque : data.gouv.fr en panne le jour J → copie locale des brutes + manifeste.

---

## Relecture croisée (anonymisée A–E)

- **A désignée la plus forte par 4 relecteurs sur 5** : seule à attaquer la validité statistique (choix de modèle sur le test, IC en pseudo-réplication N~24 semaines, annualisation biaisée) — des fautes *notées*, falsifiables, corrigeables.
- **B désignée la plus forte par 1 relecteur** : recadrage décisionnel profond (espérance du delta, levier « station » dominant, ose « il ne fallait pas de modèle »).
- **C désignée le plus grand angle mort par les 5 relecteurs** : empile des fonctionnalités sans vérifier le socle ; le ≈3 100 €/an additionne deux estimations corrélées non additives.
- **Angle mort de B** : ignore que la grille impose une méthode supervisée → « il ne fallait pas de modèle » non actionnable pour la note.
- **Angle mort de A, E** : restent dans le cadre technique sans recadrer la valeur métier.

---

## Synthèse du Chairman (verdict)

### Where the Council Agrees
1. La matérialité économique du levier « timing » est faible et le récit ne l'assume pas (A, B, D).
2. Le levier « station » domine le levier « timing » d'un facteur ~6 (B, C).
3. Le gain de 420 €/an est fragile statistiquement (A, D). La démarche (cartes, journal IA, plafond, 3 écrans) n'est contestée par personne.

### Where the Council Clashes
- **Faut-il un modèle ?** B : « non, pas pour le timing ». D tranche : l'honnêteté doit devenir le titre, le modèle reste (exigé par la grille) mais repositionné comme quantificateur d'un levier borné.
- **Fusionner « où » et « quand » ?** C veut additionner ≈3 100 €/an ; les 5 relecteurs rejettent (estimations corrélées non additives). C a raison sur la hiérarchie des leviers, tort sur l'arithmétique.
- **Quel modèle livrer ?** A démontre que seul « sans Brent » est déployable et que choisir « Brent veille » sur le test est la faute sanctionnée. Non réfuté.

### Blind Spots the Council Caught
- Coût logistique d'« attendre 3 jours » jamais calculé (0,9 c€/L × ~80 L ≈ 0,7 €/plein, possiblement < détour) → gain possiblement négatif en coût complet.
- Les prix ne sont pas déclarés quotidiennement → « prix à J+3 » souvent reporté → cible plate, modèle qui apprend le comportement de déclaration.
- Pseudo-réplication : vrai N ~24 semaines → IC clusterisés par semaine.
- Personne n'a relu `seuil_optimal` ni la Data Quality Card avant de débattre.
- La grille N3 sanctionne surtout la fuite et le choix sur test.
- Saut du 1er janv 2026 + absence d'analyse de sensibilité du seuil 0,26.

### The Recommendation
Le rendu est **défendable dans sa démarche, pas encore dans ses chiffres ni dans son récit**. Deux risques éliminatoires à traiter d'abord : (1) refaire l'évaluation honnêtement (modèle choisi sur la validation → « sans Brent », IC clusterisés par semaine, annualisation sur la borne basse ~87 €/an, analyse de sensibilité du seuil, coût logistique de l'attente, justifier/élargir la purge) ; (2) retourner le récit (colonne vertébrale « quel levier vaut combien ? », conclusion honnête en titre : timing ~0,2 % du budget, station ~6× plus, le modèle supervisé sert à le prouver). Rejeter l'addition de C. Couvrir la panne data.gouv.fr par copie locale + manifeste.

### The One Thing to Do First
Exécuter, chronomètre en main, le test du clone vide sur une machine avec réseau : `git clone` → `pip install -r requirements.txt` → `python -m backend.train` → `python -m pytest` → `streamlit run frontend/app.py`. C'est le critère qui coûte le plus de points, jamais validé de bout en bout, et il produit le `metriques.json` frais dont dépendent tous les chiffres corrigés ensuite.

---

*Fin de la transcription.*
