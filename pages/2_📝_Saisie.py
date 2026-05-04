import streamlit as st
from utils import load_data, save_data
import pandas as pd

st.title("📝 Ajouter une recharge")

df = load_data()

with st.form("add_form"):
    date = st.date_input("Date")
    station = st.text_input("Station")
    puissance = st.number_input("Puissance délivrée (kW)", min_value=0.0, max_value=500.0 step=0.1)
    cout = st.number_input("Coût (€)", min_value=0.0, step=0.1)
    submit = st.form_submit_button("Ajouter")

if submit:
    new_row = pd.DataFrame([{
        "Date": date,
        "Station": station,
        "Puissance": Puissance,
        "Cout": cout
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)
    st.success("Recharge ajoutée !")
