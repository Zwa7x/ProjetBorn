# 1_📊_Reporting.py
import os
import streamlit as st
import pandas as pd
import unicodedata
import difflib
import plotly.express as px

st.set_page_config(page_title="Reporting", layout="wide")

# -------------------------
# Configuration
# -------------------------
DATA_PATH = "data/CONSO_CUPRA.xlsx"  # <-- Modifier ici vers votre fichier CSV ou XLSX

# -------------------------
# Fonctions utilitaires
# -------------------------
def read_data(path):
    if not os.path.exists(path):
        st.error(f"Fichier introuvable : {path}")
        return pd.DataFrame()
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".csv":
            # Ajuster sep et decimal si nécessaire
            df = pd.read_csv(path, sep=';', encoding='utf-8', decimal=',', dtype=str)
        elif ext in [".xls", ".xlsx"]:
            df = pd.read_excel(path, dtype=str)
        else:
            df = pd.read_csv(path, dtype=str)
    except Exception as e:
        st.error(f"Erreur lecture fichier : {e}")
        return pd.DataFrame()
    df.columns = df.columns.str.strip()
    return df

def normalize_colname(name):
    name = str(name).strip().lower()
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    name = " ".join(name.split())
    return name

def find_best_column(df_cols, target, cutoff=0.5):
    norm_cols = [normalize_colname(c) for c in df_cols]
    target_norm = normalize_colname(target)
    if target_norm in norm_cols:
        return df_cols[norm_cols.index(target_norm)]
    matches = difflib.get_close_matches(target_norm, norm_cols, n=3, cutoff=cutoff)
    if matches:
        return df_cols[norm_cols.index(matches[0])]
    return None

def clean_numeric_series(s):
    s = s.astype(str).str.replace('\xa0', ' ', regex=False)
    s = s.str.replace('€', '', regex=False)
    s = s.str.replace(',', '.', regex=False)
    s = s.str.strip()
    return pd.to_numeric(s, errors='coerce')

# -------------------------
# Lecture des données
# -------------------------
df = read_data(DATA_PATH)

# -------------------------
# Sidebar filtres professionnels
# -------------------------
st.sidebar.header("Filtres")
# Date range filter si colonne Date détectée
date_col = None
for c in df.columns:
    if normalize_colname(c) == "date":
        date_col = c
        break

# Candidate categorical columns for multiselect
candidate_cats = [c for c in df.columns if df[c].nunique(dropna=True) < 200 and df[c].nunique(dropna=True) > 1]
supplier_col = None
for cand in ["fournisseur", "provider", "vendeur", "operateur", "supplier"]:
    for c in candidate_cats:
        if normalize_colname(c) == cand:
            supplier_col = c
            break
    if supplier_col:
        break

# Sidebar widgets
if date_col:
    try:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        min_date = df[date_col].min()
        max_date = df[date_col].max()
        date_range = st.sidebar.date_input("Période", value=(min_date, max_date))
    except Exception:
        date_range = None
else:
    date_range = None

if supplier_col:
    suppliers = sorted(df[supplier_col].dropna().unique().tolist())
    selected_suppliers = st.sidebar.multiselect("Fournisseurs", options=suppliers, default=suppliers[:5])
else:
    selected_suppliers = None

# Checkbox pour afficher debug
show_debug_sidebar = st.sidebar.checkbox("Afficher debug", value=False)

# -------------------------
# Définition de df_filtered
# -------------------------
try:
    df_filtered = df.copy()
    if date_range and len(date_range) == 2:
        start, end = date_range
        if pd.notna(start) and pd.notna(end):
            df_filtered = df_filtered[(df_filtered[date_col] >= pd.to_datetime(start)) & (df_filtered[date_col] <= pd.to_datetime(end))]
    if supplier_col and selected_suppliers:
        df_filtered = df_filtered[df_filtered[supplier_col].isin(selected_suppliers)]
except Exception as e:
    st.error(f"Erreur lors de la définition de df_filtered : {e}")
    df_filtered = df.copy()

# -------------------------
# Debug rétractable professionnel
# -------------------------
with st.expander("🔧 Debug colonnes et aperçu", expanded=show_debug_sidebar):
    try:
        st.write("Nombre de lignes :", len(df_filtered))
        st.write("Colonnes disponibles :", df_filtered.columns.tolist())
        st.write("Aperçu des 5 premières lignes :", df_filtered.head())
    except Exception as e:
        st.error(f"Impossible d'afficher df_filtered: {e}")

# -------------------------
# Normalisation et recherche colonne prix
# -------------------------
# Construire mapping original -> normalisé
cols_orig = df_filtered.columns.tolist()
cols_norm = [normalize_colname(c) for c in cols_orig]
col_map = dict(zip(cols_norm, cols_orig))

# Chercher colonne prix
price_original = find_best_column(cols_orig, "Prix du KwH", cutoff=0.5)
if not price_original:
    # fallback: chercher colonne contenant 'prix' et 'kwh'
    for c in cols_orig:
        if "prix" in normalize_colname(c) and "kwh" in normalize_colname(c):
            price_original = c
            break

