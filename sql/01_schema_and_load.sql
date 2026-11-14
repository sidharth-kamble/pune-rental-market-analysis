-- =====================================================================
-- Pune Rental Market Analysis | MySQL 8.0
-- Step 1: create database + table and load the cleaned CSV
-- =====================================================================
CREATE DATABASE IF NOT EXISTS pune_rentals;
USE pune_rentals;

DROP TABLE IF EXISTS listings;
CREATE TABLE listings (
    listing_id          VARCHAR(12) PRIMARY KEY,
    locality            VARCHAR(50)  NOT NULL,
    bhk                 TINYINT      NOT NULL,
    area_sqft           INT          NOT NULL,
    furnishing          VARCHAR(20),
    rent_inr            INT          NOT NULL,
    deposit_inr         INT,
    floor_no            INT,
    property_age_years  INT,
    parking             TINYINT,
    property_type       VARCHAR(30),
    listing_date        DATE,
    bathrooms           TINYINT,
    rent_per_sqft       DECIMAL(8,2),
    zone                VARCHAR(15),
    listing_month       CHAR(7),
    rent_band           VARCHAR(10),
    deposit_months      DECIMAL(4,1)
);

-- Option A (recommended for beginners): MySQL Workbench ->
--   right-click table `listings` -> Table Data Import Wizard -> choose
--   data/processed/pune_rental_clean.csv  (map column `floor` -> `floor_no`).
--
-- Option B: command (enable local_infile first):
-- LOAD DATA LOCAL INFILE 'data/processed/pune_rental_clean.csv'
-- INTO TABLE listings
-- FIELDS TERMINATED BY ',' ENCLOSED BY '"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 LINES;

-- Quick check
SELECT COUNT(*) AS total_listings, MIN(listing_date) AS first_date, MAX(listing_date) AS last_date
FROM listings;

-- Helpful indexes for the analysis queries
CREATE INDEX idx_locality ON listings (locality);
CREATE INDEX idx_bhk ON listings (bhk);
CREATE INDEX idx_month ON listings (listing_month);
