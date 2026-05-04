import streamlit as st
import pandas as pd
import os
from utils import load_data, save_data

st.header("📁 Gestion des données")

df = load_data()

# --- TABLEAU EDITABLE ---
st.subheader("📄 Tableau éditable")

edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True
)

col1, col2 = st.columns(2)

with col1:
    if st.button("💾 Enregistrer les modifications"):
        save_data(edited_df)
        st.success("Modifications enregistrées !")

with col2:
    if st.button("🔄 Recharger les données"):
        st.rerun()

st.divider()

# --- MENU D'ACTIONS AVANCÉES ---
st.subheader("⚙️ Actions avancées")

descriptions = {
    "Télécharger le CSV": "Télécharge le fichier CSV actuellement utilisé par l'application.",
    "Télécharger l'Excel": "Télécharge le fichier Excel d'origine (CONSO_CUPRA.xlsx).",
    "Importer un nouveau fichier Excel": "Importe un nouveau fichier Excel et régénère le CSV.",
    "Sauvegarder une copie du CSV": "Télécharge une copie du CSV comme sauvegarde.",
    "ADMIN - Supprimer le fichier CSV (forcer régénération)": "Supprime le CSV pour le recréer à partir de l'Excel."
}

actions = ["Aucune"] + list(descriptions.keys())

action = st.selectbox(
    "Choisir une action",
    actions
)

if action != "Aucune":
    st.caption(descriptions[action])

# --- ACTIONS ---
if action == "Télécharger le CSV":
    st.download_button(
        "📥 Télécharger conso.csv",
        data=df.to_csv(index=False),
        file_name="conso.csv",
        mime="text/csv"
    )

elif action == "Télécharger l'Excel":
    if os.path.exists("CONSO_CUPRA.xlsx"):
        with open("CONSO_CUPRA.xlsx", "rb") as f:
            st.download_button(
                "📥 Télécharger CONSO_CUPRA.xlsx",
                data=f,
                file_name="CONSO_CUPRA.xlsx"
            )
    else:
        st.error("Fichier Excel introuvable.")

elif action == "Importer un nouveau fichier Excel":
    uploaded = st.file_uploader("Importer un fichier Excel", type=["xlsx"])
    if uploaded:
        with open("CONSO_CUPRA.xlsx", "wb") as f:
            f.write(uploaded.getbuffer())
        st.success("Nouveau fichier Excel importé !")
        if os.path.exists("data/conso.csv"):
            os.remove("data/conso.csv")
        st.info("Le CSV sera régénéré automatiquement au prochain chargement.")
        st.rerun()

elif action == "Sauvegarder une copie du CSV":
    if os.path.exists("data/conso.csv"):
        with open("data/conso.csv", "rb") as f:
            st.download_button(
                "📥 Télécharger une copie du CSV",
                data=f,
                file_name="conso_backup.csv"
            )
    else:
        st.error("Aucun CSV à sauvegarder.")

elif action == "Supprimer le fichier CSV (forcer régénération)":
    if os.path.exists("data/conso.csv"):
        os.remove("data/conso.csv")
        st.success("CSV supprimé. Il sera recréé automatiquement à partir de l'Excel.")
        st.rerun()
    else:
        st.info("Aucun fichier CSV à supprimer.")
