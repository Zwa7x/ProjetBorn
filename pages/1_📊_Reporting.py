# 1_📊_Reporting.py
# Script Streamlit pour reporting — version robuste pour éviter KeyError / NameError
import streamlit as st
import pandas as pd
import unicodedata
import difflib
import os

st.set_page_config(page_title="Reporting", layout="wide")

# -------------------------
# 1) Lecture du fichier source
# -------------------------
# Remplacez ce chemin par le vôtre ou adaptez la lecture (CSV/Excel)
DATA_PATH = "data/CONSO_CUPRA.xlsx"  # <-- modifier ici si besoin

def read_data(path):
    if not os.path.exists(path):
        st.error(f"Fichier introuvable : {path}")
        return pd.DataFrame()
    # Détecter extension
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext in [".csv"]:
            # Exemple pour CSV français : séparateur ; et décimale ,
            df = pd.read_csv(path, sep=';', encoding='utf-8', decimal=',', dtype=str)
        elif ext in [".xls", ".xlsx"]:
            df = pd.read_excel(path, dtype=str)
        else:
            # Tentative générique
            df = pd.read_csv(path, dtype=str)
    except Exception as e:
        st.error(f"Erreur lecture fichier : {e}")
        df = pd.DataFrame()
    # Nettoyage basique des noms de colonnes
    df.columns = df.columns.str.strip()
    return df

df = read_data(DATA_PATH)

# -------------------------
# 2) Définir df_filtered (adapter ici vos filtres)
# -------------------------
# Si vous avez déjà une logique de filtrage, collez-la ici.
# Par défaut on prend tout le DataFrame lu.
try:
    # --- APPLIQUEZ VOS FILTRES ICI ---
    # Exemple : df_filtered = df[df["Statut"] == "Valide"]
    # Si vous n'avez pas de filtre, on copie tout :
    df_filtered = df.copy()
except Exception as e:
    st.error(f"Erreur lors de la définition de df_filtered : {e}")
    df_filtered = df.copy()

# -------------------------
# 3) Debug : afficher colonnes et aperçu
# -------------------------
st.write("=== DEBUG : colonnes et aperçu du DataFrame ===")
try:
    st.write("Nombre de lignes :", len(df_filtered))
    st.write("Colonnes disponibles :", df_filtered.columns.tolist())
    st.write("Aperçu des 5 premières lignes :", df_filtered.head())
except Exception as e:
    st.error(f"Impossible d'afficher df_filtered: {e}")

# -------------------------
# 4) Normalisation des noms de colonnes et recherche de la colonne prix
# -------------------------
def normalize_colname(name):
    name = str(name).strip().lower()
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    name = " ".join(name.split())
    return name

# Construire mapping original <-> normalisé
cols_orig = df_filtered.columns.tolist()
cols_norm = [normalize_colname(c) for c in cols_orig]
col_map = dict(zip(cols_norm, cols_orig))

# Travailler sur une copie normalisée pour éviter surprises
df_norm = df_filtered.copy()
df_norm.columns = cols_norm

# Nom cible normalisé
target_norm = normalize_colname("Prix du KwH")

# Trouver la meilleure correspondance
col_to_use = None
if target_norm in df_norm.columns:
    col_to_use = target_norm
else:
    matches = difflib.get_close_matches(target_norm, df_norm.columns, n=3, cutoff=0.5)
    st.write("Nom cible normalisé :", target_norm)
    st.write("Correspondances proches trouvées :", matches)
    if matches:
        col_to_use = matches[0]
        st.info(f"Utilisation de la colonne approchante : '{col_to_use}' (nom original: '{col_map.get(col_to_use)}')")
    else:
        st.error("Colonne 'Prix du KwH' introuvable après normalisation. Vérifiez l'import ou le pré-traitement.")

# -------------------------
# 5) Conversion en numérique et calcul de la moyenne
# -------------------------
prix_kwh_global = None
if col_to_use:
    try:
        # Nettoyage des valeurs : remplacer virgule décimale, retirer symbole euro, espaces
        s = df_norm[col_to_use].astype(str).str.replace('\xa0', ' ', regex=False)
        s = s.str.replace('€', '', regex=False)
        s = s.str.replace(',', '.', regex=False)
        s = s.str.strip()
        # Conversion forcée en numérique
        s_num = pd.to_numeric(s, errors='coerce')
        valid_count = s_num.notna().sum()
        st.write(f"Nombre de valeurs numériques valides dans la colonne choisie : {valid_count}")
        if valid_count == 0:
            st.warning("Aucune valeur numérique valide trouvée dans la colonne prix. Vérifiez le format des données.")
        prix_kwh_global = s_num.mean()
        st.write("**Prix kWh moyen :**", prix_kwh_global)
    except Exception as e:
        st.error(f"Erreur lors du calcul du prix kWh : {e}")
else:
    st.warning("Calcul du prix kWh ignoré car aucune colonne correspondante n'a été trouvée.")

# -------------------------
# 6) Option : renommer définitivement la colonne dans df_filtered (si vous le souhaitez)
# -------------------------
# Exemple : si vous voulez standardiser le nom dans le DataFrame original
if col_to_use:
    original_name = col_map.get(col_to_use, col_to_use)
    # Renommer dans df_filtered original
    try:
        df_filtered = df_filtered.rename(columns={original_name: "Prix du KwH"})
        st.write("Colonne renommée en 'Prix du KwH' dans df_filtered.")
    except Exception as e:
        st.warning(f"Impossible de renommer la colonne : {e}")

# -------------------------
# 7) Export ou affichage final (exemples)
# -------------------------
st.markdown("### Résumé")
st.write({"prix_kwh_global": prix_kwh_global})
