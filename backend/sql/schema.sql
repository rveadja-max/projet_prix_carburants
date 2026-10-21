-- Schéma de la base SQLite (tables remplacées à chaque chargement par backend.data).
--
-- Sources :
--   stations             flux quotidien data.gouv.fr : référentiel du réseau tel qu'il est la veille
--                        (une ligne par station, toute la France)
--   stations_historique  archives annuelles XML : stations ayant publié des prix sur la période
--   prix                 historique du gazole : archives annuelles + dernier prix du flux quotidien
--   taux_change          BCE : taux de référence EUR/USD (dollars pour 1 euro), jours ouvrés
--   calendrier           un jour par ligne, du premier prix au jour du conseil
drop table if exists stations;
drop table if exists stations_historique;
drop table if exists prix;
drop table if exists taux_change;
drop table if exists calendrier;

create table stations (
    station TEXT PRIMARY KEY,
    cp TEXT,
    departement TEXT,
    zone TEXT,               -- R : route, A : autoroute
    ville TEXT,
    adresse TEXT,
    latitude REAL,
    longitude REAL,
    automate_24_24 INTEGER,  -- 1 : paiement par carte possible à toute heure
    fermee INTEGER,          -- 1 : fermeture temporaire ou définitive en cours le jour du conseil
    rupture INTEGER,         -- 1 : rupture du carburant étudié en cours le jour du conseil
    prix_jour REAL,          -- dernier prix connu du carburant (€/L), vide si absent ou aberrant
    maj_prix_jour TEXT       -- date et heure (locales) de ce prix
);
create table stations_historique (station TEXT PRIMARY KEY, cp TEXT, departement TEXT, zone TEXT);
create table prix (station TEXT, maj TEXT, valeur REAL);
create table taux_change (jour TEXT, dollars_par_euro REAL);
create table calendrier (jour TEXT);
