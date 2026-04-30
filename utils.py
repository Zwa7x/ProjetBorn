import pandas as pd
import os

DATA_PATH = "data/conso.csv"
EXCEL_SOURCE = "CONSO_CUPRA.xlsx"

def load_data():
    # Si le CSV existe → on le charge
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
        return clean_columns(df)

    # Sinon → on convertit l'Excel en CSV
    if os.path.exists(EXCEL_SOURCE):
        df = pd.read_excel(EXCEL_SOURCE)

        # Renommage automatique des colonnes
        df = clean_columns(df)

        os.makedirs("data", exist_ok=True)
        df.to_csv(DATA_PATH, index=False)
        return df

    # Si rien n'existe → dataframe vide
    return pd.DataFrame(columns=["Date", "Station", "kWh", "Cout"])

def clean_columns(df):
    # Normalisation des noms de colonnes
    df = df.rename(columns={
        "DATE": "Date",
        "date": "Date",
        "STATION": "Station",
        "station": "Station",
        "DEBIT": "kWh",
        "kwh": "kWh",
        "€": "Cout",
        "COUT": "Cout",
        "cout": "Cout"
    })

    # Conversion des types
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], format="mixed", errors="coerce")

    if "kWh" in df.columns:
        df["kWh"] = pd.to_numeric(df["kWh"], errors="coerce")

    if "Cout" in df.columns:
        df["Cout"] = pd.to_numeric(df["Cout"], errors="coerce")

    return df

def save_data(df):
    os.makedirs("data", exist_ok=True)
    df.to_csv(DATA_PATH, index=False)
