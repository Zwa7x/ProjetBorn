# utils/helpers.py
import pandas as pd
import os

# Emplacements des fichiers
DATA_PATH = "data/conso.csv"
EXCEL_PATH = "data/CONSO_CUPRA.xlsx"

def clean_columns(df):
    """Nettoie et normalise les colonnes du fichier Excel/CSV."""
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

    # Conversions
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], format="mixed", errors="coerce")

    if "Puissance" in df.columns:
        df["Puissance"] = pd.to_numeric(df["Puissance"], errors="coerce")

    if "Cout" in df.columns:
        df["Cout"] = pd.to_numeric(df["Cout"], errors="coerce")

    return df


def load_data():
    """
    Charge les données :
    - si conso.csv existe → lecture CSV
    - sinon → lecture Excel + nettoyage + création du CSV
    """
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
        df = clean_columns(df)
    else:
        df = pd.read_excel(EXCEL_PATH)
        df = clean_columns(df)
        os.makedirs("data", exist_ok=True)
        df.to_csv(DATA_PATH, index=False)

    return df


def save_data(df):
    """Sauvegarde les données dans conso.csv."""
    os.makedirs("data", exist_ok=True)
    df.to_csv(DATA_PATH, index=False)

