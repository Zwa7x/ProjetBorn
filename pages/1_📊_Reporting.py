import streamlit as st
import plotly.express as px
from utils import load_data

st.title("📊 Reporting & Analyses")

df = load_data()

if len(df) == 0:
    st.warning("Aucune donnée disponible.")
    st.stop()

df["€/min"] = df["Cout"] / df["TEMPS en min"]

st.subheader("📈 Évolution des kWh chargés")
fig1 = px.line(df, x="Date", y="Puissance", title="Évolution de la puissance délivrée (kW)")
st.plotly_chart(fig, use_container_width=True)

st.subheader("💰 Coût par station")
fig2 = px.bar(df, x="Station", y="Cout", title="Coût total par station (€)")
st.plotly_chart(fig2, use_container_width=True)

st.subheader("🏆 Stations les plus économiques (€/kWh)")
fig3 = px.box(df, x="Station", y="€/kWh")
st.plotly_chart(fig3, use_container_width=True)
