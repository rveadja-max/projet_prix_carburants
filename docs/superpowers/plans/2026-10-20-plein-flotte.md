# Plan de développement : SEP Conseil et Livraisons Exemple, aide au plein de la flotte

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal :** reproduire la forme exacte de `exemple_projet_a_suivre/exemple_livrable/` (German Credit) sur les prix du gazole du Nord et du Pas-de-Calais, croisés avec le Brent et l'euro/dollar, pour répondre à « faire le plein aujourd'hui ou dans 3 jours ? ».

**Architecture :** `backend.download` récupère 2 archives XML + 2 CSV. `backend.data` les charge dans SQLite, puis `sql/table_analyse.sql` construit une ligne par station et par jour, jointe au marché (Brent, taux). pandas ajoute la cible et les variables. `backend.model` et `backend.train` entraînent 3 forêts aléatoires (sans Brent, Brent de la veille, Brent à 8 jours) et sauvent celle « Brent de la veille ». `backend.service` est la seule porte du frontend Streamlit à 3 onglets.

**Tech Stack :** Python 3.14, pandas 3.0, scikit-learn 1.9, joblib 1.6, SQLite (`sqlite3`), Streamlit 1.66, pytest 9.

**Spec :** `docs/superpowers/specs/2026-10-20-plein-flotte-design.md` (validée par l'équipe le 2026-10-20). La lire avant toute tâche.

## Global Constraints

- Forme de l'exemple : même structure de fichiers, même style (`config.py` de constantes, `data.py`, `model.py`, `train.py`, `service.py`, `conftest.py`, README en 6 parties). Lire le fichier correspondant de `exemple_projet_a_suivre/exemple_livrable/` avant d'écrire le sien.
- **Noms de code en français** dans tout le dépôt (variables, fonctions, modules), comme l'exemple.
- `backend/` n'importe jamais `streamlit`. `frontend/app.py` n'importe que `backend.service` (plus pandas, streamlit).
- Tous les réglages dans `backend/config.py`, chemins depuis `Path(__file__)`. `SEED = 42`.
- Aucune valeur après `DATE_FIN_DONNEES = "2026-10-19"` n'est utilisée.
- Rien après le jour J dans les variables. Brent : cotations ≤ J − `RETARD_BRENT_JOURS`. Taux : ≤ J − `RETARD_TAUX_JOURS`.
- Seuil et H, B calculés **sur l'entraînement seulement**. Aucun choix fait sur le test.
- `requirements.txt` : `pandas==3.0.*`, `scikit-learn==1.9.*`, `joblib==1.6.*`, `streamlit==1.66.*`, `pytest==9.*`. Rien d'autre.
- Aucun chiffre écrit à la main dans le README ou les docs : tout vient de `models/metriques.json`.
- Lancement en 4 commandes : `pip install -r requirements.txt`, `python -m backend.train`, `python -m pytest`, `python -m streamlit run frontend/app.py`.
- Ne supprimer aucun fichier existant qui n'est pas cité dans ce plan.

## Review Focus

1. **Brent absent le week-end** (`.` dans le CSV FRED, ou date manquante) : le jour J reprend la dernière cotation ≤ J − retard, jamais une date future. Test : `test_brent_reporte_le_week_end` (Tâche 3).
2. **Mise à jour de prix après midi** : elle compte pour le lendemain, pas pour le jour même. Test : `test_prix_du_jour_ignore_les_mises_a_jour_apres_midi` (Tâche 3).
3. **Station muette plus de 7 jours** : pas de prix inventé, la ligne sort de la table. Test : `test_station_muette_plus_de_7_jours_exclue` (Tâche 3).
4. **Prix aberrant ou après la date de fin** (hors [0,8 ; 3,5] €/L, ou `maj` > 2026-10-19) : ignoré au chargement et compté. Test : `test_chargement_ignore_prix_aberrants_et_dates_apres_fin` (Tâche 2).
5. **Date ou station hors de la période de test demandée dans la démo** : message clair, pas de plantage. Test : `test_conseiller_refuse_une_date_hors_test` (Tâche 6).

---

### Tâche 1 : socle en français (Git, config, téléchargement des 4 sources)

**Files :**
- Modify : `backend/config.py` (réécriture complète), `backend/download.py` (renommage et ajout des CSV), `requirements.txt`, `.gitignore`
- Test : `tests/test_download.py` (renommer les appels, ajouter les tests CSV)

**Interfaces :**
- Produit, dans `backend/config.py` :
  - Chemins : `RACINE`, `DOSSIER_BRUT = RACINE / "data" / "raw"`, `DOSSIER_HISTORIQUE = DOSSIER_BRUT / "historique_xml"`, `FICHIER_MANIFESTE = DOSSIER_BRUT / "manifest.json"`, `FICHIER_BRENT = DOSSIER_BRUT / "brent.csv"`, `FICHIER_TAUX = DOSSIER_BRUT / "eurusd.csv"`, `BASE = RACINE / "data" / "carburants.db"`, `FICHIER_MODELE = RACINE / "models" / "modele.joblib"`, `FICHIER_METRIQUES = RACINE / "models" / "metriques.json"`.
  - Sources : `URL_PAGE_SOURCE = "https://www.prix-carburants.gouv.fr/rubrique/opendata/"`, `URL_ARCHIVE_ANNUELLE = "https://donnees.roulez-eco.fr/opendata/annee/{annee}"`, `URL_BRENT = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU&cosd=2024-12-01"`, `URL_TAUX = "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?format=csvdata&startPeriod=2024-12-01"`, `ANNEES = (2025, 2026)`, `DELAI_TELECHARGEMENT_S = 120`.
  - Périmètre et règles : `DATE_FIN_DONNEES = "2026-10-19"`, `CARBURANT = "Gazole"`, `DEPARTEMENTS = ("59", "62")`, `TYPES_ZONE = ("R",)`, `PRIX_MIN, PRIX_MAX = 0.8, 3.5`, `HEURE_DECISION = 12`, `HORIZON_JOURS = 3`, `REPORT_MAX_JOURS = 7`, `RETARD_BRENT_JOURS = 1`, `RETARD_BRENT_REALISTE_JOURS = 8`, `RETARD_TAUX_JOURS = 1`.
  - Validation : `DATE_FIN_ENTRAINEMENT = "2026-04-30"`, `PURGE_JOURS = HORIZON_JOURS`.
  - Flotte (hypothèses) : `NB_VEHICULES = 40`, `LITRES_PAR_PLEIN = 60`, `PLEINS_PAR_SEMAINE = 1`, `LITRES_PAR_AN = NB_VEHICULES * LITRES_PAR_PLEIN * PLEINS_PAR_SEMAINE * 52`.
  - `SEED = 42`.
  - Chaque groupe de constantes porte un commentaire d'une ligne : source vérifiée le 2026-10-20, ou « hypothèse fictive ».
- Produit, dans `backend/download.py` :
  - `url_archive(annee: int) -> str`
  - `chemin_archive(annee: int, dossier: Path) -> Path` (nom inchangé : `PrixCarburants_annuel_{annee}.zip`, les fichiers déjà téléchargés restent valides)
  - `empreinte_sha256(chemin: Path) -> str`
  - `ouvrir_distant(url: str, delai: int)`
  - `telecharger_archive(annee, dossier=DOSSIER_HISTORIQUE, forcer=False, ouvrir_url=ouvrir_distant) -> dict | None`
  - `telecharger_csv(url: str, cible: Path, entete_attendue: str, forcer=False, ouvrir_url=ouvrir_distant) -> dict | None` : écrit dans un `.part`, vérifie que la première ligne commence par `entete_attendue`, sinon supprime le fichier et lève `ValueError`.
  - `mettre_a_jour_manifeste(entrees: list[dict], manifeste: Path = FICHIER_MANIFESTE) -> None`
  - `telecharger_tout(forcer: bool = False) -> list[dict]` : 2 archives, puis Brent (`entete_attendue="observation_date"`), puis taux (`entete_attendue="KEY"`, à vérifier sur le fichier réel). Renvoie les nouvelles entrées et met le manifeste à jour.
  - `main(argv=None) -> int` : options `--annees` et `--forcer`.

- [ ] **Step 1 : initialiser Git** (le cahier des charges exige un dépôt Git)

Run : `git init && git status --short | head`
Expected : le dépôt est créé. `.venv/`, `ECC-main/` et `data/raw/*` n'apparaissent pas une fois `.gitignore` mis à jour (Step 7).

- [ ] **Step 2 : renommer les tests existants et ajouter les tests CSV** dans `tests/test_download.py`

Reprendre les 6 tests en français : `test_url_archive_contient_annee`, `test_telechargement_ecrit_zip_valide_et_empreinte`, `test_archive_presente_pas_retelechargee`, `test_forcer_retelecharge`, `test_archive_invalide_rejetee_et_supprimee`, `test_manifeste_garde_les_entrees_precedentes`. Mêmes assertions, avec les nouveaux noms de fonctions et d'arguments. Ajouter :

```python
def test_csv_valide_ecrit_avec_empreinte(tmp_path):
    contenu = b"observation_date,DCOILBRENTEU\n2026-10-13,125.78\n"
    cible = tmp_path / "brent.csv"
    entree = download.telecharger_csv("http://x", cible, "observation_date",
                                      ouvrir_url=faux_ouvreur(contenu, []))
    assert cible.read_bytes() == contenu
    assert entree["sha256"] == download.empreinte_sha256(cible)

def test_csv_avec_mauvais_entete_rejete(tmp_path):
    cible = tmp_path / "brent.csv"
    with pytest.raises(ValueError):
        download.telecharger_csv("http://x", cible, "observation_date",
                                 ouvrir_url=faux_ouvreur(b"<html>erreur</html>", []))
    assert list(tmp_path.iterdir()) == []
```

- [ ] **Step 3 : vérifier l'échec**

Run : `python -m pytest tests/test_download.py -v`
Expected : FAIL (`AttributeError: module 'backend.download' has no attribute 'url_archive'`)

- [ ] **Step 4 : réécrire `backend/config.py` et `backend/download.py`** avec les interfaces ci-dessus. Garder la logique actuelle (`.part`, `testzip`, manifeste trié). Le manifeste passe de `data/raw/historique_xml/manifest.json` à `data/raw/manifest.json` : y recopier les 2 entrées existantes.

- [ ] **Step 5 : vérifier la réussite**

Run : `python -m pytest tests/test_download.py -v`
Expected : 8 passed

- [ ] **Step 6 : téléchargement réel**

Run : `python -m backend.download`
Expected : 2025 et 2026 « déjà présent, ignoré » ; `brent.csv` et `eurusd.csv` écrits ; `data/raw/manifest.json` contient 4 entrées. Ouvrir `eurusd.csv` pour confirmer l'en-tête utilisé par `entete_attendue`.

- [ ] **Step 7 : `requirements.txt` et `.gitignore`**

`requirements.txt` : exactement les 5 lignes des Global Constraints, au format de l'exemple, sans commentaire superflu. `.gitignore` : ajouter `data/carburants.db` et `models/` aux règles existantes. Garder `ECC-main/`.
Run : `python -m pip install -r requirements.txt && python -m pip check`
Expected : « No broken requirements found. »

- [ ] **Step 8 : commit**

```bash
git add .gitignore requirements.txt pytest.ini backend/ tests/
git commit -m "Socle en français : config, téléchargement des 4 sources"
```

---

### Tâche 2 : chargement brut → SQLite

**Files :**
- Create : `backend/data.py`, `tests/conftest.py`, `tests/test_data.py`

**Interfaces :**
- Consomme : constantes de `backend.config` (Tâche 1).
- Produit, dans `backend/data.py` :
  - `charger_brut_dans_sqlite(archives: list[Path] | None = None, fichier_brent: Path = FICHIER_BRENT, fichier_taux: Path = FICHIER_TAUX, base: Path = BASE, date_fin: str = DATE_FIN_DONNEES) -> dict[str, int]`. Par défaut : `[chemin_archive(a, DOSSIER_HISTORIQUE) for a in ANNEES]`. Lève `FileNotFoundError` si un fichier manque. Renvoie `{"stations": n, "prix": n, "prix_ignores": n, "brent": n, "taux_change": n}`.
  - Tables SQLite (remplacées à chaque appel) :
    - `stations(station TEXT PRIMARY KEY, cp TEXT, departement TEXT, zone TEXT, ville TEXT, adresse TEXT)`, avec `departement = cp[:2]` et `zone` = attribut `pop`.
    - `prix(station TEXT, maj TEXT, valeur REAL)` pour `CARBURANT` seulement, avec un index sur `(station, maj)`.
    - `brent(jour TEXT, dollars_baril REAL)`, sans les lignes `.`.
    - `taux_change(jour TEXT, dollars_par_euro REAL)`.
    - `calendrier(jour TEXT)` : tous les jours du premier `maj` à `date_fin`.
  - XML lu en flux avec `xml.etree.ElementTree.iterparse` (fichiers de 340 à 390 Mo, encodage ISO-8859-1), `elem.clear()` après chaque `pdv`. Une même mise à jour (même station, même `maj`) présente 2 fois n'est gardée qu'une fois.
- Produit, dans `tests/conftest.py` : la fixture `base_test(tmp_path_factory) -> Path` (portée session). Elle fabrique un mini-jeu et le charge avec `charger_brut_dans_sqlite`. Le mini-jeu, décrit une fois et réutilisé par les Tâches 3 à 5 :
  - archive ZIP `PrixCarburants_annuel_2026.zip` contenant un XML ISO-8859-1, du 2026-01-01 au 2026-01-31 ;
  - station `"5900001"` (cp `59000`, `pop="R"`, ville `"LILLE"`) : un prix Gazole chaque jour à 06:00, qui monte de 0,01 €/L tous les 4 jours ;
  - station `"5900002"` (cp `59100`, `pop="R"`, ville `"ROUBAIX"`) : prix à 06:00 les jours pairs ; en plus, le 2026-01-10 à 15:00, un prix de 1,999 ; aucune mise à jour du 2026-01-20 au 2026-01-31 ;
  - station `"5900003"` (cp `59000`, `pop="A"`) : autoroute, à exclure ;
  - station `"7500001"` (cp `75001`, `pop="R"`) : hors périmètre ;
  - station `"5900004"` (cp `59000`, `pop="R"`) : un prix de 9,99 et un prix daté du 2026-02-05 ;
  - une ligne `SP95` pour `5900001` (à ignorer) ;
  - `brent.csv` : jours ouvrés du 2025-12-01 au 2026-01-31, valeur 60,0, sauf **100,0 le 2026-01-15** ; `.` le 2026-01-12 ;
  - `eurusd.csv` : jours ouvrés, 1,10 partout ;
  - `date_fin = "2026-01-31"`.

- [ ] **Step 1 : écrire les tests** dans `tests/test_data.py`

```python
def test_chargement_compte_les_tables(base_test):
    with closing(sqlite3.connect(base_test)) as con:
        assert con.execute("select count(*) from stations").fetchone()[0] == 5
        assert con.execute("select count(*) from brent where dollars_baril is null").fetchone()[0] == 0

def test_chargement_ignore_prix_aberrants_et_dates_apres_fin(base_test):
    with closing(sqlite3.connect(base_test)) as con:
        prix = con.execute("select valeur, maj from prix where station='5900004'").fetchall()
    assert all(0.8 <= v <= 3.5 and m <= "2026-01-31T23:59:59" for v, m in prix)

def test_chargement_garde_seulement_le_gazole(base_test): ...   # pas de ligne SP95 : 5900001 a 31 prix exactement

def test_fichier_absent_leve_une_erreur(tmp_path):
    with pytest.raises(FileNotFoundError):
        charger_brut_dans_sqlite([tmp_path / "absent.zip"], base=tmp_path / "b.db")
```

- [ ] **Step 2 : vérifier l'échec** — Run : `python -m pytest tests/test_data.py -v` → Expected : FAIL (`ModuleNotFoundError` ou `ImportError`).
- [ ] **Step 3 : implémenter `charger_brut_dans_sqlite`** et la fixture.
- [ ] **Step 4 : vérifier la réussite** — Run : `python -m pytest tests/test_data.py -v` → Expected : 4 passed.
- [ ] **Step 5 : contrôle sur les vraies données** — Run : `python -c "from backend.data import charger_brut_dans_sqlite as c; print(c())"` → Expected : environ 10 200 stations et environ 2,8 M prix (chiffres du profil exploratoire de la spec, § 2.1), en moins de 3 minutes. Noter les comptes exacts pour la Data Quality Card (Tâche 7).
- [ ] **Step 6 : commit** — `git add backend/data.py tests/ && git commit -m "Chargement XML et CSV dans SQLite"`

---

### Tâche 3 : table d'analyse (SQL + variables pandas)

**Files :**
- Create : `backend/sql/table_analyse.sql`
- Modify : `backend/data.py`
- Test : `tests/test_data.py`

**Interfaces :**
- Consomme : tables de la Tâche 2.
- Produit :
  - `backend/sql/table_analyse.sql` : requête à paramètres nommés SQLite `:heure_decision, :report_max, :retard_brent, :retard_brent_realiste, :retard_taux` et départements et zones fixés par `config` (voir Step 3). Une ligne par `(station, jour)`, pour `calendrier × stations` filtré sur `DEPARTEMENTS` et `TYPES_ZONE`. Colonnes :
    - `station, jour, departement` ;
    - `prix` : dernière `valeur` avec `maj < jour || 'T' || printf('%02d', :heure_decision) || ':00:00'` et `maj >= date(jour, -:report_max days)` ;
    - `date_maj` : son `maj` ;
    - `brent_eur` : dernier `dollars_baril` avec `brent.jour <= date(jour, -:retard_brent days)`, divisé par le dernier `dollars_par_euro` avec `taux_change.jour <= date(jour, -:retard_taux days)` ;
    - `brent_eur_realiste` : idem avec `:retard_brent_realiste` ;
    - `taux` : ce même dernier taux.
    - Commentaire d'en-tête comme l'exemple : une ligne par station et par jour ; les règles anti-fuite.
  - Dans `backend/data.py` :
    - `lire_table_analyse(base: Path = BASE) -> pd.DataFrame` : exécute le SQL avec les valeurs de `config`, puis appelle `ajouter_cible_et_variables`.
    - `ajouter_cible_et_variables(table: pd.DataFrame) -> pd.DataFrame` :
      - par station, sur la grille quotidienne : `variation_future = prix(J+HORIZON_JOURS) − prix(J)` en €/L, et `hausse = (variation_future > 0).astype(int)` ;
      - variables : `var_prix_1j`, `var_prix_3j`, `var_prix_7j`, `ecart_mediane_dep` (prix − médiane du département ce jour-là), `var_mediane_dep_7j`, `jours_depuis_changement`, `age_prix_jours` (jour − date de `date_maj`), `var_brent_7j`, `var_brent_realiste_7j`, `var_taux_7j`, `jour_semaine` ;
      - supprime les lignes où `prix`, le prix à J+3 ou une variable manque. Renvoie une ligne par `(station, jour)`.
    - `enregistrer_table_analyse(table: pd.DataFrame, base: Path = BASE) -> None` : table SQLite `table_analyse`.
    - `lire_table_enregistree(base: Path = BASE) -> pd.DataFrame` : lève `FileNotFoundError("... Lancer d'abord : python -m backend.train")` si la base ou la table manque.

- [ ] **Step 1 : écrire les tests** (mini-jeu de la Tâche 2)

```python
@pytest.fixture(scope="module")
def table(base_test):
    return lire_table_analyse(base=base_test)

def test_une_ligne_par_station_et_par_jour(table):
    assert not table.duplicated(["station", "jour"]).any()

def test_perimetre_departements_et_zone(table):
    assert set(table["station"]) <= {"5900001", "5900002", "5900004"}

def test_prix_dans_les_bornes_et_cible_binaire(table):
    assert table["prix"].between(0.8, 3.5).all()
    assert set(table["hausse"]) <= {0, 1}

def test_brent_sans_fuite(table):
    # pic à 100 le 2026-01-15 : invisible le 15, visible le 16 (retard 1 jour) ;
    # invisible jusqu'au 22, visible le 23 (retard 8 jours)
    ligne = table[table.station == "5900001"].set_index("jour")
    assert ligne.loc["2026-01-15", "brent_eur"] == pytest.approx(60 / 1.10)
    assert ligne.loc["2026-01-16", "brent_eur"] == pytest.approx(100 / 1.10)
    assert ligne.loc["2026-01-22", "brent_eur_realiste"] == pytest.approx(60 / 1.10)
    assert ligne.loc["2026-01-23", "brent_eur_realiste"] == pytest.approx(100 / 1.10)

def test_brent_reporte_le_week_end(table): ...   # le 2026-01-13 (veille = 12, valeur ".") a le brent du 2026-01-09

def test_prix_du_jour_ignore_les_mises_a_jour_apres_midi(table): ...
    # 5900002 : prix du 2026-01-10 = celui de 06:00 ; le 1,999 de 15:00 apparaît le 2026-01-11

def test_station_muette_plus_de_7_jours_exclue(table): ...
    # 5900002 : dernière mise à jour le 2026-01-18 à 06:00, donc prix connu jusqu'au 25 (report de 7 jours) ;
    # le prix à J+3 étant exigé, aucune ligne après le 2026-01-22

def test_jointure_marche_ne_duplique_pas(base_test): ...
    # nombre de lignes du SQL seul == nombre de couples (calendrier × stations du périmètre)
```

Les dates attendues ci-dessus découlent du mini-jeu. Si la fixture change, recalculer chaque date à la main et l'écrire en commentaire du test.

- [ ] **Step 2 : vérifier l'échec** — Run : `python -m pytest tests/test_data.py -v` → Expected : les nouveaux tests en FAIL.
- [ ] **Step 3 : écrire le SQL et les fonctions.** Le filtre départements et zones peut être injecté via une table SQLite `perimetre(departement, zone)` remplie par `data.py` depuis `config`. Les listes ne sont pas écrites dans le `.sql`, ce qui garde un réglage à un seul endroit.
- [ ] **Step 4 : vérifier la réussite** — Run : `python -m pytest tests/test_data.py -v` → Expected : tout passe.
- [ ] **Step 5 : contrôle sur les vraies données** — Run : `python -c "from backend.data import lire_table_analyse as l; t=l(); print(len(t), t.station.nunique(), t.jour.min(), t.jour.max(), t.hausse.mean())"` → Expected : environ 500 stations, des jours de janvier 2025 au 2026-10-16 (19 − 3), un taux de hausse entre 0,1 et 0,5. Durée à noter : si elle dépasse 5 minutes, ajouter un index et le signaler.
- [ ] **Step 6 : commit** — `git add backend/ tests/ && git commit -m "Table d'analyse SQL : prix du jour, Brent et taux sans fuite"`

---

### Tâche 4 : logique métier (coûts, seuil, split, modèle, segments)

**Files :**
- Create : `backend/model.py`, `tests/test_model.py`

**Interfaces :**
- Consomme : colonnes de la table d'analyse (Tâche 3).
- Produit, dans `backend/model.py` :
  - Listes de variables :
    - `VARIABLES_SANS_BRENT = ["prix", "var_prix_1j", "var_prix_3j", "var_prix_7j", "ecart_mediane_dep", "var_mediane_dep_7j", "jours_depuis_changement", "age_prix_jours", "jour_semaine"]` ;
    - `VARIABLES_AVEC_BRENT = VARIABLES_SANS_BRENT + ["var_brent_7j", "var_taux_7j"]` ;
    - `VARIABLES_BRENT_REALISTE = VARIABLES_SANS_BRENT + ["var_brent_realiste_7j", "var_taux_7j"]` ;
    - `CIBLE = "hausse"`.
  - `couts_moyens(variation_future: pd.Series, hausse: pd.Series) -> tuple[float, float]` : `H` = moyenne de `variation_future × 100` quand `hausse == 1` ; `B` = moyenne de `max(0, −variation_future) × 100` quand `hausse == 0` (zéros compris). En c€/L.
  - `seuil_optimal(hausse_moyenne: float, baisse_moyenne: float) -> float` : renvoie `B / (H + B)`. Docstring qui dérive la règle comme l'exemple : faire le plein si p × H > (1 − p) × B.
  - `regret(variation_future, faire_le_plein) -> np.ndarray` en c€/L : plein → `max(0, −Δ) × 100` ; attendre → `max(0, Δ) × 100`.
  - `cout_moyen(variation_future, proba_hausse, seuil: float) -> float` : moyenne du regret, avec `faire_le_plein = proba_hausse > seuil`.
  - `couts_references(variation_future) -> dict` : `{"toujours_plein": ..., "toujours_attendre": ..., "oracle": 0.0}`.
  - `decouper_temporel(table, fin_entrainement: str = DATE_FIN_ENTRAINEMENT, purge_jours: int = PURGE_JOURS) -> tuple[pd.DataFrame, pd.DataFrame]` : entraînement `jour <= fin` ; test `jour > fin + purge_jours` ; les deux triés par `jour`.
  - `creer_pipeline() -> Pipeline` : `Pipeline([("foret", RandomForestClassifier(n_estimators=200, min_samples_leaf=100, max_samples=0.5, class_weight="balanced", random_state=SEED, n_jobs=-1))])`. Hyperparamètres modifiables si `python -m backend.train` dépasse 10 minutes au total. Jamais réglés sur le test.
  - `evaluer(pipeline, X_test, y_test, variation_future_test, seuil: float) -> dict` : `{"roc_auc", "cout_moyen_modele", "cout_moyen_seuil_05", "importance_permutation"}`. Importance par permutation (scoring `roc_auc`, `n_repeats=5`, `random_state=SEED`) sur un échantillon d'au plus 20 000 lignes tirées avec `SEED`.
  - `VARIABLES_PROFIL = ["prix_relatif", "changements_par_semaine", "volatilite"]`.
  - `profils_stations(table) -> pd.DataFrame` : une ligne par station, indexée par `station`. `prix_relatif` = moyenne de `ecart_mediane_dep` × 100 ; `changements_par_semaine` = 7 × part des jours où `var_prix_1j != 0` ; `volatilite` = écart-type de `var_prix_1j` × 100.
  - `segmenter(profils, k: int = 3) -> pd.DataFrame` : K-means sur `VARIABLES_PROFIL` standardisées (`n_init=10`, `random_state=SEED`), ajoute la colonne `segment`.

- [ ] **Step 1 : écrire les tests**

```python
def test_seuil_issu_des_couts():
    assert seuil_optimal(3.0, 1.0) == pytest.approx(0.25)

def test_couts_moyens_comptent_les_zeros_dans_la_baisse():
    delta = pd.Series([0.02, 0.0, -0.01, 0.0])
    hausse = (delta > 0).astype(int)
    assert couts_moyens(delta, hausse) == pytest.approx((2.0, 1 / 3))

def test_cout_moyen():
    delta = np.array([0.02, -0.01, 0.02, -0.01])   # +2 c, −1 c, +2 c, −1 c
    proba = np.array([0.9, 0.9, 0.1, 0.1])         # plein, plein, attendre, attendre
    # plein et hausse : 0 ; plein et baisse : 1 ; attendre et hausse : 2 ; attendre et baisse : 0
    assert cout_moyen(delta, proba, 0.5) == pytest.approx(3 / 4)

def test_references():
    r = couts_references(np.array([0.02, -0.01]))
    assert r["toujours_plein"] == pytest.approx(0.5)
    assert r["toujours_attendre"] == pytest.approx(1.0)

def test_split_temporel_sans_chevauchement():
    jours = pd.date_range("2026-04-25", "2026-05-10").strftime("%Y-%m-%d")
    entrainement, test = decouper_temporel(pd.DataFrame({"jour": jours}), "2026-04-30", 3)
    assert entrainement["jour"].max() == "2026-04-30"
    assert test["jour"].min() == "2026-05-04"

def test_segmenter_ajoute_k_segments(): ...   # 30 profils aléatoires (seed 42), k=3 → segments {0, 1, 2}
```

- [ ] **Step 2 : vérifier l'échec** — Run : `python -m pytest tests/test_model.py -v` → Expected : FAIL (`ModuleNotFoundError`).
- [ ] **Step 3 : implémenter `backend/model.py`.**
- [ ] **Step 4 : vérifier la réussite** — Run : `python -m pytest tests/test_model.py -v` → Expected : 6 passed.
- [ ] **Step 5 : commit** — `git add backend/model.py tests/test_model.py && git commit -m "Coûts, seuil, split temporel, forêt et segments"`

---

### Tâche 5 : entraînement (`python -m backend.train`)

**Files :**
- Create : `backend/train.py`
- Modify : `tests/conftest.py` (ajout de `modele_entraine`)
- Test : `tests/test_train.py`

**Interfaces :**
- Consomme : `download.telecharger_tout`, `data.*`, `model.*`.
- Produit :
  - `main() -> dict`. Ordre des étapes :
    1. Télécharge si un fichier brut manque.
    2. `charger_brut_dans_sqlite()`, puis `lire_table_analyse()`, puis `enregistrer_table_analyse()`.
    3. `decouper_temporel`. `H, B = couts_moyens(...)` **sur l'entraînement**, puis `seuil = seuil_optimal(H, B)`.
    4. Pour chacune des 3 listes de variables : AUC en validation croisée avec `TimeSeriesSplit(n_splits=3)` sur l'entraînement, `fit`, `evaluer` sur le test.
    5. Sauvegarde du seul pipeline `avec_brent` dans `FICHIER_MODELE`, puis écriture de `FICHIER_METRIQUES`.
  - Structure exacte de `metriques.json` :
    - Premier niveau : `nb_stations`, `nb_lignes_entrainement`, `nb_lignes_test`, `debut_test`, `fin_test`, `taux_hausse`, `hausse_moyenne_c`, `baisse_moyenne_c`, `seuil`, `litres_par_an`.
    - `couts` : `{toujours_plein, toujours_attendre, oracle}`.
    - `modeles` : `{"sans_brent": {...}, "avec_brent": {...}, "brent_realiste": {...}}`. Chacun contient `roc_auc`, `roc_auc_cv_moyenne`, `roc_auc_cv_ecart_type`, `cout_moyen_modele`, `cout_moyen_seuil_05`, `importance_permutation`.
    - `economie_annuelle_euros` = `(couts.toujours_plein − modeles.avec_brent.cout_moyen_modele) / 100 × LITRES_PAR_AN`.
  - Affichage console comme l'exemple : AUC, les coûts des stratégies, le chemin du modèle.
  - `tests/conftest.py` : fixture `modele_entraine` (portée session), qui appelle `train.main()` si `FICHIER_MODELE` est absent, comme l'exemple.

- [ ] **Step 1 : écrire le test**

```python
def test_metriques_coherentes(modele_entraine):
    m = json.loads(FICHIER_METRIQUES.read_text(encoding="utf-8"))
    assert set(m["modeles"]) == {"sans_brent", "avec_brent", "brent_realiste"}
    assert m["debut_test"] > "2026-05-03"
    assert m["seuil"] == pytest.approx(m["baisse_moyenne_c"] / (m["hausse_moyenne_c"] + m["baisse_moyenne_c"]))
    assert m["couts"]["oracle"] == 0.0
    assert all(0.5 <= v["roc_auc"] <= 1 for v in m["modeles"].values()) or pytest.fail("AUC < 0,5 : à investiguer, ne pas masquer")
```

- [ ] **Step 2 : vérifier l'échec** — Run : `python -m pytest tests/test_train.py -v` → Expected : FAIL (`ModuleNotFoundError: backend.train`).
- [ ] **Step 3 : implémenter `backend/train.py`.**
- [ ] **Step 4 : entraînement réel** — Run : `time python -m backend.train` → Expected : se termine en moins de 10 minutes et écrit `models/modele.joblib` et `models/metriques.json`. **Recopier la sortie console dans le compte rendu de tâche.** Si une AUC est inférieure à 0,5 ou si `avec_brent` ne bat pas `toujours_plein`, ne rien corriger sur le test : le noter pour les limites (Tâche 7).
- [ ] **Step 5 : vérifier** — Run : `python -m pytest -v` → Expected : tous les tests passent.
- [ ] **Step 6 : vérifier la reproductibilité** — relancer `python -m backend.train` et comparer avec `diff` les deux `metriques.json` → Expected : identiques.
- [ ] **Step 7 : commit** — `git add backend/train.py tests/ && git commit -m "Entraînement : 3 modèles, seuil issu des coûts, métriques"`

---

### Tâche 6 : `backend/service.py`

**Files :**
- Create : `backend/service.py`, `tests/test_service.py`

**Interfaces :**
- Consomme : `data.lire_table_enregistree`, `model.VARIABLES_AVEC_BRENT`, `model.profils_stations`, `model.segmenter`, `FICHIER_MODELE`, `FICHIER_METRIQUES`.
- Produit :
  - `_modele()` en `lru_cache`, avec le même commentaire joblib/pickle que l'exemple.
  - `_table_test()` en `lru_cache` : lignes de `lire_table_enregistree()` avec `jour >= metriques()["debut_test"]`.
  - `metriques() -> dict`.
  - `lister_stations() -> pd.DataFrame` : colonnes `station, ville, adresse, cp`, stations présentes dans le test, triées par ville. Lire `stations` dans SQLite via une fonction de `data.py`, `lire_stations(base=BASE)`, à ajouter.
  - `jours_disponibles(station: str) -> list[str]`.
  - `historique_prix(station: str) -> pd.DataFrame` : colonnes `jour, prix`.
  - `conseiller(station: str, jour: str) -> dict` : `{"station", "jour", "prix", "proba_hausse", "seuil", "decision", "brent_eur"}`, avec `decision` ∈ `{"faire le plein", "attendre 3 jours"}` (plein si `proba_hausse > seuil`). `ValueError("Station inconnue : ...")` si la station n'existe pas ; `ValueError("Pas de donnée pour ... le ... (période de test : ... à ...)")` si le couple est absent.
  - `profils_segments(k: int = 3) -> pd.DataFrame` : moyenne de `VARIABLES_PROFIL` par segment, plus `effectif` en première colonne, arrondie à 2 décimales, comme l'exemple.

- [ ] **Step 1 : écrire les tests**

```python
def test_conseiller_refuse_une_station_inconnue(modele_entraine):
    with pytest.raises(ValueError, match="Station inconnue"):
        service.conseiller("0000000", "2026-06-01")

def test_conseiller_refuse_une_date_hors_test(modele_entraine):
    station = service.lister_stations()["station"].iloc[0]
    with pytest.raises(ValueError, match="période de test"):
        service.conseiller(station, "2025-03-01")

def test_conseiller_renvoie_une_decision(modele_entraine):
    station = service.lister_stations()["station"].iloc[0]
    jour = service.jours_disponibles(station)[0]
    r = service.conseiller(station, jour)
    assert 0 <= r["proba_hausse"] <= 1
    assert r["decision"] in {"faire le plein", "attendre 3 jours"}
    assert r["seuil"] == pytest.approx(service.metriques()["seuil"])

def test_profils_segments(modele_entraine):
    assert len(service.profils_segments(3)) == 3
```

- [ ] **Step 2 : vérifier l'échec** — Run : `python -m pytest tests/test_service.py -v` → Expected : FAIL.
- [ ] **Step 3 : implémenter.**
- [ ] **Step 4 : vérifier la réussite** — Run : `python -m pytest tests/test_service.py -v` → Expected : 4 passed. Run : `grep -rn "import streamlit" backend/` → Expected : aucune sortie.
- [ ] **Step 5 : commit** — `git add backend/ tests/ && git commit -m "Service : seule interface du frontend"`

---

### Tâche 7 : frontend Streamlit (3 onglets)

**Files :**
- Create : `frontend/app.py`, `tests/test_frontend.py`
- Supprimer : `frontend/.gitkeep`, `backend/.gitkeep`, `tests/.gitkeep` (remplacés par de vrais fichiers)

**Interfaces :**
- Consomme : uniquement `backend.service` (Tâche 6).
- Produit : application en 3 onglets, `["Conseil de plein", "Segments", "Le modèle"]`, calquée sur `exemple_livrable/frontend/app.py` (même ordre, même `try/except FileNotFoundError` avec `st.stop()`).
  - **Titre :** « SEP Conseil × Livraisons Exemple : aide au plein de la flotte ».
  - **Légende :** « Démonstrateur de formation, prix des carburants (Nord, Pas-de-Calais) et cours du Brent. Le gestionnaire garde la décision finale. »
  - **Conseil de plein :**
    - sélection de la station (libellé `ville — adresse`), puis du jour ;
    - `st.metric` de la probabilité de hausse et du prix du jour ;
    - décision en `st.success` ou `st.warning`, avec le seuil ;
    - courbe `historique_prix`.
    - Légende de bas d'écran : « Seuil issu des coûts mesurés sur l'entraînement. En usage réel, il faut le cours du Brent de la veille chaque matin. »
  - **Segments :** curseur k de 2 à 6 (3 par défaut), tableau `profils_segments(k)`, une phrase sur les 3 variables.
  - **Le modèle :**
    - tableau des 7 stratégies de la spec (§ 5), lu dans `metriques()` ;
    - `st.metric` de l'économie annuelle ;
    - `st.bar_chart` des 8 premières importances du modèle `avec_brent` ;
    - liste des limites (texte fixe, mêmes points que le README).
  - Vérifier avec Context7 (`/streamlit/streamlit`) si `use_container_width` est déprécié en 1.66 ; si oui, utiliser `width="stretch"`.

- [ ] **Step 1 : écrire le test** (même forme que l'exemple)

```python
def test_application_demarre_sans_erreur(modele_entraine):
    app = AppTest.from_file("../frontend/app.py", default_timeout=60).run()
    assert not app.exception
    assert len(app.tabs) == 3
```

- [ ] **Step 2 : vérifier l'échec** — Run : `python -m pytest tests/test_frontend.py -v` → Expected : FAIL (`FileNotFoundError: AppTest script not found`).
- [ ] **Step 3 : écrire `frontend/app.py`.**
- [ ] **Step 4 : vérifier la réussite** — Run : `python -m pytest -v` → Expected : tous les tests passent. Run : `grep -n "^from\|^import" frontend/app.py` → Expected : seulement `pandas`, `streamlit`, `from backend import service`.
- [ ] **Step 5 : contrôle à l'œil** — Run : `python -m streamlit run frontend/app.py`. Ouvrir les 3 onglets et vérifier qu'aucune erreur n'apparaît et que les chiffres sont ceux de `metriques.json`.
- [ ] **Step 6 : commit** — `git add frontend/ tests/ && git commit -m "Démonstrateur Streamlit : 3 onglets"`

---

### Tâche 8 : README, docs et CLAUDE.md (chiffres réels)

**Files :**
- Modify : `README.md` (réécriture complète), `CLAUDE.md` (§ 1 noms en français, § 3 question business, § 4.1 sources Brent et taux, § 10 les 4 commandes)
- Create ou remplacer : `docs/note_cadrage.md`, `docs/data_quality_card.md`, `docs/model_card.md`, `docs/note_synthese.md`, `docs/journal_ia.md`, `docs/plan_soutenance.md`. Chacun part du modèle `exemple_projet_a_suivre/modeles/*.md`, ou du fichier de `exemple_livrable/docs/` quand aucun modèle n'existe (cas de `plan_soutenance.md`).

**Interfaces :**
- Consomme : `models/metriques.json`, la sortie de la Tâche 2 (Step 5), les mesures de la spec § 2.1.

- [ ] **Step 1 : README** — mêmes 6 parties et même ton que `exemple_livrable/README.md` :
  1. Titre et bandeau (datasets et licences).
  2. Question business (§ 2 de la spec).
  3. Résultats : tableau des stratégies (spec § 5), avec ses valeurs, puis 3 puces (AUC du test et de la validation croisée ; variable la plus utile ; segment le plus marquant).
  4. Lancer le projet : les 4 commandes. Le premier lancement télécharge environ 62 Mo.
  5. Architecture.
  6. Limites. Au minimum :
     - le Brent de la veille suppose un flux quotidien ;
     - le résultat du scénario à 8 jours ;
     - le plafond de gain ;
     - la période de crise 2026 ;
     - le saut du 1er janvier, de cause non vérifiée ;
     - les volumes fictifs ;
     - le gazole seulement ;
     - « aide à la décision : le gestionnaire décide ».

  Ajouter le tableau « Retours du COMEX », vide, avec la mention « à remplir après le J3 ».
- [ ] **Step 2 : vérifier** que chaque chiffre du README est dans `metriques.json` — Run : `python -c "import json;print(json.dumps(json.load(open('models/metriques.json')),indent=1))"` et comparer ligne à ligne.
- [ ] **Step 3 : docs** — remplir chaque modèle avec les chiffres réels :
  - **Data Quality Card :**
    - comptes de chargement ;
    - stations exclues (autoroute, hors périmètre) ;
    - part des lignes perdues à cause des trous ;
    - prix aberrants ;
    - saut du 1er janvier ;
    - retard de publication du Brent ;
    - changement de source à faire valider par le formateur.
  - **Model Card :** 3 modèles, validation, seuil, règle de réentraînement (`python -m backend.download --forcer`, puis changer `DATE_FIN_DONNEES` et relancer).
  - `journal_ia.md` : les prompts importants de cette session et ce qui a été gardé ou corrigé (dont l'autocritique de la spec, § 2.1).
  - `plan_soutenance.md` : 10 slides, avec des titres qui sont des conclusions.
  - `note_synthese.pdf` et `soutenance.pdf` : exportés à la main par l'équipe (spec § 10 bis). Le signaler dans le compte rendu, sans ajouter de dépendance.
- [ ] **Step 4 : CLAUDE.md** — appliquer les 4 modifications listées dans Files. Ne rien changer d'autre.
- [ ] **Step 5 : test du clone vide** — Run :

```bash
rm -rf /tmp/clone_test && git clone . /tmp/clone_test && cd /tmp/clone_test \
 && python3 -m venv .venv && . .venv/bin/activate \
 && pip install -r requirements.txt && python -m backend.train && python -m pytest
```

Expected : tous les tests passent, et `metriques.json` est identique à celui du dépôt.
- [ ] **Step 6 : commit** — `git add README.md CLAUDE.md docs/ && git commit -m "README, cartes et notes avec les chiffres réels"`
- [ ] **Step 7 : liste du ménage** — écrire dans le compte rendu final la liste des fichiers et dossiers absents de l'exemple (spec § 10). **Ne rien supprimer** : l'équipe décide.
