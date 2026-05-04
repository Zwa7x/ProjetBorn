import streamlit as st
from utils import load_data

st.set_page_config(page_title="Suivi CUPRA Born", layout="wide")

st.title("Suivi de consommation – CUPRA Born")

df = load_data()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Nombre de recharges", len(df))

with col2:
    st.metric("Puissance totale (kW)", round(df["Puissance"].sum(), 2) if len(df) else 0)

with col3:
    st.metric("Coût total (€)", round(df["Cout"].sum(), 2) if len(df) else 0)

st.subheader("📄 Aperçu des données")
st.dataframe(df)
