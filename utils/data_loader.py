# utils/data_loader.py
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

def load_data():
    csv = DATA_DIR / "data.csv"
    if csv.exists():
        return pd.read_csv(csv)
    return pd.DataFrame()

def save_data(df):
    csv = DATA_DIR / "data.csv"
    df.to_csv(csv, index=False)
    return True
