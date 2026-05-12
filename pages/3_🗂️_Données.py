import streamlit as st
from utils.data_loader import ingest_excel, load_table, load_all, save_table_upsert

st.set_page_config(page_title="Gestion des données", layout="wide")
st.title("📁 Gestion des données")

# --- Upload et ingestion (action utilisateur) ---
st.subheader("Importer CONSO_CUPRA.xlsx")
uploaded = st.file_uploader("Importer CONSO_CUPRA.xlsx", type=["xlsx"])
if uploaded:
    tmp = "data/CONSO_CUPRA.xlsx"
    with open(tmp, "wb") as f:
        f.write(uploaded.getbuffer())
    if st.button("Ingest Excel (upsert)"):
        try:
            ingest_excel(tmp, mode="upsert")
            st.success("Ingestion terminée")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Erreur d'ingestion: {e}")

# --- Tables et mapping ---
st.subheader("Tables importées")
tables = list(load_all().keys())
st.write("Tables détectées :", tables)

st.subheader("Mapping informatif (exemple)")
mapping_example = {
    "Feuil1": {"DATE": "date", "REGION": "region", "LIEUX": "lieux", "KW": "kw", "€": "cout"}
}
st.table(mapping_example)

st.subheader("Schéma relationnel (recommandé)")
st.markdown("""
- **sheet_feuil1** : id PK; date; region; lieux; debit; temps_en_min; kw; cout; prix_du_kwh; vitesse_kw_min; km_au_compteur; _row_hash
- Optionnel : séparer `regions` en table `regions(id, region, acronyme)` et référencer via `region_id`.
""")

# --- Choix de la table à afficher ---
table_choice = st.selectbox("Choisir une table à afficher", ["feuil1", "mesures", "regions"] + tables)
try:
    df = load_table(table_choice)
except Exception as e:
    st.error(f"Impossible de charger la table: {e}")
    st.stop()

# --- Tableau éditable ---
st.subheader("Tableau éditable")
edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    if st.button("💾 Enregistrer les modifications"):
        res = save_table_upsert(table_choice, edited_df, mode="upsert")
        st.success(f"Sauvegarde terminée : {res}")
with col2:
    if st.button("🔄 Recharger"):
        st.experimental_rerun()
