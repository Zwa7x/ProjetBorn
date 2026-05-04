import streamlit as st
from utils import load_data

st.header("📁 Données")

df = load_data()

st.dataframe(df)
