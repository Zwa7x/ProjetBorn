import streamlit as st
import pandas as pd

st.title("Suivi consommation CUPRA Born")

df = pd.read_excel("CONSO_CUPRA.xlsx")
st.dataframe(df)
