import pandas as pd
import os

DATA_PATH = "conso.csv"
EXCEL_SOURCE = "CONSO_CUPRA.xlsx"

def load_data():
    # Si le CSV existe → on le charge
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)

    # Sinon → on convertit l'Excel en CSV
    if os.path.exists(EXCEL_SOURCE):
        df = pd.read_excel(EXCEL_SOURCE)
        os.makedirs("data", exist_ok=True)
        df.to_csv(DATA_PATH, index=False)
        return df

    # Si rien n'existe → dataframe vide
    return pd.DataFrame(columns=["Date", "Station", "kWh", "Cout"])

def save_data(df):
    os.makedirs("data", exist_ok=True)
    df.to_csv(DATA_PATH, index=False)
