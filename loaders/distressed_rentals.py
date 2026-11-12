"""Loader for the Distressed Rentals page. The SQL stays monolithic (see methodology)."""

import time
import duckdb
import pandas as pd
import streamlit as st

from config import DR_START, DR_END, _OWNER_PATTERNS


@st.cache_data(ttl=3600)
def load_distressed_rentals():
    t0 = time.perf_counter()

    owner_case_parts = []
    for label, pat in _OWNER_PATTERNS.items():
        sql_pat = pat.replace("'", "''")
        owner_case_parts.append(f"WHEN regexp_matches(owner_norm, '{sql_pat}') THEN '{label}'")
    owner_case_parts.append(r"WHEN regexp_matches(owner_norm, '^[A-Z]+,?\s[A-Z]+') THEN 'Individual'")
    owner_case = " ".join(owner_case_parts)

    q = f"""
    WITH base AS (
        SELECT
            PARCEL, address, NEIGHBOR10, ward2025, zip, cuyregion,
            PRIMARY_OWNER_NAME,
            UPPER(TRIM(COALESCE(PRIMARY_OWNER_NAME, ''))) AS owner_norm,
            CLASSIFICATION_DESCR AS land_use_code,
            pclass AS property_class,
            HOMESTEAD_FLAG AS homestead,
            totbldgs AS tot_bldgs,
            TAX_MARKET_IMPROVEMENT AS estimated_building_value,
            TAX_MARKET_TOTAL,
            NET_TAX_DELQ_DUE,
            FORECLOSURE_FLAG,
            combovac,
            violation_file_date,
            cdc_comp_file_date, council_comp_file_date, mac_comp_file_date,
            public_comp_file_date, other_comp_file_date, mayor_comp_file_date,
            COALESCE(cases_filed_2021,0) + COALESCE(cases_filed_2022,0)
              + COALESCE(cases_filed_2023,0) + COALESCE(cases_filed_2024,0)
              + COALESCE(cases_filed_2025,0) AS eviction_cases_total,
            tci2015_survey_grade AS grade_2015,
            wrlc23_results AS grade_2023,
            RR_status,
            LATITUDE, LONGITUDE
        FROM 'data/parquets917/nst.parquet'
        WHERE regexp_matches(PARCEL, '^[0-9]{{3}}-[0-9]{{2}}-[0-9]{{3}}')
          AND (parcel_status IS NULL OR UPPER(parcel_status) = 'CURRENT')
    ),
    flagged AS (
        SELECT *,
            CASE
                WHEN property_class IN ('AGRICULTURAL','PUBLIC UTILITIES','INDUSTRIAL',
                    'LAND BANK','MISSING','COMMON AREA','COMMUNITY SHOPPING CENTER',
                    'DAY CARE CENTERS') THEN 99
                WHEN land_use_code IN ('SINGLE FAMILY DWELLING','RESIDENTIAL CONDOMINIUM')
                     AND regexp_matches(owner_norm, 'LLC|L\\.L\\.C') THEN 2
                WHEN land_use_code IN ('SINGLE FAMILY DWELLING','RESIDENTIAL CONDOMINIUM')
                     AND homestead = 1 THEN 0
                WHEN land_use_code LIKE '%TWO FAMILY%' OR land_use_code LIKE '%THREE FAMILY%' THEN 2
                WHEN (tot_bldgs = 0 OR tot_bldgs IS NULL)
                     AND (estimated_building_value = 0 OR estimated_building_value IS NULL) THEN 99
                WHEN land_use_code = 'SINGLE FAMILY DWELLING' AND (homestead = 0 OR homestead IS NULL) THEN 2
                WHEN land_use_code = 'RESIDENTIAL CONDOMINIUM' AND (homestead = 0 OR homestead IS NULL) THEN 2
                WHEN UPPER(COALESCE(RR_status,'')) IN ('ABOUT TO EXPIRE','REGISTRATION RENEWED','ACTIVE') THEN 1
                WHEN land_use_code LIKE '%APARTMENT%' THEN 1
                ELSE 99
            END AS rent_flag,

            CASE WHEN NET_TAX_DELQ_DUE >= 500 THEN 1 ELSE 0 END AS delinquent_flag,

            CASE WHEN TRY_CAST(violation_file_date AS DATE)
                    BETWEEN DATE '{DR_START}' AND DATE '{DR_END}' THEN 1 ELSE 0 END AS violation_flag,

            CASE WHEN
                (TRY_CAST(cdc_comp_file_date     AS DATE) BETWEEN DATE '{DR_START}' AND DATE '{DR_END}')
             OR (TRY_CAST(council_comp_file_date AS DATE) BETWEEN DATE '{DR_START}' AND DATE '{DR_END}')
             OR (TRY_CAST(mac_comp_file_date     AS DATE) BETWEEN DATE '{DR_START}' AND DATE '{DR_END}')
             OR (TRY_CAST(public_comp_file_date  AS DATE) BETWEEN DATE '{DR_START}' AND DATE '{DR_END}')
             OR (TRY_CAST(other_comp_file_date   AS DATE) BETWEEN DATE '{DR_START}' AND DATE '{DR_END}')
             OR (TRY_CAST(mayor_comp_file_date   AS DATE) BETWEEN DATE '{DR_START}' AND DATE '{DR_END}')
            THEN 1 ELSE 0 END AS complaint_flag,

            CASE
                WHEN grade_2015 NOT IN ('A','B','C','D','F') THEN NULL
                WHEN grade_2023 NOT IN ('A','B','C','D','F') THEN NULL
                WHEN (CASE grade_2023 WHEN 'A' THEN 4 WHEN 'B' THEN 3 WHEN 'C' THEN 2 WHEN 'D' THEN 1 WHEN 'F' THEN 0 END)
                   < (CASE grade_2015 WHEN 'A' THEN 4 WHEN 'B' THEN 3 WHEN 'C' THEN 2 WHEN 'D' THEN 1 WHEN 'F' THEN 0 END)
                THEN 1 ELSE 0
            END AS grade_declined_flag,

            CASE
                WHEN grade_2015 NOT IN ('A','B','C','D','F') OR grade_2023 NOT IN ('A','B','C','D','F') THEN 'Unknown'
                WHEN (CASE grade_2023 WHEN 'A' THEN 4 WHEN 'B' THEN 3 WHEN 'C' THEN 2 WHEN 'D' THEN 1 WHEN 'F' THEN 0 END)
                   > (CASE grade_2015 WHEN 'A' THEN 4 WHEN 'B' THEN 3 WHEN 'C' THEN 2 WHEN 'D' THEN 1 WHEN 'F' THEN 0 END)
                THEN 'Improved'
                WHEN (CASE grade_2023 WHEN 'A' THEN 4 WHEN 'B' THEN 3 WHEN 'C' THEN 2 WHEN 'D' THEN 1 WHEN 'F' THEN 0 END)
                   < (CASE grade_2015 WHEN 'A' THEN 4 WHEN 'B' THEN 3 WHEN 'C' THEN 2 WHEN 'D' THEN 1 WHEN 'F' THEN 0 END)
                THEN 'Declined'
                ELSE 'No Change'
            END AS grade_change,

            CASE WHEN eviction_cases_total > 0 THEN 1 ELSE 0 END AS eviction_flag,

            CASE
                WHEN owner_norm = '' OR owner_norm IS NULL OR owner_norm = 'NONE' THEN 'Unknown/Missing'
                {owner_case}
                ELSE 'Unknown/Missing'
            END AS owner_type
        FROM base
    ),
    scored AS (
        SELECT *,
            (delinquent_flag + violation_flag + complaint_flag
             + COALESCE(grade_declined_flag,0) + eviction_flag) AS distress_score,
            CASE WHEN owner_type IN ('Corporate Entity','Trust') THEN 1 ELSE 0 END AS investor_flag
        FROM flagged
        WHERE rent_flag IN (1, 2)
    ),

    tax_latest AS (
        SELECT PROPERTY_NUMBER,
               PRIMARY_OWNER_NAME AS tax_owner,
               ROW_NUMBER() OVER (PARTITION BY PROPERTY_NUMBER ORDER BY TAX_YEAR DESC NULLS LAST) AS rn,
               MAIL_STREET_NUMBER, MAIL_STREET_DIRECTION, MAIL_STREET_NAME, MAIL_STREET_SUFFIX,
               MAIL_CITY, MAIL_STATE, MAIL_ZIPCODE
        FROM 'data/parquets917/tax_bill.parquet'
        WHERE PROPERTY_NUMBER IS NOT NULL AND TRIM(PROPERTY_NUMBER) != ''
    ),
    tax_mailing AS (
        SELECT PROPERTY_NUMBER, tax_owner,
               UPPER(TRIM(REGEXP_REPLACE(
                 CONCAT_WS(' ', MAIL_STREET_NUMBER, MAIL_STREET_DIRECTION,
                           MAIL_STREET_NAME, MAIL_STREET_SUFFIX),
                 '[[:punct:]]', '', 'g'))) AS clean_addr,
               SUBSTR(TRIM(MAIL_ZIPCODE), 1, 5) AS clean_zip,
               UPPER(TRIM(COALESCE(MAIL_CITY,''))) AS mail_city,
               UPPER(TRIM(COALESCE(MAIL_STATE,''))) AS mail_state
        FROM tax_latest
        WHERE rn = 1
          AND MAIL_STREET_NAME IS NOT NULL AND TRIM(MAIL_STREET_NAME) != ''
          AND MAIL_ZIPCODE   IS NOT NULL AND TRIM(MAIL_ZIPCODE)   != ''
    ),
    tax_with_id AS (
        SELECT *, clean_addr || '_' || clean_zip AS mailing_id,
               TRIM(clean_addr || ', ' || mail_city || ' ' || mail_state || ' ' || clean_zip) AS mailing_display
        FROM tax_mailing
    ),
    portfolio_stats AS (
        SELECT mailing_id,
               ANY_VALUE(mailing_display) AS mailing_display,
               COUNT(*) AS true_portfolio_size,
               COUNT(DISTINCT tax_owner) AS unique_entity_count,
               CAST(COUNT(DISTINCT tax_owner) AS DOUBLE)
                   / NULLIF(COUNT(*), 0) AS name_ratio,
               MODE(tax_owner) AS primary_owner_at_mailing,
               STRING_AGG(DISTINCT tax_owner, ' | ' ORDER BY tax_owner) AS all_entity_names
        FROM tax_with_id
        GROUP BY mailing_id
    ),
    portfolio_flagged AS (
        SELECT *,
            CASE WHEN name_ratio > 0.5 AND true_portfolio_size >= 10 THEN 1 ELSE 0 END AS is_likely_mail_drop
        FROM portfolio_stats
    )

    SELECT s.*,
           t.mailing_id, t.mailing_display,
           COALESCE(pf.true_portfolio_size, 1) AS true_portfolio_size,
           COALESCE(pf.unique_entity_count, 1) AS unique_entity_count,
           COALESCE(pf.is_likely_mail_drop, 0) AS is_likely_mail_drop,
           pf.primary_owner_at_mailing,
           pf.all_entity_names
    FROM scored s
    LEFT JOIN tax_with_id t ON s.PARCEL = t.PROPERTY_NUMBER
    LEFT JOIN portfolio_flagged pf ON t.mailing_id = pf.mailing_id
    """
    df = duckdb.query(q).df()

    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].replace('NONE', pd.NA)

    print(f"[distressed_rentals] {len(df):,} rentals in {time.perf_counter() - t0:.2f}s")
    return df