if price_original:
    st.sidebar.write(f"Colonne prix détectée : **{price_original}**")
else:
    st.sidebar.warning("Aucune colonne prix détectée automatiquement")

# Standardiser colonne prix dans df_filtered si trouvée
if price_original:
    try:
        df_filtered = df_filtered.rename(columns={price_original: "Prix du KwH"})
        price_col = "Prix du KwH"
    except Exception:
        price_col = price_original
else:
    price_col = None

# -------------------------
# Calculs principaux
# -------------------------
prix_kwh_global = None
if price_col and price_col in df_filtered.columns:
    s_num = clean_numeric_series(df_filtered[price_col])
    valid_count = s_num.notna().sum()
    if valid_count > 0:
        prix_kwh_global = s_num.mean()
    else:
        prix_kwh_global = None

# Affichage résumé
st.title("Reporting")
st.markdown("### Résumé rapide")
st.write({"prix_kwh_global": prix_kwh_global})

# -------------------------
# Visualisations interactives
# -------------------------
st.markdown("## Visualisations")

col_left, col_right = st.columns([2, 1])

# Graphique 1 Evolution temporelle
with col_left:
    st.markdown("### Évolution temporelle du prix kWh")
    if date_col and price_col and date_col in df_filtered.columns and price_col in df_filtered.columns:
        try:
            df_plot = df_filtered[[date_col, price_col]].copy()
            df_plot[price_col] = clean_numeric_series(df_plot[price_col])
            df_plot = df_plot.dropna(subset=[date_col, price_col]).sort_values(date_col)
            if not df_plot.empty:
                fig_ts = px.line(df_plot, x=date_col, y=price_col, title="Évolution du prix kWh", markers=True)
                fig_ts.update_layout(yaxis_title="Prix (€/kWh)", xaxis_title="Date")
                st.plotly_chart(fig_ts, use_container_width=True)
            else:
                st.info("Pas de données valides Date+Prix pour tracer l'évolution.")
        except Exception as e:
            st.error(f"Erreur graphique évolution temporelle : {e}")
    else:
        st.info("Colonne Date ou colonne Prix absente pour tracer l'évolution temporelle.")

# Graphique 2 Histogramme
with col_right:
    st.markdown("### Distribution des prix")
    if price_col and price_col in df_filtered.columns:
        try:
            s = clean_numeric_series(df_filtered[price_col]).dropna()
            if not s.empty:
                fig_hist = px.histogram(s, nbins=30, title="Distribution des prix kWh", labels={"value":"Prix (€/kWh)"})
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.info("Aucune valeur numérique valide dans la colonne prix pour l'histogramme.")
        except Exception as e:
            st.error(f"Erreur histogramme prix : {e}")
    else:
        st.info("Colonne prix introuvable pour l'histogramme.")

# Graphique 3 Boxplot par catégorie
st.markdown("### Boxplot par catégorie")
cat_col = None
preferred_cats = ["Fournisseur", "Type", "Categorie", "Contrat", "Statut"]
for pref in preferred_cats:
    for c in df_filtered.columns:
        if normalize_colname(c) == normalize_colname(pref):
            cat_col = c
            break
    if cat_col:
        break

if not cat_col:
    # fallback : choisir la première colonne catégorielle raisonnable
    for c in df_filtered.columns:
        if df_filtered[c].nunique(dropna=True) < 200 and df_filtered[c].nunique(dropna=True) > 1:
            cat_col = c
            break

if cat_col and price_col and price_col in df_filtered.columns:
    try:
        df_box = df_filtered[[cat_col, price_col]].copy()
        df_box[price_col] = clean_numeric_series(df_box[price_col])
        df_box = df_box.dropna()
        if not df_box.empty:
            fig_box = px.box(df_box, x=cat_col, y=price_col, points="outliers", title=f"Boxplot de {price_col} par {cat_col}")
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.info("Pas de données valides pour le boxplot.")
    except Exception as e:
        st.error(f"Erreur boxplot : {e}")
else:
    st.info("Colonne catégorielle ou colonne prix manquante pour le boxplot.")

# Graphique 4 Comptages top catégories
st.markdown("### Comptages")
if cat_col:
    try:
        counts = df_filtered[cat_col].value_counts().reset_index()
        counts.columns = [cat_col, "count"]
        fig_bar = px.bar(counts.head(20), x=cat_col, y="count", title=f"Top {min(20, len(counts))} {cat_col}", text="count")
        fig_bar.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)
    except Exception as e:
        st.error(f"Erreur bar chart : {e}")
else:
    st.info("Aucune colonne catégorielle détectée pour les comptages.")

# -------------------------
# Footer et conseils d'utilisation
# -------------------------
st.markdown("---")
st.markdown("**Conseils**")
st.markdown("- Modifiez `DATA_PATH` pour pointer vers votre fichier de données.")
st.markdown("- Activez `Afficher debug` dans la sidebar pour voir les colonnes et aperçus.")
st.markdown("- Installez plotly si nécessaire `pip install plotly` ou ajoutez au requirements.txt.")
