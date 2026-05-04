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
    df = df.rename(columns={
        "DATE": "Date",
        "STATION": "Station",
        "DEBIT": "Puissance",     # anciennement kWh
        "Puissance": "Puissance", # si déjà présent
        "€": "Cout",
        "COUT": "Cout",
        "cout": "Cout"
    })

    # Nettoyage des types
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], format="mixed", errors="coerce")

    if "Puissance" in df.columns:
        df["Puissance"] = pd.to_numeric(df["Puissance"], errors="coerce")

    if "Cout" in df.columns:
        df["Cout"] = pd.to_numeric(df["Cout"], errors="coerce")

    return df

def save_data(df):
    os.makedirs("data", exist_ok=True)
    df.to_csv(DATA_PATH, index=False)
