"""Frontend Streamlit : affichage uniquement, toute la logique est dans backend.service.

Lancement (depuis la racine du dépôt) : python -m streamlit run frontend/app.py
"""
import pandas as pd
import streamlit as st

from backend import service

# Couleurs de la carte (affichage seulement) : l'état de chaque station vient de backend.service.
COULEURS_ETAT = {
    "ouverte": "#2e7d32", "prix absent ou périmé": "#9e9e9e", "rupture de gazole": "#ef6c00", "fermée": "#c62828",
}

st.set_page_config(page_title="SEP Conseil : plein de la flotte", layout="wide")
st.title("SEP Conseil × Livraisons Exemple : aide au plein de la flotte")
st.caption(
    "Démonstrateur de formation. Sources : flux quotidien des prix des carburants (data.gouv.fr) et taux "
    "EUR/USD de la BCE, Nord et Pas-de-Calais, gazole. Le gestionnaire garde la décision finale."
)


@st.cache_data
def stations() -> pd.DataFrame:
    return service.lister_stations()


def euros(valeur: float) -> str:
    return f"{valeur:,.0f} €".replace(",", " ")


try:
    metriques = service.metriques()
    table_stations = stations()
except FileNotFoundError:
    st.error("Modèle absent. Lancer d'abord : `python -m backend.train`")
    st.stop()

onglet_decision, onglet_exploration, onglet_modele = st.tabs(["Décision", "Exploration", "Le modèle"])

with onglet_decision:
    libelles = dict(zip(table_stations["station"], table_stations["ville"] + " — " + table_stations["adresse"]))
    station = st.selectbox("Station habituelle de la tournée", list(libelles), format_func=libelles.get)
    etat = service.etat_station(station)

    st.subheader(f"Conseil du {etat['jour_conseil']}")
    if etat["fermee"]:
        st.error("Station fermée aujourd'hui selon le flux : choisir une station proche ci-dessous.")
    if etat["rupture"]:
        st.error("Rupture de gazole déclarée dans cette station : choisir une station proche ci-dessous.")
    try:
        conseil = service.conseil_du_jour(station)
    except ValueError as erreur:
        st.warning(str(erreur))
    else:
        colonne_proba, colonne_prix, colonne_taux = st.columns(3)
        colonne_proba.metric("Probabilité de hausse dans 3 jours", f"{conseil['proba_hausse']:.0%}")
        colonne_prix.metric("Prix connu à midi (€/L)", f"{conseil['prix']:.3f}")
        colonne_taux.metric("Euro en dollars (BCE, veille)", f"{conseil['taux']:.4f}")
        texte = f"Recommandation : {conseil['decision']} (seuil {conseil['seuil']:.0%}, modèle {conseil['modele']})"
        if conseil["decision"] == service.DECISION_PLEIN:
            st.success(texte)
        else:
            st.warning(texte)
    if etat["prix_jour"] is not None:
        st.caption(f"Dernier prix publié dans le flux : {etat['prix_jour']:.3f} €/L le {etat['maj_prix_jour']}. "
                   f"Automate 24 h/24 : {'oui' if etat['automate_24_24'] else 'non'}.")

    rayon = metriques["choix_station"]["rayon_km"]
    st.subheader(f"Stations moins chères aujourd'hui à proximité (moins de {rayon:.0f} km)")
    proches = service.alternatives(station)
    if proches.empty:
        st.info("Aucune station proche ne fait gagner plus que le coût du détour : rester à cette station.")
    else:
        st.dataframe(
            proches.drop(columns="station").rename(columns={
                "ville": "Ville", "adresse": "Adresse", "prix_jour": "Prix du jour (€/L)",
                "distance_km": "Distance (km, vol d'oiseau)", "gain_c_l": "Moins chère de (c€/L)",
                "gain_plein_euros": "Gain net par plein (€)",
            }),
            hide_index=True, width="stretch",
        )
    st.caption(
        "Prix du jour du flux, stations ouvertes et sans rupture seulement. Gain net = écart × 60 L − coût du "
        "détour aller-retour (carburant et temps du chauffeur, hypothèses dans backend/config.py)."
    )

    with st.expander("Rejouer un jour de la période de test"):
        jours = service.jours_disponibles(station)
        jour = st.selectbox("Jour", jours, index=len(jours) - 1 if jours else None)
        if jour is not None:
            passe = service.conseiller(station, jour)
            st.write(f"Le {jour} : probabilité de hausse {passe['proba_hausse']:.0%}, "
                     f"prix {passe['prix']:.3f} €/L, recommandation : **{passe['decision']}**.")
        st.line_chart(service.historique_prix(station).set_index("jour")["prix"],
                      alt="Prix du gazole de la station sur la période de test")

