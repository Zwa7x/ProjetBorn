import streamlit as st
import plotly.express as px
import pandas as pd
from utils import load_data

st.header("📊 Reporting")

df = load_data()

# --- FILTRES ---
st.subheader("🔍 Filtres")

regions = df["REGION"].dropna().unique()
lieux = df["LIEUX"].dropna().unique()

col1, col2 = st.columns(2)

with col1:
    region_filter = st.selectbox("Filtrer par région", ["Toutes"] + list(regions))

with col2:
    lieu_filter = st.selectbox("Filtrer par lieu", ["Tous"] + list(lieux))

df_filtered = df.copy()

if region_filter != "Toutes":
    df_filtered = df_filtered[df_filtered["REGION"] == region_filter]

if lieu_filter != "Tous":
    df_filtered = df_filtered[df_filtered["LIEUX"] == lieu_filter]

st.divider()

# --- INDICATEURS ---
st.subheader("📈 Indicateurs clés")

col1, col2, col3 = st.columns(3)

# Station la moins chère
cout_par_lieu = df_filtered.groupby("LIEUX")["Cout"].sum().sort_values()
if len(cout_par_lieu) > 0:
    col1.metric("Lieu le moins cher", cout_par_lieu.index[0], f"{cout_par_lieu.iloc[0]:.2f} €")

# Station la plus rapide
puissance_par_lieu = df_filtered.groupby("LIEUX")["Puissance"].mean().sort_values(ascending=False)
if len(puissance_par_lieu) > 0:
    col2.metric("Lieu le plus rapide", puissance_par_lieu.index[0], f"{puissance_par_lieu.iloc[0]:.1f} kW")

# Nombre de sessions
col3.metric("Nombre de sessions", len(df_filtered))

st.divider()

# --- GRAPHIQUE 1 : Évolution de la puissance ---
st.subheader("📉 Évolution de la puissance délivrée")

fig1 = px.line(
    df_filtered,
    x="Date",
    y="Puissance",
    title="Évolution de la puissance (kW)"
)

st.plotly_chart(fig1, use_container_width=True)

# --- GRAPHIQUE 2 : Coût total par lieu ---
st.subheader("💶 Coût total par lieu (tri décroissant)")

df_grouped = df_filtered.groupby("LIEUX")["Cout"].sum().sort_values(ascending=False).reset_index()

fig2 = px.bar(
    df_grouped,
    x="LIEUX",
    y="Cout",
    title="Coût total par lieu (€)"
)

st.plotly_chart(fig2, use_container_width=True)

# --- TOP 10 DONUT ---
st.subheader("🏆 Top 10 des lieux les plus utilisés")

top10 = df_filtered["LIEUX"].value_counts().head(10)

fig3 = px.pie(
    names=top10.index,
    values=top10.values,
    hole=0.5,
    title="Top 10 des lieux les plus utilisés"
)

st.plotly_chart(fig3, use_container_width=True)

# --- GRAPHIQUE MENSUEL ---
st.subheader("📅 Évolution mensuelle du coût")

df_filtered["Mois"] = df_filtered["Date"].dt.to_period("M").astype(str)

fig4 = px.line(
    df_filtered.groupby("Mois")["Cout"].sum().reset_index(),
    x="Mois",
    y="Cout",
    title="Coût total par mois (€)"
)

st.plotly_chart(fig4, use_container_width=True)
