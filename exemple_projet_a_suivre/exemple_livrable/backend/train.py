"""Entraîne et sauvegarde le modèle. Usage : python -m backend.train"""
import json

import joblib
from sklearn.model_selection import cross_val_score, train_test_split

from backend.config import FICHIER_METRIQUES, FICHIER_MODELE, SEED
from backend.data import charger_brut_dans_sqlite, lire_table_analyse
from backend.model import CIBLE, VARIABLES, creer_pipeline, evaluer


def main() -> dict:
    nb_lignes = charger_brut_dans_sqlite()
    table = lire_table_analyse()
    X, y = table[VARIABLES], table[CIBLE]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=SEED,
    )

    pipeline = creer_pipeline()
    auc_cv = cross_val_score(pipeline, X_train, y_train, cv=5, scoring="roc_auc")
    pipeline.fit(X_train, y_train)

    metriques = evaluer(pipeline, X_test, y_test)
    metriques.update({
        "nb_demandes": nb_lignes,
        "taux_defaut": float(y.mean()),
        "roc_auc_cv_moyenne": float(auc_cv.mean()),
        "roc_auc_cv_ecart_type": float(auc_cv.std()),
    })

    FICHIER_MODELE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, FICHIER_MODELE)
    FICHIER_METRIQUES.write_text(json.dumps(metriques, indent=2, ensure_ascii=False), encoding="utf-8")
    return metriques


if __name__ == "__main__":
    resultats = main()
    print(f"ROC-AUC test : {resultats['roc_auc']:.3f} "
          f"(CV : {resultats['roc_auc_cv_moyenne']:.3f} ± {resultats['roc_auc_cv_ecart_type']:.3f})")
    print(f"Coût moyen par demande. Tout accepter : {resultats['cout_moyen_tout_accepter']:.3f}, "
          f"seuil 0,5 : {resultats['cout_moyen_seuil_05']:.3f}, "
          f"seuil {resultats['seuil']:.3f} : {resultats['cout_moyen_modele']:.3f}")
    print(f"Modèle sauvegardé : {FICHIER_MODELE}")
