import streamlit as st
import pandas as pd
from utils import load_data, save_data

st.header("📁 Gestion des données")

df = load_data()

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

st.info("Vous pouvez ajouter, modifier ou supprimer des lignes directement dans le tableau.")

