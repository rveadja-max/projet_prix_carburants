-- Table d'analyse : une ligne par station et par jour (calendrier × stations du périmètre).
-- Jointure des deux sources : prix du gazole (archives + flux quotidien) et taux EUR/USD de la BCE.
-- Le périmètre (départements, types de zone) vient de la table `perimetre`, remplie depuis config.
-- Règles anti-fuite (décision prise le jour J à :heure_decision heures) :
--   * prix : dernière mise à jour strictement avant J à :heure_decision h, et pas plus vieille
--     que :report_max jours (sinon la station est muette : prix vide) ;
--   * taux EUR/USD : dernière cotation datée au plus tard J - :retard_taux jours.
-- Les week-ends et jours sans cotation reprennent donc la dernière cotation connue.
-- MATERIALIZED : le marché est calculé une fois par jour, la dernière mise à jour une fois par ligne.
WITH grille AS (
    SELECT
        s.station,
        s.departement,
        c.jour,
        c.jour || 'T' || printf('%02d', :heure_decision) || ':00:00' AS instant_decision
    FROM calendrier AS c
    CROSS JOIN stations_historique AS s
    JOIN perimetre AS p ON p.departement = s.departement AND p.zone = s.zone
),
derniere_maj AS MATERIALIZED (
    SELECT
        g.station,
        g.departement,
        g.jour,
        (
            SELECT pr.maj
            FROM prix AS pr
            WHERE pr.station = g.station
              AND pr.maj < g.instant_decision
              AND pr.maj >= date(g.jour, '-' || :report_max || ' days')
            ORDER BY pr.maj DESC
            LIMIT 1
        ) AS date_maj
    FROM grille AS g
),
marche AS MATERIALIZED (
    SELECT
        c.jour,
        (
            SELECT t.dollars_par_euro FROM taux_change AS t
            WHERE t.jour <= date(c.jour, '-' || :retard_taux || ' days')
            ORDER BY t.jour DESC LIMIT 1
        ) AS taux
    FROM calendrier AS c
)
SELECT
    d.station,
    d.jour,
    d.departement,
    (SELECT pr.valeur FROM prix AS pr WHERE pr.station = d.station AND pr.maj = d.date_maj) AS prix,
    d.date_maj,
    m.taux
FROM derniere_maj AS d
JOIN marche AS m ON m.jour = d.jour
ORDER BY d.station, d.jour;
