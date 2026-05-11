# pages/5_🛠️_Settings.py
import streamlit as st

st.set_page_config(page_title="Settings (safe)", layout="wide")
st.title("Settings - page de secours")

st.write("Cette page remplace temporairement la page Settings pour permettre le debug.")
if st.button("Afficher un test"):
    st.success("Bouton cliqué — l'app fonctionne.")
