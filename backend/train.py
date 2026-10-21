"""Construit la base, entraîne les 2 modèles, choisit le modèle de la démo et sauvegarde.

Usage : python -m backend.train
"""
import json
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import cross_val_score

from backend.config import (
    ANNEES, DEPARTEMENTS, DOSSIER_HISTORIQUE, FICHIER_FLUX, FICHIER_METRIQUES, FICHIER_MODELE, FICHIER_TAUX,
    LITRES_PAR_AN, PLEINS_PAR_AN, RAYON_KM, REPORT_MAX_JOURS, TYPES_ZONE,
)
from backend.data import (
    ajouter_cible_et_variables, calculer_variables, charger_brut_dans_sqlite, enregistrer_table_analyse,
    executer_requete_analyse, lignes_du_jour, lire_stations,
)
from backend.download import chemin_archive, telecharger_tout
from backend.model import (
    CIBLE, MODELES, couts_moyens, couts_references, creer_pipeline, decouper_temporel, evaluer,
    evaluer_choix_station, intervalle_gain, plis_temporels, profils_stations, regret, regret_par_mois,
    regret_validation_croisee, seuil_optimal,
)


def fichiers_bruts_manquants() -> list:
    fichiers = [chemin_archive(annee, DOSSIER_HISTORIQUE) for annee in ANNEES] + [FICHIER_FLUX, FICHIER_TAUX]
    return [fichier for fichier in fichiers if not fichier.exists()]


def en_euros_par_an(gain_c_l: dict) -> dict:
    """Ajoute l'économie annuelle de la flotte fictive (€) à un gain moyen en c€/L."""
    return {**gain_c_l, "economie_annuelle_euros": gain_c_l["moyenne"] / 100 * LITRES_PAR_AN}


def qualite_reseau(stations: pd.DataFrame, grille: pd.DataFrame, jour_conseil: str) -> dict:
    """Diagnostic du périmètre : état du réseau le jour du conseil (flux) et trous de l'historique (grille)."""
    perimetre = stations[stations["departement"].isin(DEPARTEMENTS) & stations["zone"].isin(TYPES_ZONE)]
    age = (pd.Timestamp(jour_conseil) - pd.to_datetime(perimetre["maj_prix_jour"].str[:10])).dt.days
    historiques = grille["station"].drop_duplicates()
    return {
        "jour_conseil": jour_conseil,
        "stations_flux": int(len(perimetre)),
        "stations_fermees": int(perimetre["fermee"].sum()),
        "stations_en_rupture": int(perimetre["rupture"].sum()),
        "stations_sans_prix": int(perimetre["prix_jour"].isna().sum()),
        "stations_prix_perime": int((age > REPORT_MAX_JOURS).sum()),
        "stations_historique": int(len(historiques)),
        "stations_historique_absentes_du_flux": int((~historiques.isin(stations["station"])).sum()),
        "part_station_jour_sans_prix": float(grille["prix"].isna().mean()),
    }


def entrainer_modele(variables, entrainement, test, seuil: float) -> tuple:
    """AUC et regret en validation croisée temporelle sur l'entraînement, ajustement, évaluation sur le test.
    Renvoie le pipeline, ses métriques et le regret de chaque ligne de test (c€/L)."""
    pipeline = creer_pipeline()
    auc_cv = cross_val_score(
        pipeline, entrainement[variables], entrainement[CIBLE], cv=plis_temporels(entrainement["jour"]), scoring="roc_auc",
    )
    pipeline.fit(entrainement[variables], entrainement[CIBLE])
    resultat = evaluer(pipeline, test[variables], test[CIBLE], test["variation_future"], seuil)
    proba = pipeline.predict_proba(test[variables])[:, 1]
    regrets = regret(test["variation_future"], proba > seuil)
    regrets_plein = regret(test["variation_future"], np.ones(len(test), dtype=bool))
    resultat.update({
        "roc_auc_cv_moyenne": float(auc_cv.mean()),
        "roc_auc_cv_ecart_type": float(auc_cv.std()),
        "regret_cv": regret_validation_croisee(entrainement, variables),
        "part_plein_modele": float((proba > seuil).mean()),
        # Fiabilité des probabilités, dont dépend le seuil issu des coûts (diagnostic, non optimisé).
        "brier": float(brier_score_loss(test[CIBLE], proba)),
        "gain_vs_plein": en_euros_par_an(intervalle_gain(test["jour"], regrets_plein, regrets)),
    })
    return pipeline, resultat, regrets


