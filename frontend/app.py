"""Frontend Streamlit : affichage uniquement, toute la logique est dans backend.service.

Lancement (depuis la racine du dépôt) : python -m streamlit run frontend/app.py
"""
import pandas as pd
import streamlit as st

from backend import service

st.set_page_config(page_title="SEP Conseil : plein de la flotte", layout="wide")
st.title("SEP Conseil × Livraisons Exemple : aide au plein de la flotte")
st.caption(
    "Démonstrateur de formation, prix des carburants (Nord, Pas-de-Calais) et cours du Brent. "
    "Le gestionnaire garde la décision finale."
)


@st.cache_data
def stations() -> pd.DataFrame:
    return service.lister_stations()


try:
    metriques = service.metriques()
    table_stations = stations()
except FileNotFoundError:
    st.error("Modèle absent. Lancer d'abord : `python -m backend.train`")
    st.stop()

onglet_conseil, onglet_segments, onglet_modele = st.tabs(["Conseil de plein", "Segments", "Le modèle"])

with onglet_conseil:
    libelles = dict(zip(table_stations["station"], table_stations["ville"] + " — " + table_stations["adresse"]))
    station = st.selectbox("Station", list(libelles), format_func=libelles.get)
    jours = service.jours_disponibles(station)
    jour = st.selectbox("Jour", jours, index=len(jours) - 1 if jours else None)

    if jour is not None:
        try:
            conseil = service.conseiller(station, jour)
        except ValueError as erreur:
            st.warning(str(erreur))
        else:
            colonne_proba, colonne_prix = st.columns(2)
            colonne_proba.metric("Probabilité de hausse dans 3 jours", f"{conseil['proba_hausse']:.0%}")
            colonne_prix.metric("Prix du jour (€/L)", f"{conseil['prix']:.3f}")
            texte = f"Recommandation : {conseil['decision']} (seuil {conseil['seuil']:.0%})"
            if conseil["decision"] == service.DECISION_PLEIN:
                st.success(texte)
            else:
                st.warning(texte)

    st.subheader("Prix du Gazole de la station (€/L)")
    st.line_chart(service.historique_prix(station).set_index("jour")["prix"])
    st.caption(
        "Seuil issu des coûts mesurés sur l'entraînement. "
        "En usage réel, il faut le cours du Brent de la veille chaque matin."
    )

with onglet_segments:
    k = st.slider("Nombre de segments (K-means)", 2, 6, 3)
    st.dataframe(service.profils_segments(k), width="stretch")
    st.caption("Variables standardisées : prix relatif, changements par semaine, volatilité.")

with onglet_modele:
    st.subheader("Coût moyen par plein, c€/L de regret (jeu de test)")
    strategies = [
        ("Toujours faire le plein tout de suite (situation actuelle)", metriques["couts"]["toujours_plein"]),
        ("Toujours attendre 3 jours", metriques["couts"]["toujours_attendre"]),
        ("Modèle sans Brent, seuil tiré des coûts", metriques["modeles"]["sans_brent"]["cout_moyen_modele"]),
        ("Modèle avec Brent (veille), seuil 0,5", metriques["modeles"]["avec_brent"]["cout_moyen_seuil_05"]),
        ("Modèle avec Brent (veille), seuil tiré des coûts", metriques["modeles"]["avec_brent"]["cout_moyen_modele"]),
        ("Modèle avec Brent (8 jours de retard), seuil tiré des coûts",
         metriques["modeles"]["brent_realiste"]["cout_moyen_modele"]),
        ("Plafond : connaître l'avenir (oracle)", metriques["couts"]["oracle"]),
    ]
    tableau = pd.DataFrame(strategies, columns=["Stratégie", "Coût moyen (c€/L)"])
    tableau["Coût moyen (c€/L)"] = tableau["Coût moyen (c€/L)"].round(3)
    meilleure = strategies[4][0]
    st.dataframe(
        tableau.style.apply(
            lambda ligne: ["font-weight: bold" if ligne["Stratégie"] == meilleure else ""] * len(ligne), axis=1
        ),
        hide_index=True,
        width="stretch",
    )
    st.metric("Économie annuelle estimée (flotte fictive)", f"{metriques['economie_annuelle_euros']:,.0f} €".replace(",", " "))
    st.subheader("Importance par permutation, modèle avec Brent (baisse de ROC-AUC)")
    st.bar_chart(pd.Series(metriques["modeles"]["avec_brent"]["importance_permutation"]).head(8), width="stretch")
    st.subheader("Limites")
    st.markdown(
        "- Le Brent de la veille suppose un flux quotidien en usage réel.\n"
        "- Le scénario avec 8 jours de retard ne bat pas le modèle sans Brent.\n"
        "- Le gain par litre est petit, et plafonné par l'oracle.\n"
        "- La période de test tombe pendant la crise des prix de 2026.\n"
        "- Un saut des prix au 1er janvier a une cause non vérifiée.\n"
        "- Les volumes de la flotte sont fictifs.\n"
        "- Gazole uniquement.\n"
        "- Outil d'aide à la décision : le gestionnaire décide."
    )
