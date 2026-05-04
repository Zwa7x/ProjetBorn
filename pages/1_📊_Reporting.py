import streamlit as st
import plotly.express as px
import pandas as pd
from utils import load_data

st.header("📊 Reporting")

df = load_data()

# --- FILTRES EN CASCADE ---
st.subheader("🔍 Filtres")

regions = df["REGION"].dropna().unique()
region_filter = st.selectbox("Région", ["Toutes"] + list(regions))

df_temp = df.copy()
if region_filter != "Toutes":
    df_temp = df_temp[df_temp["REGION"] == region_filter]

lieux = df_temp["LIEUX"].dropna().unique()
lieu_filter = st.selectbox("Lieu", ["Tous"] + list(lieux))

df_filtered = df_temp.copy()
if lieu_filter != "Tous":
    df_filtered = df_filtered[df_filtered["LIEUX"] == lieu_filter]

st.divider()

# --- INDICATEURS CLÉS ---
st.subheader("📈 Indicateurs clés")

col1, col2, col3 = st.columns(3)

# Lieu le moins cher (coût moyen)
cout_moyen = df_filtered.groupby("LIEUX")["Cout"].mean().sort_values()
if len(cout_moyen) > 0:
    col1.metric(
        "Lieu le moins cher (moyenne)",
        cout_moyen.index[0],
        f"{cout_moyen.iloc[0]:.2f} €"
    )

# Lieu le plus rapide (vitesse moyenne)
if "Vitesse km/min" in df_filtered.columns:
    vitesse_moyenne = df_filtered.groupby("LIEUX")["Vitesse km/min"].mean().sort_values(ascending=False)
    if len(vitesse_moyenne) > 0:
        col2.metric(
            "Lieu le plus rapide",
            vitesse_moyenne.index[0],
            f"{vitesse_moyenne.iloc[0]:.2f} km/min"
        )
else:
    col2.info("Colonne 'Vitesse km/min' absente.")

# Nombre de sessions
col3.metric("Nombre de sessions", len(df_filtered))

st.divider()

# --- TOP 10 MOINS CHÈRES (COÛT MOYEN) ---
st.subheader("💚 Top 10 des stations les moins chères (coût moyen)")

if len(cout_moyen) > 0:
    top10_low = cout_moyen.head(10)
    fig_low = px.pie(
        names=top10_low.index,
        values=top10_low.values,
        hole=0.5,
        title="Top 10 des stations les moins chères (coût moyen)"
    )
    st.plotly_chart(fig_low, use_container_width=True)
else:
    st.info("Pas assez de données pour ce graphique.")

# --- TOP 10 PLUS CHÈRES (COÛT MOYEN) ---
st.subheader("❤️ Top 10 des stations les plus chères (coût moyen)")

cout_moyen_high = df_filtered.groupby("LIEUX")["Cout"].mean().sort_values(ascending=False)
if len(cout_moyen_high) > 0:
    top10_high = cout_moyen_high.head(10)
    fig_high = px.pie(
        names=top10_high.index,
        values=top10_high.values,
        hole=0.5,
        title="Top 10 des stations les plus chères (coût moyen)"
    )
    st.plotly_chart(fig_high, use_container_width=True)
else:
    st.info("Pas assez de données pour ce graphique.")

# --- TOP 10 PLUS RAPIDES (VITESSE MOYENNE) ---
st.subheader("⚡ Top 10 des stations les plus rapides (vitesse moyenne)")

if "Vitesse km/min" in df_filtered.columns:
    vitesse_moyenne_full = df_filtered.groupby("LIEUX")["Vitesse km/min"].mean().sort_values(ascending=False)
    if len(vitesse_moyenne_full) > 0:
        top10_fast = vitesse_moyenne_full.head(10)
        fig_fast = px.pie(
            names=top10_fast.index,
            values=top10_fast.values,
            hole=0.5,
            title="Top 10 des stations les plus rapides (km/min)"
        )
        st.plotly_chart(fig_fast, use_container_width=True)
    else:
        st.info("Pas assez de données pour ce graphique.")
else:
    st.warning("La colonne 'Vitesse km/min' est absente du dataset.")

st.divider()

# --- COÛT TOTAL PAR LIEU (BAR CHART) ---
st.subheader("📊 Coût total par lieu (tri décroissant)")

df_grouped = df_filtered.groupby("LIEUX")["Cout"].sum().sort_values(ascending=False).reset_index()

if len(df_grouped) > 0:
    fig2 = px.bar(
        df_grouped,
        x="LIEUX",
        y="Cout",
        title="Coût total par lieu (€)"
    )
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Pas assez de données pour ce graphique.")

st.divider()

# --- ÉVOLUTION MENSUELLE DU COÛT ---
st.subheader("📅 Évolution mensuelle du coût")

# Sécurisation du type datetime
df_filtered["Date"] = pd.to_datetime(df_filtered["Date"], errors="coerce")
df_filtered = df_filtered.dropna(subset=["Date"])

if len(df_filtered) > 0:
    df_filtered["Mois"] = df_filtered["Date"].dt.to_period("M").astype(str)
    df_mois = df_filtered.groupby("Mois")["Cout"].sum().reset_index()

    fig4 = px.line(
        df_mois,
        x="Mois",
        y="Cout",
        title="Coût total par mois (€)"
    )
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.info("Pas assez de données datées pour afficher l'évolution mensuelle.")
