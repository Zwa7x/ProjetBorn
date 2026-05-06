# -------------------------
# Affichage professionnel : debug rétractable + graphiques
# -------------------------
import plotly.express as px

# Sidebar : contrôle d'affichage debug
show_debug_sidebar = st.sidebar.checkbox("Afficher le debug", value=False)

# Expander debug (fermé par défaut) + possibilité d'ouvrir depuis la sidebar
with st.expander("🔧 Debug (colonnes & aperçu)", expanded=show_debug_sidebar):
    try:
        st.write("Nombre de lignes :", len(df_filtered))
        st.write("Colonnes disponibles :", df_filtered.columns.tolist())
        st.write("Aperçu des 5 premières lignes :", df_filtered.head())
        # Afficher la série prix si elle existe
        if "Prix du KwH" in df_filtered.columns:
            st.write("Aperçu colonne Prix du KwH :", df_filtered["Prix du KwH"].head(10))
    except Exception as e:
        st.error(f"Impossible d'afficher le debug : {e}")

# Container principal pour les graphiques
st.markdown("## Visualisations")
charts_col1, charts_col2 = st.columns([2, 1])

# 1) Graphique 1 : évolution temporelle du prix (si colonne Date disponible)
with charts_col1:
    if "date" in [c.lower() for c in df_filtered.columns] or "Date" in df_filtered.columns:
        # trouver le nom exact de la colonne date (tolérance casse)
        date_col = None
        for c in df_filtered.columns:
            if c.lower() == "date":
                date_col = c
                break
        try:
            df_plot = df_filtered.copy()
            # convertir en datetime si possible
            df_plot[date_col] = pd.to_datetime(df_plot[date_col], errors='coerce')
            # choisir colonne prix existante
            price_col = None
            if "Prix du KwH" in df_plot.columns:
                price_col = "Prix du KwH"
            else:
                # chercher colonne contenant 'prix' et 'kwh' approximativement
                for c in df_plot.columns:
                    if "prix" in c.lower() and "kwh" in c.lower():
                        price_col = c
                        break
            if price_col:
                df_plot[price_col] = pd.to_numeric(df_plot[price_col].astype(str).str.replace(',', '.'), errors='coerce')
                df_ts = df_plot.dropna(subset=[date_col, price_col]).sort_values(date_col)
                if not df_ts.empty:
                    fig_ts = px.line(df_ts, x=date_col, y=price_col, title="Évolution du prix kWh dans le temps", markers=True)
                    fig_ts.update_layout(yaxis_title="Prix (€/kWh)", xaxis_title="Date")
                    st.plotly_chart(fig_ts, use_container_width=True)
                else:
                    st.info("Pas de données valides Date+Prix pour tracer l'évolution.")
            else:
                st.info("Aucune colonne prix détectée pour tracer l'évolution temporelle.")
        except Exception as e:
            st.error(f"Erreur graphique évolution temporelle : {e}")
    else:
        st.info("Colonne Date absente : impossible de tracer l'évolution temporelle.")

# 2) Graphique 2 : histogramme des prix
with charts_col2:
    price_col = None
    for c in df_filtered.columns:
        if c.lower() in ["prix du kwh", "prix du kwh", "prix du kwh".lower()]:
            price_col = c
            break
    if not price_col:
        # fallback : chercher colonne contenant 'prix' et 'kwh'
        for c in df_filtered.columns:
            if "prix" in c.lower() and "kwh" in c.lower():
                price_col = c
                break

    if price_col:
        try:
            s = df_filtered[price_col].astype(str).str.replace('\xa0', ' ', regex=False).str.replace('€', '', regex=False).str.replace(',', '.', regex=False).str.strip()
            s_num = pd.to_numeric(s, errors='coerce').dropna()
            if not s_num.empty:
                fig_hist = px.histogram(s_num, nbins=30, title="Distribution des prix kWh", labels={"value":"Prix (€/kWh)"})
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.info("Aucune valeur numérique valide dans la colonne prix pour l'histogramme.")
        except Exception as e:
            st.error(f"Erreur histogramme prix : {e}")
    else:
        st.info("Colonne prix introuvable pour l'histogramme.")

# 3) Graphique 3 : boxplot par catégorie (si colonne catégorielle disponible)
st.markdown("### Comparaison par catégorie")
cat_col = None
# Prioriser colonnes usuelles
for candidate in ["Fournisseur", "Type", "Categorie", "Contrat", "Statut"]:
    for c in df_filtered.columns:
        if c.lower() == candidate.lower():
            cat_col = c
            break
    if cat_col:
        break

if cat_col and price_col:
    try:
        df_box = df_filtered[[cat_col, price_col]].copy()
        df_box[price_col] = pd.to_numeric(df_box[price_col].astype(str).str.replace(',', '.'), errors='coerce')
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

# 4) Graphique 4 : counts / top fournisseurs (si cat_col présent)
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
