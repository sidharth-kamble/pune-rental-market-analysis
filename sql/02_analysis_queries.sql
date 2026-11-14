-- =====================================================================
-- Pune Rental Market Analysis | 15 business questions in SQL
-- Uses: Aggregations, CTEs, Window Functions (RANK, LAG, NTILE,
--       ROW_NUMBER, running totals), CASE, Subqueries
-- =====================================================================
USE pune_rentals;

-- Q1. Market overview (KPI cards)
SELECT COUNT(*)                         AS total_listings,
       ROUND(AVG(rent_inr))             AS avg_rent,
       ROUND(AVG(rent_per_sqft), 2)     AS avg_rent_per_sqft,
       ROUND(AVG(deposit_months), 1)    AS avg_deposit_months
FROM listings;

-- Q2. Which localities are the most expensive per sq ft? (RANK)
SELECT locality,
       COUNT(*)                          AS listings,
       ROUND(AVG(rent_per_sqft), 2)      AS avg_rent_per_sqft,
       RANK() OVER (ORDER BY AVG(rent_per_sqft) DESC) AS price_rank
FROM listings
GROUP BY locality
ORDER BY price_rank;

-- Q3. Average rent by BHK type
SELECT bhk, COUNT(*) AS listings, ROUND(AVG(rent_inr)) AS avg_rent,
       ROUND(AVG(area_sqft)) AS avg_area
FROM listings
GROUP BY bhk
ORDER BY bhk;

-- Q4. Top 5 locality + BHK combinations by average rent (min 30 listings)
SELECT locality, bhk, COUNT(*) AS listings, ROUND(AVG(rent_inr)) AS avg_rent
FROM listings
GROUP BY locality, bhk
HAVING COUNT(*) >= 30
ORDER BY avg_rent DESC
LIMIT 5;

-- Q5. Furnishing premium: how much extra do furnished flats cost? (CTE)
WITH base AS (
    SELECT bhk, AVG(rent_per_sqft) AS unfurnished_ppsf
    FROM listings WHERE furnishing = 'Unfurnished'
    GROUP BY bhk
)
SELECT l.furnishing, l.bhk,
       ROUND(AVG(l.rent_per_sqft), 2) AS avg_ppsf,
       ROUND((AVG(l.rent_per_sqft) / b.unfurnished_ppsf - 1) * 100, 1) AS premium_pct_vs_unfurnished
FROM listings l
JOIN base b ON l.bhk = b.bhk
WHERE l.furnishing <> 'Unknown'
GROUP BY l.furnishing, l.bhk, b.unfurnished_ppsf
ORDER BY l.bhk, premium_pct_vs_unfurnished;

-- Q6. Budget finder: 1 BHK / 2 BHK localities under Rs 25,000 for a fresher
SELECT locality, bhk,
       COUNT(*)                       AS options_available,
       ROUND(AVG(rent_inr))           AS avg_rent
FROM listings
WHERE bhk IN (1, 2) AND rent_inr <= 25000
GROUP BY locality, bhk
HAVING COUNT(*) >= 10
ORDER BY bhk, avg_rent;

-- Q7. Value score: cheapest localities vs. city average (CTE + CASE)
WITH city AS (SELECT AVG(rent_per_sqft) AS city_avg FROM listings),
loc AS (
    SELECT locality, AVG(rent_per_sqft) AS loc_avg, COUNT(*) AS n
    FROM listings GROUP BY locality
)
SELECT loc.locality,
       ROUND(loc.loc_avg, 2) AS avg_rent_per_sqft,
       ROUND((loc.loc_avg / city.city_avg - 1) * 100, 1) AS vs_city_avg_pct,
       CASE WHEN loc.loc_avg < city.city_avg * 0.85 THEN 'Value'
            WHEN loc.loc_avg > city.city_avg * 1.15 THEN 'Premium'
            ELSE 'Mid-market' END AS segment
