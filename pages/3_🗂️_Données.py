import streamlit as st
from utils.data_loader import ingest_excel, load_table, load_all, save_table_upsert, _connect

st.set_page_config(page_title="Gestion des données", layout="wide")
st.title("📁 Gestion des données")

# --- extrait à coller dans pages/3_🗂️_Données.py (remplace la section ingestion) ---
st.subheader("Importer CONSO_CUPRA.xlsx")
uploaded = st.file_uploader("Importer CONSO_CUPRA.xlsx", type=["xlsx"])
if uploaded:
    tmp = "data/CONSO_CUPRA.xlsx"
    with open(tmp, "wb") as f:
        f.write(uploaded.getbuffer())
    if st.button("Ingest Excel (upsert)"):
        try:
            res = ingest_excel(tmp, mode="upsert")
            st.success("Ingestion terminée")
            st.subheader("Résumé d'ingestion")
            st.json(res)
            st.info("L'historique des imports est enregistré dans la table imports_log.")
        except Exception as e:
            st.error(f"Erreur d'ingestion: {e}")

# bouton pour afficher l'historique des imports
if st.checkbox("Afficher l'historique des imports (imports_log)"):
    try:
        # lecture simple de la table imports_log
        conn = _connect()
        df_log = pd.read_sql_query('SELECT * FROM "imports_log" ORDER BY import_id DESC LIMIT 100', conn)
        conn.close()
        if df_log.empty:
            st.info("Aucun import enregistré.")
        else:
            st.dataframe(df_log)
    except Exception as e:
        st.error(f"Impossible de lire imports_log: {e}")


# bouton de rechargement sûr (fallback si experimental_rerun absent)
def safe_rerun():
    if hasattr(st, "experimental_rerun"):
        try:
            st.experimental_rerun()
        except Exception:
            st.info("Impossible de forcer le rechargement automatiquement. Rechargez la page manuellement.")
    else:
        st.info("Votre version de Streamlit ne supporte pas st.experimental_rerun. Rechargez la page manuellement.")

if st.button("🔄 Recharger l'affichage"):
    safe_rerun()

# --- Tables et mapping ---
st.subheader("Tables importées")
all_tables = list(load_all().keys())
st.write("Tables détectées :", all_tables)

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

# --- Choix de la table à afficher (robuste) ---
# proposer d'abord des noms logiques, puis les tables détectées
suggested = ["mesures", "regions", "feuil1"]
candidates = [t for t in suggested if t in all_tables] + [t for t in all_tables if t not in suggested]
if not candidates:
    st.warning("Aucune table trouvée. Ingestez d'abord le fichier Excel.")
    st.stop()

table_choice = st.selectbox("Choisir une table à afficher", candidates, index=0)

# charger la table choisie (fallback : première table si nom non trouvé)
try:
    df = load_table(table_choice)
except Exception as e:
    st.warning(f"Table '{table_choice}' introuvable, tentative avec la première table détectée.")
    df = load_table(all_tables[0])

# --- Tableau éditable ---
st.subheader("Tableau éditable")
edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    if st.button("💾 Enregistrer les modifications"):
        res = save_table_upsert(table_choice, edited_df, mode="upsert")
        st.success(f"Sauvegarde terminée : {res}")
with col2:
    if st.button("🔄 Recharger le tableau"):
        safe_rerun()