with onglet_exploration:
    q = service.qualite()
    st.subheader(f"Réseau du Nord et du Pas-de-Calais le {q['jour_conseil']} (flux quotidien)")
    colonnes = st.columns(4)
    colonnes[0].metric("Stations du flux", q["stations_flux"])
    colonnes[1].metric("Fermées", q["stations_fermees"])
    colonnes[2].metric("En rupture de gazole", q["stations_en_rupture"])
    colonnes[3].metric("Prix absent ou périmé", q["stations_sans_prix"] + q["stations_prix_perime"])
    carte = service.carte_reseau()
    st.map(carte.assign(couleur=carte["etat"].map(COULEURS_ETAT)), latitude="latitude", longitude="longitude",
           color="couleur", size=150, alt="Stations-service du périmètre colorées selon leur état du jour")
    st.caption("Vert : ouverte · gris : prix absent ou périmé · orange : rupture de gazole · rouge : fermée.")

    st.subheader("Croisement des deux sources : gazole et euro/dollar (indice 100 au premier jour)")
    st.line_chart(service.serie_marche().set_index("jour").rename(columns={
        "gazole": "Gazole, prix médian", "euro_dollar": "Euro en dollars (BCE)",
    }), alt="Prix médian du gazole et taux euro-dollar, en indice")
    st.caption("Un euro plus fort rend le pétrole, payé en dollars, moins cher en euros : le modèle teste si "
               "les variations du taux aident à prévoir celles du prix à la pompe.")

    st.subheader("Historique : trous des séries par station")
    st.write(f"{q['stations_historique']} stations ont publié des prix dans le périmètre depuis 2025, dont "
             f"{q['stations_historique_absentes_du_flux']} absentes du flux du jour (fermées ou disparues). "
             f"{q['part_station_jour_sans_prix']:.0%} des couples station × jour n'ont pas de prix de moins de 7 jours.")

    st.subheader("Segments de stations (K-means)")
    k = st.slider("Nombre de segments", 2, 6, 3)
    st.dataframe(service.profils_segments(k), width="stretch")
    st.caption("Variables standardisées : prix relatif à la médiane du département (c€/L), changements de "
               "prix par semaine, volatilité (c€/L).")

with onglet_modele:
    retenu = metriques["modele_retenu"]
    modeles = metriques["modeles"]
    st.subheader("Coût moyen par plein, c€/L de regret (jeu de test)")
    strategies = [
        ("Toujours faire le plein tout de suite (situation actuelle)", metriques["couts"]["toujours_plein"]),
        ("Toujours attendre 3 jours", metriques["couts"]["toujours_attendre"]),
        ("Modèle prix seuls, seuil tiré des coûts", modeles["prix_seuls"]["cout_moyen_modele"]),
        ("Modèle prix + taux BCE, seuil 0,5", modeles["prix_et_taux"]["cout_moyen_seuil_05"]),
        ("Modèle prix + taux BCE, seuil tiré des coûts", modeles["prix_et_taux"]["cout_moyen_modele"]),
        ("Plafond : connaître l'avenir (oracle)", metriques["couts"]["oracle"]),
    ]
    tableau = pd.DataFrame(strategies, columns=["Stratégie", "Coût moyen (c€/L)"])
    tableau["Coût moyen (c€/L)"] = tableau["Coût moyen (c€/L)"].round(3)
    meilleure = strategies[2][0] if retenu == "prix_seuls" else strategies[4][0]
    st.dataframe(
        tableau.style.apply(
            lambda ligne: ["font-weight: bold" if ligne["Stratégie"] == meilleure else ""] * len(ligne), axis=1
        ),
        hide_index=True,
        width="stretch",
    )
    st.caption(f"En gras : le modèle de la démo ({service.NOMS_MODELES[retenu]}), choisi sur le plus petit "
               "regret en validation croisée temporelle de l'entraînement, sans regarder le test.")

    gain = modeles[retenu]["gain_vs_plein"]
    bce = metriques["valeur_taux_bce"]
    colonne_gain, colonne_bce = st.columns(2)
    colonne_gain.metric(f"Économie annuelle, modèle {service.NOMS_MODELES[retenu]} (flotte fictive)",
                        euros(gain["economie_annuelle_euros"]))
    colonne_gain.caption(
        f"Intervalle de confiance à 95 % : {gain['bas']:.2f} à {gain['haut']:.2f} c€/L "
        "(bootstrap par semaines de la période de test)."
    )
    colonne_bce.metric("Apport du taux BCE au modèle prix seuls", euros(bce["economie_annuelle_euros"]))
    colonne_bce.caption(f"Intervalle à 95 % : {bce['bas']:.2f} à {bce['haut']:.2f} c€/L.")

    st.subheader("Regret moyen par mois (c€/L, jeu de test)")
    mois = pd.DataFrame(metriques["regret_par_mois"]).rename(columns={
        "mois": "Mois", "nb_lignes": "Lignes", "toujours_plein": "Toujours plein",
        "prix_seuls": "Prix seuls", "prix_et_taux": "Prix + taux BCE",
    }).round(2)
    st.dataframe(mois, hide_index=True, width="stretch")
    st.caption("Le gain dépend de la phase du marché : un mois où le modèle dépasse « toujours plein » est un mois perdu.")

    st.subheader("Importance par permutation, modèle prix + taux BCE (baisse de ROC-AUC)")
    st.bar_chart(pd.Series(modeles["prix_et_taux"]["importance_permutation"]).head(8), width="stretch",
                 alt="Variables les plus utiles au modèle prix plus taux BCE")
    st.subheader("Limites")
    st.markdown(
        "- Le flux data.gouv.fr est une photo du jour, sans historique : l'historique vient des archives "
        "annuelles du même producteur.\n"
        "- Le conseil du jour suppose de relancer `python -m backend.download --forcer` puis "
        "`python -m backend.train` chaque matin.\n"
        "- Le gain par litre est petit, et plafonné par l'oracle.\n"
        "- La période de test tombe pendant la crise des prix de 2026.\n"
        "- Les volumes de la flotte et les coûts de détour sont fictifs.\n"
        "- Gazole uniquement.\n"
        "- Outil d'aide à la décision : le gestionnaire décide."
    )
