import streamlit as st
import pandas as pd
from utils import load_data, save_data

st.header("📝 Ajouter une recharge")

with st.form("form_saisie"):
    date = st.date_input("Date")
    station = st.text_input("Station")

    puissance = st.number_input(
        "Puissance délivrée (kW)",
        min_value=0.0,
        step=0.1
    )

    cout = st.number_input(
        "Coût (€)",
        min_value=0.0,
        step=0.1
    )

    submit = st.form_submit_button("Ajouter")

if submit:
    df = load_data()

    new_row = {
        "Date": date,
        "Station": station,
        "Puissance": puissance,
        "Cout": cout
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df)

    st.success("Recharge ajoutée avec succès !")
