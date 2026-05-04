import streamlit as st
import plotly.express as px
from utils import load_data

st.header("📊 Reporting")

df = load_data()

# Graphique 1 : évolution de la puissance
fig1 = px.line(
    df,
    x="Date",
    y="Puissance",
    title="Évolution de la puissance délivrée (kW)"
)

st.plotly_chart(fig1, use_container_width=True)

# Graphique 2 : coût par station
fig2 = px.bar(
    df,
    x="Station",
    y="Cout",
    title="Coût total par station (€)"
)

st.plotly_chart(fig2, use_container_width=True)
