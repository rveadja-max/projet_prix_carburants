"""Frontend Streamlit : affichage uniquement, toute la logique est dans backend.service.

Lancement (depuis la racine du dépôt) : python -m streamlit run frontend/app.py
"""
import pandas as pd
import streamlit as st

from backend import service

st.set_page_config(page_title="SEP Conseil : octroi de crédit", layout="wide")
st.title("SEP Conseil × Banque Exemple : aide à l'octroi de crédit")
st.caption("Démonstrateur de formation, dataset UCI German Credit. Le conseiller garde la décision finale.")


@st.cache_data
def demandes() -> pd.DataFrame:
    return service.lister_demandes()


try:
    metriques = service.metriques()
except FileNotFoundError:
    st.error("Modèle absent. Lancer d'abord : `python -m backend.train`")
    st.stop()

onglet_score, onglet_segments, onglet_modele = st.tabs(["Scorer une demande", "Segments", "Le modèle"])

with onglet_score:
    table = demandes()
    client_id = st.selectbox("Demande", table["client_id"])
    demande = table.set_index("client_id").loc[client_id].to_dict()

    colonne_saisie, colonne_resultat = st.columns(2)
    with colonne_saisie:
        demande["montant"] = st.slider("Montant (DM)", 250, 20000, int(demande["montant"]), step=250)
        demande["duree_mois"] = st.slider("Durée (mois)", 4, 72, int(demande["duree_mois"]))
        st.write(f"Compte courant : **{demande['statut_compte']}** · Épargne : **{demande['epargne']}** · Âge : **{demande['age']}**")

    resultat = service.scorer(demande)
    with colonne_resultat:
        st.metric("Probabilité de défaut", f"{resultat['proba_defaut']:.0%}")
        if resultat["decision"] == "refuser":
            st.error(f"Recommandation : étude approfondie (seuil {resultat['seuil']:.0%})")
        else:
            st.success(f"Recommandation : accorder (seuil {resultat['seuil']:.0%})")
        st.caption("Le seuil vient de la matrice de coûts : un défaut coûte 5 fois plus qu'un bon client refusé.")

with onglet_segments:
    k = st.slider("Nombre de segments (K-means)", 2, 6, 3)
    st.dataframe(service.profils_segments(k), use_container_width=True)
    st.caption("Variables standardisées : durée, montant, âge, taux d'effort.")

with onglet_modele:
    col1, col2, col3 = st.columns(3)
    col1.metric("ROC-AUC (test)", f"{metriques['roc_auc']:.2f}")
    col2.metric("Coût moyen, tout accepter", f"{metriques['cout_moyen_tout_accepter']:.2f}")
    col3.metric("Coût moyen, modèle", f"{metriques['cout_moyen_modele']:.2f}",
                delta=f"{metriques['cout_moyen_modele'] - metriques['cout_moyen_tout_accepter']:.2f}",
                delta_color="inverse")
    st.subheader("Importance par permutation (baisse de ROC-AUC)")
    st.bar_chart(pd.Series(metriques["importance_permutation"]).head(8))
