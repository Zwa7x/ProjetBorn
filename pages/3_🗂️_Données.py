# pages/3_🗂️_Données.py
import streamlit as st
import pandas as pd
from utils.data_loader import (
    ingest_excel, load_table, load_all, save_table_upsert,
    export_db, import_db, DB_PATH, _connect
)

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
            res = ingest_excel(tmp, mode="upsert")
            st.success("Ingestion terminée")
            st.subheader("Résumé d'ingestion")
            st.json(res)
            st.info("L'historique des imports est enregistré dans la table imports_log.")
        except Exception as e:
            st.error(f"Erreur d'ingestion: {e}")

# safe rerun fallback
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
all_tables_raw = list(load_all(include_internal=True).keys())
# Exclure les tables internes SQLite
all_tables = [t for t in all_tables_raw if not t.startswith("sqlite_")]

if not all_tables:
    st.warning("Aucune table métier trouvée. Ingestez d'abord le fichier Excel.")
    with st.expander("Tables internes détectées (debug)"):
        st.write(all_tables_raw)
    st.stop()

st.write("Tables détectées :", all_tables)

st.subheader("Mapping informatif (exemple)")
mapping_example = {
    "Feuil1": {"DATE": "date", "REGION": "region", "LIEUX": "lieux", "KW": "kw", "€": "cout"}
}
st.table(mapping_example)

st.subheader("Schéma relationnel (vue graphique)")
dot = """
digraph schema {
  rankdir=LR;
  node [shape=record, fontsize=10];

  mesures [label="{mesures|id PK\\ldate\\lkw\\lcout\\ltemps_min\\llieu_id FK\\limport_id FK\\l_row_hash\\l}"];
  lieux   [label="{lieux|id PK\\lnom\\lregion_id FK\\ltype\\llatitude\\llongitude\\l}"];
  regions [label="{regions|id PK\\lcode\\lnom\\l}"];
  imports [label="{imports_log|import_id PK\\lsource_file\\lts\\lrows_total\\linserted\\l}"];

  lieux -> regions [label=" region_id "];
  mesures -> lieux [label=" lieu_id "];
  mesures -> imports [label=" import_id "];
}
"""
st.graphviz_chart(dot)

# --- Choix de la table à afficher ---
table_choice = st.selectbox("Choisir une table à afficher", all_tables)

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
        try:
            res = save_table_upsert(table_choice, edited_df, mode="upsert")
            st.success(f"Sauvegarde terminée : {res}")
        except Exception as e:
            st.error(f"Erreur sauvegarde: {e}")
with col2:
    if st.button("🔄 Recharger le tableau"):
        safe_rerun()

# --- Backup / Restore DB ---
st.subheader("Sauvegarde / Restauration de la base")
st.info(f"DB path: {DB_PATH}")
st.write("DB existe :", DB_PATH.exists())
if DB_PATH.exists():
    st.write("Taille (bytes) :", DB_PATH.stat().st_size)

if st.button("Créer un backup local (.db) et proposer le téléchargement"):
    try:
        backup_path = export_db()
        with open(backup_path, "rb") as f:
            st.download_button("Télécharger le fichier .db", data=f, file_name=backup_path.split("/")[-1])
    except Exception as e:
        st.error(f"Erreur backup: {e}")

uploaded_db = st.file_uploader("Restaurer depuis un fichier .db", type=["db"])
if uploaded_db is not None:
    tmp = "data/uploaded_restore.db"
    with open(tmp, "wb") as f:
        f.write(uploaded_db.getbuffer())
    if st.button("Restaurer la DB depuis l'upload"):
        try:
            import_db(tmp)
            st.success("Restauration terminée. Rechargez la page pour voir les changements.")
        except Exception as e:
            st.error(f"Erreur restauration: {e}")

# --- Afficher historique imports_log ---
if st.checkbox("Afficher l'historique des imports (imports_log)"):
    try:
        conn = _connect()
        df_log = pd.read_sql_query('SELECT * FROM "imports_log" ORDER BY import_id DESC LIMIT 200', conn)
        conn.close()
        if df_log.empty:
            st.info("Aucun import enregistré.")
        else:
            st.dataframe(df_log)
    except Exception as e:
        st.error(f"Impossible de lire imports_log: {e}")