FROM loc CROSS JOIN city
ORDER BY vs_city_avg_pct;

-- Q8. Monthly rent trend with month-on-month change (LAG)
WITH monthly AS (
    SELECT listing_month, ROUND(AVG(rent_per_sqft), 2) AS avg_ppsf, COUNT(*) AS listings
    FROM listings GROUP BY listing_month
)
SELECT listing_month, listings, avg_ppsf,
       ROUND((avg_ppsf / LAG(avg_ppsf) OVER (ORDER BY listing_month) - 1) * 100, 2) AS mom_change_pct
FROM monthly
ORDER BY listing_month;

-- Q9. Running total of listings by month (window SUM)
SELECT listing_month,
       COUNT(*) AS listings,
       SUM(COUNT(*)) OVER (ORDER BY listing_month) AS cumulative_listings
FROM listings
GROUP BY listing_month
ORDER BY listing_month;

-- Q10. Rank localities inside each zone (PARTITION BY)
SELECT zone, locality, ROUND(AVG(rent_per_sqft), 2) AS avg_ppsf,
       RANK() OVER (PARTITION BY zone ORDER BY AVG(rent_per_sqft) DESC) AS rank_in_zone
FROM listings
GROUP BY zone, locality
ORDER BY zone, rank_in_zone;

-- Q11. Does property age reduce rent? (CASE bucket)
SELECT CASE WHEN property_age_years <= 3  THEN '0-3 yrs (new)'
            WHEN property_age_years <= 8  THEN '4-8 yrs'
            WHEN property_age_years <= 14 THEN '9-14 yrs'
            ELSE '15+ yrs' END AS age_group,
       COUNT(*) AS listings,
       ROUND(AVG(rent_per_sqft), 2) AS avg_ppsf
FROM listings
GROUP BY age_group
ORDER BY MIN(property_age_years);

-- Q12. Does a parking slot add to the rent?
SELECT locality,
       ROUND(AVG(CASE WHEN parking = 1 THEN rent_per_sqft END), 2) AS with_parking,
       ROUND(AVG(CASE WHEN parking = 0 THEN rent_per_sqft END), 2) AS without_parking
FROM listings
GROUP BY locality
ORDER BY locality;

-- Q13. Price tiers: split localities into 4 groups (NTILE)
WITH loc AS (
    SELECT locality, AVG(rent_per_sqft) AS avg_ppsf FROM listings GROUP BY locality
)
SELECT locality, ROUND(avg_ppsf, 2) AS avg_ppsf,
       NTILE(4) OVER (ORDER BY avg_ppsf DESC) AS price_tier   -- 1 = most expensive
FROM loc
ORDER BY price_tier, avg_ppsf DESC;

-- Q14. Listings priced far above their locality + BHK norm (overpriced flag, subquery)
SELECT l.listing_id, l.locality, l.bhk, l.area_sqft, l.rent_inr,
       ROUND(a.avg_rent) AS locality_bhk_avg,
       ROUND((l.rent_inr / a.avg_rent - 1) * 100, 1) AS above_avg_pct
FROM listings l
JOIN (SELECT locality, bhk, AVG(rent_inr) AS avg_rent
      FROM listings GROUP BY locality, bhk) a
  ON a.locality = l.locality AND a.bhk = l.bhk
WHERE l.rent_inr > a.avg_rent * 1.25
ORDER BY above_avg_pct DESC
LIMIT 20;

-- Q15. Top 3 best-value listings per locality for 2 BHK (ROW_NUMBER)
WITH ranked AS (
    SELECT listing_id, locality, area_sqft, rent_inr, rent_per_sqft, furnishing,
           ROW_NUMBER() OVER (PARTITION BY locality ORDER BY rent_per_sqft) AS rn
    FROM listings
    WHERE bhk = 2 AND area_sqft >= 800
)
SELECT * FROM ranked WHERE rn <= 3 ORDER BY locality, rn;
