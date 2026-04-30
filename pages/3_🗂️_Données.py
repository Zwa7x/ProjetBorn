import streamlit as st
from utils import load_data, save_data

st.title("🗂️ Gestion des données")

df = load_data()

edited_df = st.data_editor(df, num_rows="dynamic")

if st.button("💾 Enregistrer les modifications"):
    save_data(edited_df)
    st.success("Données mises à jour !")
