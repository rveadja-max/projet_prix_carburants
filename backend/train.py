"""Entraîne les 3 modèles, calcule le seuil et sauvegarde le modèle. Usage : python -m backend.train"""
import json
import time

import joblib
from sklearn.model_selection import cross_val_score

from backend.config import (
    ANNEES, DOSSIER_HISTORIQUE, FICHIER_BRENT, FICHIER_METRIQUES, FICHIER_MODELE, FICHIER_TAUX,
    LITRES_PAR_AN, PLEINS_PAR_AN, RAYON_KM,
)
from backend.data import charger_brut_dans_sqlite, enregistrer_table_analyse, lire_stations, lire_table_analyse
from backend.download import chemin_archive, telecharger_tout
from backend.model import (
    CIBLE, VARIABLES_AVEC_BRENT, VARIABLES_BRENT_REALISTE, VARIABLES_SANS_BRENT,
    couts_moyens, couts_references, creer_pipeline, decouper_temporel, evaluer, evaluer_choix_station,
    plis_temporels, profils_stations, seuil_optimal,
)

MODELES = {
    "sans_brent": VARIABLES_SANS_BRENT,
    "avec_brent": VARIABLES_AVEC_BRENT,
    "brent_realiste": VARIABLES_BRENT_REALISTE,
}


def fichiers_bruts_manquants() -> list:
    fichiers = [chemin_archive(annee, DOSSIER_HISTORIQUE) for annee in ANNEES] + [FICHIER_BRENT, FICHIER_TAUX]
    return [fichier for fichier in fichiers if not fichier.exists()]


def entrainer_modele(variables, entrainement, test, seuil: float) -> tuple:
    """AUC en validation croisée temporelle sur l'entraînement, ajustement, évaluation sur le test."""
    pipeline = creer_pipeline()
    auc_cv = cross_val_score(
        pipeline, entrainement[variables], entrainement[CIBLE], cv=plis_temporels(entrainement["jour"]), scoring="roc_auc",
    )
    pipeline.fit(entrainement[variables], entrainement[CIBLE])
    resultat = evaluer(pipeline, test[variables], test[CIBLE], test["variation_future"], seuil)
    proba = pipeline.predict_proba(test[variables])[:, 1]
    resultat.update({
        "roc_auc_cv_moyenne": float(auc_cv.mean()),
        "roc_auc_cv_ecart_type": float(auc_cv.std()),
        "part_plein_modele": float((proba > seuil).mean()),
    })
    return pipeline, resultat


def main() -> dict:
    if fichiers_bruts_manquants():
        telecharger_tout()
    charger_brut_dans_sqlite()
    table = lire_table_analyse()
    enregistrer_table_analyse(table)

    entrainement, test = decouper_temporel(table)
    hausse_moyenne, baisse_moyenne = couts_moyens(entrainement["variation_future"], entrainement[CIBLE])
    seuil = seuil_optimal(hausse_moyenne, baisse_moyenne)

    modeles, pipelines = {}, {}
    for nom, variables in MODELES.items():
        pipelines[nom], modeles[nom] = entrainer_modele(variables, entrainement, test, seuil)

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
        "choix_station": choix_station,
        "couts": couts,
        "modeles": modeles,
        "economie_annuelle_euros": float(
            (couts["toujours_plein"] - modeles["avec_brent"]["cout_moyen_modele"]) / 100 * LITRES_PAR_AN
        ),
    }

    FICHIER_MODELE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipelines["avec_brent"], FICHIER_MODELE)
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
              f"plein conseillé {m['part_plein_modele']:.1%} du temps")
    c = resultats["couts"]
    print(f"Coût moyen c€/L. Toujours plein : {c['toujours_plein']:.3f}, "
          f"toujours attendre : {c['toujours_attendre']:.3f}, oracle : {c['oracle']:.3f}")
    print(f"Économie annuelle (avec_brent vs toujours plein) : {resultats['economie_annuelle_euros']:.0f} €")
    print(f"Modèle sauvegardé : {FICHIER_MODELE}")
    print(f"Durée : {time.time() - debut:.0f} s")
