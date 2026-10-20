# Synthèse conceptuelle : idéité et ichéité dans le produit de données

## Ce que soutient le document source
Le document « Ichéité et idéité » oppose sans les rendre incompatibles :
- l'idéité : la recherche d'une forme idéale, efficace, reproductible, débarrassée du superflu ;
- l'ichéité : ce qui rend un objet ou un cas précis singulier, lié à son contexte et à ses caractéristiques propres.

Le document insiste aussi sur la création de valeur par la combinaison d'un socle maîtrisé et de spécificités contextuelles, ainsi que sur l'importance de penser la valeur dans la durée. Il s'agit ici d'une synthèse du document fourni, pas d'une validation indépendante de toutes ses affirmations historiques, économiques ou scientifiques.

## Transposition au projet carburants
### Idéité : le socle reproductible
- ingestion reproductible des données ;
- schéma SQL documenté ;
- contrôles de qualité systématiques ;
- fonctions backend réutilisables ;
- baselines et modèles évalués de façon cohérente ;
- tests, versionnage, documentation et interface lisible.

### Ichéité : le contexte de chaque observation
- station et identifiant de station ;
- type de carburant ;
- localisation si disponible ;
- horodatage ou date d'observation ;
- historique et fréquence de publication ;
- couverture temporelle et niveau de confiance des conclusions.

### Synthèse
Le système doit être standardisé dans sa méthode et contextualisé dans son interprétation. Une comparaison nationale peut fournir un repère, mais ne doit pas effacer les effets de localisation, de carburant, de période ou de données insuffisantes.

## Traduction dans l'expérience utilisateur
Pour chaque signal, afficher autant que possible :
1. observation actuelle ;
2. référence de comparaison pertinente ;
3. écart calculé ;
4. contexte disponible ;
5. niveau de confiance ou qualité de couverture ;
6. motif du signal ;
7. action prudente proposée, par exemple « vérifier cette observation ».

## Garde-fous
- Ne pas prétendre que ces concepts philosophiques démontrent la validité d'un modèle.
- Ne pas conclure à une fraude sur la base d'une anomalie statistique.
- Ne pas produire de prévision lorsqu'il n'y a pas assez d'historique fiable.
- Ne pas présenter les exemples et chiffres du document comme des résultats du projet.
