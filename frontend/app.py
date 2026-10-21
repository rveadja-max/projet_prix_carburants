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

onglet_conseil, onglet_segments, onglet_modele = st.tabs(["Décision", "Exploration", "Le modèle"])

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

    rayon = metriques["choix_station"]["rayon_km"]
    st.subheader(f"Stations moins chères à proximité (moins de {rayon:.0f} km)")
    proches = service.alternatives(station)
    if proches.empty:
        st.info("Aucune station proche ne fait gagner plus que le coût du détour : rester à cette station.")
    else:
        st.dataframe(
            proches.drop(columns="station").rename(columns={
                "ville": "Ville", "adresse": "Adresse", "distance_km": "Distance (km, vol d'oiseau)",
                "gain_c_l": "Moins chère de (c€/L)", "gain_plein_euros": "Gain net par plein (€)",
            }),
            hide_index=True, width="stretch",
        )
    st.caption(
        "Écarts de prix appris sur l'entraînement. Gain net = écart × 60 L − coût du détour aller-retour "
        "(carburant et temps du chauffeur, hypothèses dans backend/config.py)."
    )

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
    meilleure = strategies[2][0]  # le modèle utilisable aujourd'hui avec des données gratuites
    st.dataframe(
        tableau.style.apply(
            lambda ligne: ["font-weight: bold" if ligne["Stratégie"] == meilleure else ""] * len(ligne), axis=1
        ),
        hide_index=True,
        width="stretch",
    )

    def euros(valeur: float) -> str:
        return f"{valeur:,.0f} €".replace(",", " ")

    gain = metriques["modeles"]["sans_brent"]["gain_vs_plein"]
    brent = metriques["valeur_brent_veille"]
    colonne_gain, colonne_brent = st.columns(2)
    colonne_gain.metric("Économie annuelle, modèle sans Brent (flotte fictive)", euros(gain["economie_annuelle_euros"]))
    colonne_gain.caption(
        f"Intervalle de confiance à 95 % : {gain['bas']:.2f} à {gain['haut']:.2f} c€/L "
        "(bootstrap par semaines de la période de test)."
    )
    colonne_brent.metric("En plus avec le Brent de la veille (flux payant)", euros(brent["economie_annuelle_euros"]))
    colonne_brent.caption(
        f"Intervalle à 95 % : {brent['bas']:.2f} à {brent['haut']:.2f} c€/L. "
        "Un abonnement au cours quotidien ne vaut la peine que s'il coûte moins que ce gain."
    )
    st.subheader("Regret moyen par mois (c€/L, jeu de test)")
    mois = pd.DataFrame(metriques["regret_par_mois"]).rename(columns={
        "mois": "Mois", "nb_lignes": "Lignes", "toujours_plein": "Toujours plein", "sans_brent": "Sans Brent",
        "avec_brent": "Brent de la veille", "brent_realiste": "Brent à 8 jours",
    }).round(2)
    st.dataframe(mois, hide_index=True, width="stretch")
    st.caption("Le gain dépend de la phase du marché : un mois où le modèle dépasse « toujours plein » est un mois perdu.")

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
