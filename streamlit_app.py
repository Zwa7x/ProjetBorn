import streamlit as st
from utils import load_data, save_data

from utils.data_loader import load_table, save_table_upsert

df = load_table("mesures")            # charge la table
# ... édition par l'utilisateur ...
save_result = save_table_upsert("mesures", edited_df, mode="upsert")
st.write(save_result)                 # affiche {"inserted": X, "skipped": Y}


st.set_page_config(page_title="Suivi de consommation – CUPRA Born", layout="wide")

st.title("Suivi de consommation – CUPRA Born")

df = load_data()

col1, col2, col3 = st.columns(3)

col1.metric("Nombre de recharges", len(df))
col2.metric("Puissance totale (kW)", round(df["Puissance"].sum(), 2))
col3.metric("Coût total (€)", round(df["Cout"].sum(), 2))

st.subheader("🏠 Accueil – Aperçu des données")
st.dataframe(df)

st.sidebar.subheader("🎨 Thème")
theme_choice = st.sidebar.radio("Choisir un thème :", ["Standard", "CUPRA"])

st.session_state.theme_cupra = (theme_choice == "CUPRA")

if st.sidebar.button("📄 Exporter le reporting en PDF"):
    st.session_state.export_pdf = True
