import streamlit as st
import plotly.express as px
from utils import load_data

st.title("📊 Reporting & Analyses")

df = load_data()

if len(df) == 0:
    st.warning("Aucune donnée disponible.")
    st.stop()

df["€/kWh"] = df["Cout"] / df["kWh"]

st.subheader("📈 Évolution des kWh chargés")
fig = px.line(df, x="Date", y="kWh")
st.plotly_chart(fig, use_container_width=True)

st.subheader("💰 Coût par station")
fig2 = px.bar(df, x="Station", y="Cout")
st.plotly_chart(fig2, use_container_width=True)

st.subheader("🏆 Stations les plus économiques (€/kWh)")
fig3 = px.box(df, x="Station", y="€/kWh")
st.plotly_chart(fig3, use_container_width=True)
