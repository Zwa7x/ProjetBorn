import pandas as pd
import os

DATA_PATH = "data/conso.csv"
EXCEL_PATH = "data/CONSO_CUPRA.xlsx"

def clean_columns(df):
    df = df.rename(columns={
        "DATE": "Date",
        "date": "Date",
        "STATION": "Station",
        "station": "Station",
        "DEBIT": "Puissance",
        "Puissance": "Puissance",
        "€": "Cout",
        "COUT": "Cout",
        "cout": "Cout",
        "Prix du KwH": "Prix_du_kWh",
        "Prix du KWh": "Prix_du_kWh",
        "Prix du kWh": "Prix_du_kWh",
        "Prix du KW/H": "Prix_du_kWh",
        "Prix du kW/h": "Prix_du_kWh"
    })

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], format="mixed", errors="coerce")

    if "Puissance" in df.columns:
        df["Puissance"] = pd.to_numeric(df["Puissance"], errors="coerce")

    if "Cout" in df.columns:
        df["Cout"] = pd.to_numeric(df["Cout"], errors="coerce")

    return df


def load_data():
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
    else:
        df = pd.read_excel(EXCEL_PATH)
        df = clean_columns(df)
        os.makedirs("data", exist_ok=True)
        df.to_csv(DATA_PATH, index=False)
    return df


def save_data(df):
    os.makedirs("data", exist_ok=True)
    df.to_csv(DATA_PATH, index=False)

print("EXCEL_PATH =", EXCEL_PATH)
print("Working directory =", os.getcwd())
print("Files in data =", os.listdir("data"))
