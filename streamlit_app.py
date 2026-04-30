import streamlit as st
import pandas as pd

st.title("🚗 Suivi de consommation voiture électrique")

df = pd.read_excel("data/CONSO_CUPRA.xlsx")
st.dataframe(df)
