# Power BI Dashboard Guide

A `.pbix` file cannot be generated outside Power BI Desktop, so build it with this guide (about 2-3 hours).
Save the finished file as `powerbi/Pune_Rental_Dashboard.pbix` and add screenshots to `images/`.

## 1. Load data
1. Power BI Desktop -> **Get Data -> Text/CSV** -> `data/processed/pune_rental_clean.csv`
2. **Transform Data** and check types: `listing_date` = Date, `rent_inr`, `area_sqft`, `deposit_inr` = Whole Number, `rent_per_sqft` = Decimal.
3. Rename the table to `Listings`. Close & Apply.

## 2. Date table (needed for time intelligence)
```DAX
DateTable =
ADDCOLUMNS (
    CALENDAR ( DATE ( 2025, 1, 1 ), DATE ( 2025, 12, 31 ) ),
    "Month No", MONTH ( [Date] ),
    "Month", FORMAT ( [Date], "MMM" )
)
```
Relate `DateTable[Date]` -> `Listings[listing_date]` (many-to-one). Sort `Month` by `Month No`.

## 3. DAX measures
```DAX
Total Listings = COUNTROWS ( Listings )

Avg Rent = AVERAGE ( Listings[rent_inr] )

Median Rent = MEDIAN ( Listings[rent_inr] )

Avg Rent per SqFt = AVERAGE ( Listings[rent_per_sqft] )

Avg Deposit Months = AVERAGE ( Listings[deposit_months] )

City Avg PPSF = CALCULATE ( [Avg Rent per SqFt], ALL ( Listings ) )

Vs City Avg % = DIVIDE ( [Avg Rent per SqFt], [City Avg PPSF] ) - 1

Locality Segment =
VAR r = DIVIDE ( [Avg Rent per SqFt], [City Avg PPSF] )
RETURN SWITCH ( TRUE (), r > 1.15, "Premium", r < 0.85, "Value", "Mid-market" )

Furnished Premium % =
VAR f = CALCULATE ( [Avg Rent per SqFt], Listings[furnishing] = "Furnished" )
VAR u = CALCULATE ( [Avg Rent per SqFt], Listings[furnishing] = "Unfurnished" )
RETURN DIVIDE ( f, u ) - 1

Fresher Budget Listings =
CALCULATE ( [Total Listings], Listings[bhk] IN { 1, 2 }, Listings[rent_inr] <= 25000 )

MoM Change % =
VAR prev = CALCULATE ( [Avg Rent per SqFt], DATEADD ( DateTable[Date], -1, MONTH ) )
RETURN DIVIDE ( [Avg Rent per SqFt] - prev, prev )
```

## 4. Page layout (4 pages)

| Page | Visuals |
|---|---|
| **1. Market Overview** | KPI cards (Total Listings, Avg Rent, Median Rent, Avg Rent per SqFt, Avg Deposit Months); line chart of Avg Rent per SqFt by Month; donut of listings by BHK; slicers: Zone, BHK, Furnishing |
| **2. Locality Analysis** | Bar chart of Avg Rent per SqFt by Locality coloured by `Locality Segment`; matrix Locality x BHK with Avg Rent and a colour scale; table with `Vs City Avg %` |
| **3. Fresher Budget Finder** | Slicer for Max Rent (what-if parameter, Rs 10k-60k); bar of `Fresher Budget Listings` by Locality; table of cheapest locality + BHK combos; card for the number of options |
| **4. Pricing Drivers** | Clustered column: Avg Rent by Furnishing and BHK; column chart: PPSF by property-age band; card `Furnished Premium %`; scatter of Area vs Rent |

## 5. Design rules
- 2 colours only (navy `#1F4E79`, orange `#E07B39`) plus grey.
- Titles that state the question, e.g. "Which localities are overpriced?".
- Add a short text box on each page with the insight in one sentence.
- Use bookmarks / page navigation buttons for a clean look.

## 6. Publish
Take screenshots of all 4 pages -> `images/dashboard_page1.png` ... `page4.png`, and link them in the README.
