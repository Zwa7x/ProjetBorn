import streamlit as st
from utils import load_data, save_data
import pandas as pd

st.title("📝 Ajouter une recharge")

df = load_data()

with st.form("add_form"):
    date = st.date_input("Date")
    station = st.text_input("Station")
    kwh = st.number_input("kWh chargés", min_value=0.0)
    cout = st.number_input("Coût (€)", min_value=0.0)
    submit = st.form_submit_button("Ajouter")

if submit:
    new_row = pd.DataFrame([{
        "Date": date,
        "Station": station,
        "kWh": kwh,
        "Cout": cout
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)
    st.success("Recharge ajoutée !")
