"""
Generate a SAMPLE raw Pune rental-listings file (deliberately messy).

IMPORTANT: this data is SIMULATED so the pipeline can run end to end.
Replace data/raw/pune_rental_raw.csv with REAL listings (a Kaggle housing
dataset or your own collection) before you quote any numbers on your CV.
Locality price levels below are illustrative assumptions, not market facts.
"""
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
N = 6000

# locality: (base rent per sq ft, zone)
LOCALITIES = {
    "Baner": (34, "West"), "Koregaon Park": (42, "East"), "Kalyani Nagar": (38, "East"),
    "Viman Nagar": (33, "East"), "Kharadi": (30, "East"), "Hadapsar": (24, "East"),
    "Wakad": (27, "West"), "Hinjewadi": (26, "West"), "Pimple Saudagar": (22, "West"),
    "Kothrud": (31, "Central"), "Karve Nagar": (25, "Central"), "Aundh": (35, "West"),
    "Bavdhan": (28, "West"), "Magarpatta": (32, "East"), "Katraj": (18, "South"),
    "Undri": (19, "South"), "Dhanori": (21, "East"), "Wagholi": (17, "East"),
}
WEIGHTS = np.array([5, 3, 3, 5, 6, 6, 8, 9, 6, 6, 6, 4, 3, 3, 4, 4, 4, 5], dtype=float)
WEIGHTS /= WEIGHTS.sum()
BHK_AREA = {1: (450, 700), 2: (750, 1100), 3: (1150, 1650), 4: (1700, 2600)}
FURN_MULT = {"Unfurnished": 1.00, "Semi-Furnished": 1.10, "Furnished": 1.22}
PROP_TYPES = ["Apartment", "Apartment", "Apartment", "Independent House", "Builder Floor"]

names = list(LOCALITIES)
rows = []
for i in range(N):
    loc = rng.choice(names, p=WEIGHTS)
    base, _zone = LOCALITIES[loc]
    bhk = int(rng.choice([1, 2, 3, 4], p=[0.20, 0.45, 0.28, 0.07]))
    lo, hi = BHK_AREA[bhk]
    area = int(rng.integers(lo, hi))
    furn = str(rng.choice(list(FURN_MULT), p=[0.35, 0.40, 0.25]))
    age = int(rng.integers(0, 20))
    floor = int(rng.integers(0, 22))
    parking = int(rng.random() < 0.7)
    ptype = str(rng.choice(PROP_TYPES))
    ppsf = base * FURN_MULT[furn] * (1 - 0.006 * age) * (1 + 0.004 * min(floor, 15))
    ppsf *= rng.normal(1.0, 0.08)
    rent = max(5000, int(round(ppsf * area, -2)))
    deposit = int(rent * rng.choice([2, 3, 4, 5, 6], p=[0.15, 0.30, 0.25, 0.20, 0.10]))
    month = int(rng.integers(1, 13))
    day = int(rng.integers(1, 28))
    baths = min(bhk, int(rng.integers(1, bhk + 2)))
    rows.append([f"PUN{100000 + i}", loc, bhk, area, furn, rent, deposit, floor, age,
                 parking, ptype, f"2025-{month:02d}-{day:02d}", baths])

df = pd.DataFrame(rows, columns=[
    "listing_id", "locality", "bhk", "area_sqft", "furnishing", "rent_inr", "deposit_inr",
    "floor", "property_age_years", "parking", "property_type", "listing_date", "bathrooms"])

# ---------- make it messy, like real scraped data ----------
raw = df.copy().astype(object)
raw["rent_inr"] = [f"₹ {v:,}" if rng.random() < 0.6 else f"{v}" for v in df["rent_inr"]]
raw["area_sqft"] = [f"{v} sq.ft" if rng.random() < 0.5 else f"{v}" for v in df["area_sqft"]]
raw["deposit_inr"] = [f"Rs {v:,}" for v in df["deposit_inr"]]
raw["locality"] = [
    str(rng.choice([v, v.upper(), v.lower(), f" {v} "], p=[0.7, 0.1, 0.1, 0.1]))
    for v in df["locality"]
]
raw["parking"] = ["Yes" if v == 1 else "No" for v in df["parking"]]

# missing values
for col, frac in [("furnishing", 0.04), ("floor", 0.06),
                  ("property_age_years", 0.08), ("bathrooms", 0.03)]:
    idx = rng.choice(raw.index, int(frac * N), replace=False)
    raw.loc[idx, col] = np.nan

# duplicate listings
raw = pd.concat([raw, raw.sample(90, random_state=1)], ignore_index=True)

# bad entries / outliers
bad = rng.choice(raw.index, 25, replace=False)
raw.loc[bad[:10], "rent_inr"] = "₹ 9,99,999"
raw.loc[bad[10:18], "area_sqft"] = "12 sq.ft"
raw.loc[bad[18:], "rent_inr"] = "₹ 500"

out = Path(__file__).resolve().parents[1] / "data" / "raw" / "pune_rental_raw.csv"
raw.sample(frac=1, random_state=7).to_csv(out, index=False)
print(f"Saved {len(raw):,} raw rows -> {out}")