def main() -> dict:
    if fichiers_bruts_manquants():
        telecharger_tout()
    comptes = charger_brut_dans_sqlite()
    jour_conseil = comptes["jour_conseil"]
    grille = executer_requete_analyse()
    table = ajouter_cible_et_variables(grille)
    enregistrer_table_analyse(table)
    enregistrer_table_analyse(lignes_du_jour(calculer_variables(grille), jour_conseil), nom="table_jour")

    entrainement, test = decouper_temporel(table)
    hausse_moyenne, baisse_moyenne = couts_moyens(entrainement["variation_future"], entrainement[CIBLE])
    seuil = seuil_optimal(hausse_moyenne, baisse_moyenne)

    modeles, pipelines, regrets = {}, {}, {}
    for nom, variables in MODELES.items():
        pipelines[nom], modeles[nom], regrets[nom] = entrainer_modele(variables, entrainement, test, seuil)
    # Modèle de la démo : le plus petit regret en validation croisée sur l'entraînement, jamais le test.
    retenu = min(modeles, key=lambda nom: modeles[nom]["regret_cv"])

    couts = couts_references(test["variation_future"])
    # Choix de la station : alternatives apprises sur l'entraînement, gain mesuré sur le test.
    prix_litre = float(test["prix"].median())
    stations = lire_stations()
    ecarts = profils_stations(entrainement)["prix_relatif"], profils_stations(test)["prix_relatif"]
    choix_station = {
        "rayon_km": RAYON_KM,
        "prix_litre": prix_litre,
        "avec_detour": evaluer_choix_station(stations, *ecarts, prix_litre, avec_detour=True),
        "sur_tournee": evaluer_choix_station(stations, *ecarts, prix_litre, avec_detour=False),
    }
    metriques = {
        "nb_stations": int(table["station"].nunique()),
        "nb_lignes_entrainement": int(len(entrainement)),
        "nb_lignes_test": int(len(test)),
        "debut_test": str(test["jour"].min()),
        "fin_test": str(test["jour"].max()),
        "taux_hausse": float(entrainement[CIBLE].mean()),
        "hausse_moyenne_c": hausse_moyenne,
        "baisse_moyenne_c": baisse_moyenne,
        "seuil": float(seuil),
        "litres_par_an": int(LITRES_PAR_AN),
        "pleins_par_an": int(PLEINS_PAR_AN),
        "chargement": comptes,
        "qualite": qualite_reseau(stations, grille, jour_conseil),
        "choix_station": choix_station,
        "couts": couts,
        "modeles": modeles,
        "modele_retenu": retenu,
        "economie_annuelle_euros": modeles[retenu]["gain_vs_plein"]["economie_annuelle_euros"],
        "regret_par_mois": regret_par_mois(test["jour"], {
            "toujours_plein": regret(test["variation_future"], np.ones(len(test), dtype=bool)), **regrets,
        }),
        # Ce qu'apporte le croisement avec le taux BCE au modèle qui ne voit que les prix.
        "valeur_taux_bce": en_euros_par_an(
            intervalle_gain(test["jour"], regrets["prix_seuls"], regrets["prix_et_taux"])
        ),
    }

    FICHIER_MODELE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipelines[retenu], FICHIER_MODELE)
    FICHIER_METRIQUES.write_text(json.dumps(metriques, indent=2, ensure_ascii=False), encoding="utf-8")
    return metriques


if __name__ == "__main__":
    debut = time.time()
    resultats = main()
    print(f"Test du {resultats['debut_test']} au {resultats['fin_test']} "
          f"({resultats['nb_lignes_test']} lignes), seuil {resultats['seuil']:.3f}")
    for nom, m in resultats["modeles"].items():
        print(f"{nom} : ROC-AUC test {m['roc_auc']:.3f} "
              f"(CV : {m['roc_auc_cv_moyenne']:.3f} ± {m['roc_auc_cv_ecart_type']:.3f}), "
              f"coût {m['cout_moyen_modele']:.3f} c€/L (seuil 0,5 : {m['cout_moyen_seuil_05']:.3f}), "
              f"regret CV {m['regret_cv']:.3f}, plein conseillé {m['part_plein_modele']:.1%} du temps")
    c = resultats["couts"]
    print(f"Coût moyen c€/L. Toujours plein : {c['toujours_plein']:.3f}, "
          f"toujours attendre : {c['toujours_attendre']:.3f}, oracle : {c['oracle']:.3f}")
    g = resultats["modeles"][resultats["modele_retenu"]]["gain_vs_plein"]
    v = resultats["valeur_taux_bce"]
    print(f"Modèle retenu (validation croisée) : {resultats['modele_retenu']}, économie annuelle "
          f"{g['economie_annuelle_euros']:.0f} € (gain {g['moyenne']:.2f} c€/L, IC 95 % {g['bas']:.2f} à {g['haut']:.2f})")
    print(f"Apport du taux BCE : {v['economie_annuelle_euros']:.0f} € "
          f"(gain {v['moyenne']:.2f} c€/L, IC 95 % {v['bas']:.2f} à {v['haut']:.2f})")
    print(f"Conseil du jour : {resultats['qualite']['jour_conseil']}")
    print(f"Modèle sauvegardé : {FICHIER_MODELE}")
    print(f"Durée : {time.time() - debut:.0f} s")
