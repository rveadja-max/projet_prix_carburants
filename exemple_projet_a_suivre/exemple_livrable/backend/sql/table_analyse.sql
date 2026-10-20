-- Table d'analyse : une ligne par demande de crédit.
-- Les variables sensibles (statut_personnel_sexe, travailleur_etranger) sont exclues :
-- voir docs/model_card.md.
SELECT
    client_id,
    CASE statut_compte
        WHEN 'A11' THEN 'négatif'
        WHEN 'A12' THEN '0 à 200 DM'
        WHEN 'A13' THEN '200 DM et plus'
        ELSE 'pas de compte'
    END AS statut_compte,
    duree_mois,
    historique_credit,
    objet,
    montant,
    CASE epargne
        WHEN 'A61' THEN 'moins de 100 DM'
        WHEN 'A62' THEN '100 à 500 DM'
        WHEN 'A63' THEN '500 à 1000 DM'
        WHEN 'A64' THEN '1000 DM et plus'
        ELSE 'inconnue'
    END AS epargne,
    anciennete_emploi,
    taux_effort,
    autres_debiteurs,
    anciennete_residence,
    patrimoine,
    age,
    autres_credits,
    logement,
    nb_credits,
    emploi,
    nb_personnes_charge,
    telephone,
    CASE WHEN cible = 2 THEN 1 ELSE 0 END AS defaut
FROM demandes;
