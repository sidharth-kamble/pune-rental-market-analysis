"""
Cleaning pipeline: raw listings -> analysis-ready CSV.

Steps
1. Standardise text (locality names, furnishing)
2. Convert "₹ 25,000" / "850 sq.ft" / "Rs 1,20,000" strings to numbers
3. Remove duplicate listings
4. Handle missing values (documented choice per column)
5. Remove impossible values / outliers (IQR rule per BHK on rent per sq ft)
6. Feature engineering: rent_per_sqft, rent_band, listing_month, zone

Run:  python scripts/clean_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "pune_rental_raw.csv"
OUT = ROOT / "data" / "processed" / "pune_rental_clean.csv"
LOG = ROOT / "docs" / "cleaning_log.txt"

ZONES = {
    "Baner": "West", "Koregaon Park": "East", "Kalyani Nagar": "East", "Viman Nagar": "East",
    "Kharadi": "East", "Hadapsar": "East", "Wakad": "West", "Hinjewadi": "West",
    "Pimple Saudagar": "West", "Kothrud": "Central", "Karve Nagar": "Central", "Aundh": "West",
    "Bavdhan": "West", "Magarpatta": "East", "Katraj": "South", "Undri": "South",
    "Dhanori": "East", "Wagholi": "East",
}

log = []


def note(msg: str) -> None:
    print(msg)
    log.append(msg)


def to_number(series: pd.Series) -> pd.Series:
    """'₹ 1,20,000' / 'Rs 45,300' / '850 sq.ft' -> float."""
    cleaned = series.astype(str).str.replace(r"[^\d.]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


df = pd.read_csv(RAW)
note(f"Raw rows: {len(df):,}")

# 1. text standardisation
df["locality"] = df["locality"].str.strip().str.title()
df["furnishing"] = df["furnishing"].str.strip()
df["property_type"] = df["property_type"].str.strip()
df["parking"] = df["parking"].str.strip().str.title().map({"Yes": 1, "No": 0})

# 2. numeric conversion
for col in ["rent_inr", "deposit_inr", "area_sqft"]:
    df[col] = to_number(df[col])
df["listing_date"] = pd.to_datetime(df["listing_date"], errors="coerce")

# 3. duplicates
before = len(df)
df = df.drop_duplicates()
df = df.drop_duplicates(subset="listing_id")
note(f"Duplicates removed: {before - len(df):,}")

# 4. missing values
note("Missing values before treatment:\n" + df.isna().sum()[lambda s: s > 0].to_string())
df["furnishing"] = df["furnishing"].fillna("Unknown")
df["floor"] = df["floor"].fillna(df.groupby("locality")["floor"].transform("median"))
df["property_age_years"] = df["property_age_years"].fillna(
    df.groupby("locality")["property_age_years"].transform("median"))
df["bathrooms"] = df["bathrooms"].fillna(df["bhk"].clip(upper=3))
df = df.dropna(subset=["rent_inr", "area_sqft", "locality", "listing_date"])

# 5. impossible values + outliers
before = len(df)
df = df[(df["rent_inr"] >= 3000) & (df["area_sqft"] >= 200)]
note(f"Impossible rent/area rows removed: {before - len(df):,}")

df["rent_per_sqft"] = df["rent_inr"] / df["area_sqft"]
q1 = df.groupby("bhk")["rent_per_sqft"].transform(lambda s: s.quantile(0.25))
q3 = df.groupby("bhk")["rent_per_sqft"].transform(lambda s: s.quantile(0.75))
iqr = q3 - q1
mask = (df["rent_per_sqft"] >= q1 - 1.5 * iqr) & (df["rent_per_sqft"] <= q3 + 1.5 * iqr)
note(f"Statistical outliers removed (IQR rule per BHK): {(~mask).sum():,}")
df = df[mask].copy()

# 6. features
df["rent_per_sqft"] = df["rent_per_sqft"].round(2)
df["zone"] = df["locality"].map(ZONES).fillna("Other")
df["listing_month"] = df["listing_date"].dt.strftime("%Y-%m")
df["rent_band"] = pd.cut(
    df["rent_inr"], bins=[0, 15000, 25000, 40000, 70000, np.inf],
    labels=["<15k", "15-25k", "25-40k", "40-70k", "70k+"]).astype(str)
df["deposit_months"] = (df["deposit_inr"] / df["rent_inr"]).round(1)

for col in ["rent_inr", "deposit_inr", "area_sqft", "bhk", "floor", "property_age_years", "bathrooms"]:
    df[col] = df[col].round(0).astype(int)
df["listing_date"] = df["listing_date"].dt.strftime("%Y-%m-%d")

OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)
note(f"Clean rows saved: {len(df):,} -> {OUT.relative_to(ROOT)}")
LOG.parent.mkdir(exist_ok=True)
LOG.write_text("\n".join(log), encoding="utf-8")
