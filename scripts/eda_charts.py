"""
EDA + charts + auto-generated insight summary.

Run:  python scripts/eda_charts.py
Outputs: images/*.png  and  docs/insights_summary.md
All numbers in insights_summary.md are computed from whatever data is in
data/processed/pune_rental_clean.csv, so re-run after loading REAL data.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "data" / "processed" / "pune_rental_clean.csv")
IMG = ROOT / "images"
IMG.mkdir(exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.0)
BLUE, ORANGE, GREY = "#1f4e79", "#e07b39", "#9aa5b1"


def save(name):
    plt.tight_layout()
    plt.savefig(IMG / name, dpi=150)
    plt.close()


# 1. Rent per sq ft by locality
loc = df.groupby("locality").agg(ppsf=("rent_per_sqft", "mean"), n=("listing_id", "count")) \
        .sort_values("ppsf")
city_avg = df["rent_per_sqft"].mean()
colors = [ORANGE if v > city_avg * 1.15 else BLUE if v < city_avg * 0.85 else GREY for v in loc["ppsf"]]
plt.figure(figsize=(9, 7))
plt.barh(loc.index, loc["ppsf"], color=colors)
plt.axvline(city_avg, color="black", ls="--", lw=1)
plt.text(city_avg + 0.3, 0.2, f"City avg Rs {city_avg:.1f}", fontsize=9)
plt.title("Average Rent per Sq Ft by Locality (orange = premium, blue = value)")
plt.xlabel("Rs per sq ft per month")
save("01_rent_per_sqft_by_locality.png")

# 2. Average rent by BHK and furnishing
piv = df[df["furnishing"] != "Unknown"].pivot_table(
    index="bhk", columns="furnishing", values="rent_inr", aggfunc="mean")
piv[["Unfurnished", "Semi-Furnished", "Furnished"]].plot(
    kind="bar", figsize=(8, 5), color=[GREY, BLUE, ORANGE])
plt.title("Average Monthly Rent by BHK and Furnishing")
plt.ylabel("Rs per month")
plt.xlabel("BHK")
plt.xticks(rotation=0)
save("02_rent_by_bhk_furnishing.png")

# 3. Monthly trend
m = df.groupby("listing_month").agg(ppsf=("rent_per_sqft", "mean"), n=("listing_id", "count"))
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(m.index, m["ppsf"], marker="o", color=BLUE)
ax.set_ylabel("Avg rent per sq ft (Rs)", color=BLUE)
ax2 = ax.twinx()
ax2.bar(m.index, m["n"], alpha=0.2, color=ORANGE)
ax2.set_ylabel("Listings", color=ORANGE)
ax.set_title("Monthly Rent per Sq Ft and Listing Volume")
plt.setp(ax.get_xticklabels(), rotation=45)
save("03_monthly_trend.png")

# 4. Price tier heatmap: locality x BHK average rent
heat = df.pivot_table(index="locality", columns="bhk", values="rent_inr", aggfunc="mean")
heat = heat.loc[loc.index[::-1]]
plt.figure(figsize=(7, 8))
sns.heatmap(heat / 1000, annot=True, fmt=".0f", cmap="YlOrRd", cbar_kws={"label": "Rs '000 / month"})
plt.title("Average Rent (Rs '000) by Locality and BHK")
save("04_heatmap_locality_bhk.png")

# 5. Property age vs rent per sqft
age_bins = pd.cut(df["property_age_years"], [-1, 3, 8, 14, 100], labels=["0-3", "4-8", "9-14", "15+"])
a = df.groupby(age_bins, observed=True)["rent_per_sqft"].mean()
plt.figure(figsize=(6, 4.5))
plt.bar(a.index.astype(str), a.values, color=BLUE)
plt.title("Rent per Sq Ft by Property Age (years)")
plt.ylabel("Rs per sq ft")
save("05_age_vs_rent.png")

# 6. Budget finder: options under Rs 25k for 1-2 BHK
bud = df[(df["bhk"].isin([1, 2])) & (df["rent_inr"] <= 25000)].groupby("locality").size().sort_values()
plt.figure(figsize=(8, 6))
plt.barh(bud.index, bud.values, color=BLUE)
plt.title("Number of 1-2 BHK Listings Under Rs 25,000 by Locality")
plt.xlabel("Listings")
save("06_budget_options.png")

# 7. Distribution of rent
plt.figure(figsize=(8, 4.5))
sns.histplot(df["rent_inr"], bins=40, color=BLUE)
plt.axvline(df["rent_inr"].median(), color=ORANGE, ls="--", label=f"Median Rs {df['rent_inr'].median():,.0f}")
plt.legend()
plt.title("Distribution of Monthly Rent")
plt.xlabel("Rs per month")
save("07_rent_distribution.png")

# ---------------- insight summary ----------------
top = loc.sort_values("ppsf", ascending=False)
f = df[df["furnishing"] != "Unknown"].groupby("furnishing")["rent_per_sqft"].mean()
prem = (f["Furnished"] / f["Unfurnished"] - 1) * 100
age_new, age_old = a.iloc[0], a.iloc[-1]
fresher = df[(df["bhk"] == 1) & (df["rent_inr"] <= 20000)].groupby("locality").size().sort_values(ascending=False)
dep = df["deposit_months"].mean()
spread = top["ppsf"].iloc[0] / top["ppsf"].iloc[-1]

lines = [
    "# Insights Summary (auto-generated)",
    "",
    "> Generated from the data currently in `data/processed/pune_rental_clean.csv`.",
    "> If that file is the SIMULATED sample, these numbers are NOT real market findings.",
    "> Re-run the pipeline on real listings before using any figure on a CV or in an interview.",
    "",
    f"- Listings analysed: **{len(df):,}** across **{df['locality'].nunique()}** localities.",
    f"- Median rent: **Rs {df['rent_inr'].median():,.0f}**; average rent per sq ft: **Rs {city_avg:.1f}**.",
    f"- Most expensive locality: **{top.index[0]}** (Rs {top['ppsf'].iloc[0]:.1f}/sq ft); cheapest: "
    f"**{top.index[-1]}** (Rs {top['ppsf'].iloc[-1]:.1f}/sq ft), a **{spread:.1f}x** gap.",
    f"- Furnished flats cost about **{prem:.0f}%** more per sq ft than unfurnished ones.",
    f"- Newer properties (0-3 yrs) average Rs {age_new:.1f}/sq ft vs Rs {age_old:.1f} for 15+ yrs.",
    f"- Average security deposit: **{dep:.1f} months** of rent.",
    f"- Most 1 BHK options under Rs 20,000: " + ", ".join(f"{k} ({v})" for k, v in fresher.head(3).items()) + ".",
]
(ROOT / "docs" / "insights_summary.md").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
