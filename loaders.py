"""Cached data loaders. All @st.cache_data functions live here."""

import time
import duckdb
import pandas as pd
import geopandas as gpd
import streamlit as st

from config import (
    _NEEDED_COLS, _PROP_TYPE, _COND, NAME_FIX,
    DR_START, DR_END, _OWNER_PATTERNS,
)


@st.cache_data(ttl=3600)
def load_data():
    t0 = time.perf_counter()

    schema = duckdb.query(
        "DESCRIBE SELECT * FROM 'data/parquets917/nst.parquet'"
    ).df()
    existing = dict(zip(schema['column_name'], schema['column_type']))
    pull_cols = [c for c in _NEEDED_COLS if c in existing]

    _cleaned_cd = "NULLIF(TRIM(REGEXP_REPLACE(COALESCE(CLASSIFICATION_DESCR,''), '\\s+', ' ', 'g')), '')"
    _cd_cases = " ".join(
        f"WHEN cd = '{k.replace(chr(39), chr(39) * 2)}' THEN '{v.replace(chr(39), chr(39) * 2)}'"
        for k, v in _PROP_TYPE.items()
    )
    cd_expr = (
        f"CASE WHEN cd = 'NONE' THEN NULL {_cd_cases} ELSE cd END AS CLASSIFICATION_DESCR"
    )

    _cond_cases = " ".join(f"WHEN condition = '{k}' THEN '{v}'" for k, v in _COND.items())
    cond_expr = (
        f"CASE WHEN condition IS NULL OR condition = '' OR condition = 'NONE' THEN NULL "
        f"{_cond_cases} ELSE condition END AS condition"
    )

    # Bulk pandas replace for NONE strings outperforms per-column NULLIF() in SQL.
    select_parts = []
    for c in pull_cols:
        if c == 'CLASSIFICATION_DESCR':
            select_parts.append(cd_expr)
        elif c == 'condition':
            select_parts.append(cond_expr)
        else:
            select_parts.append(c)

    select_sql = ",\n            ".join(select_parts)

    df = duckdb.query(f"""
        WITH src AS (
            SELECT *,
                {_cleaned_cd} AS cd
            FROM 'data/parquets917/nst.parquet'
            WHERE PARCEL LIKE '%-%-%'
              AND (
                  LENGTH(TRIM(COALESCE(NEIGHBOR10,''))) > 0
                  OR (LENGTH(TRIM(COALESCE(address,''))) > 5
                      AND TRIM(COALESCE(address,'')) NOT LIKE '0%')
              )
        )
        SELECT {select_sql}
        FROM src
    """).df()

    _obj_cols = df.select_dtypes(include='object').columns
    if len(_obj_cols) > 0:
        df[_obj_cols] = df[_obj_cols].replace('NONE', pd.NA)

    # Fall back to number+street when address is empty or zero-prefixed.
    _addr = df['address'].fillna('')
    bad = _addr.str.len().eq(0) | _addr.str.startswith('0')
    if bad.any():
        df.loc[bad, 'address'] = (
            df.loc[bad, 'number'].fillna('').str.strip() + ' ' +
            df.loc[bad, 'street'].fillna('').str.strip()
        ).str.strip().replace('', pd.NA)
    # Strip leading zeros from any address starting with 0 followed by a digit or space.
    # Covers: "00616-800 E 6" -> "616-800 E 6", "00750 PROSPECT AVE" -> "750 PROSPECT AVE",
    # "01 DALWOOD AVE" -> "1 DALWOOD AVE", "00000" -> NA.
    df['address'] = df['address'].str.replace(r'^0+(?=[\d\s])', '', regex=True).str.strip()
    df['address'] = df['address'].replace(r'^0+$', pd.NA, regex=True)
    df['address'] = df['address'].replace('', pd.NA)

    df['is_cleveland'] = df['ward2025'].fillna('').str.strip().ne('')

    # SAS date serial (days since 1960-01-01) to YYYY-MM-DD.
    if 'date' in df.columns and pd.api.types.is_numeric_dtype(df['date']):
        _dt = pd.to_datetime(df['date'], origin='1960-01-01', unit='D', errors='coerce')
        df['date'] = _dt.dt.strftime('%Y-%m-%d').where(_dt.notna(), other=None)

    for col in _NEEDED_COLS:
        if col not in df.columns:
            df[col] = None

    print(f"[load_data] {len(df):,} rows in {time.perf_counter() - t0:.2f}s")
    return df


@st.cache_data
def load_neighborhoods():
    gdf = gpd.read_file("data/cuy_nei20_NAD83.shp").to_crs(epsg=4326)
    gdf["name_key"] = (
        gdf["NEIGHBOR20"].str.upper().str.strip()
        .map(lambda x: NAME_FIX.get(x, x))
    )
    return gdf


@st.cache_data
def load_map_agg():
    return duckdb.query("""
        SELECT
            NEIGHBOR10,
            COUNT(*) AS count,
            ROUND(SUM(CASE WHEN combovac = 1 THEN 1.0 ELSE 0.0 END)
                  / COUNT(*) * 100, 1) AS vacancy_pct,
            ROUND(AVG(CASE WHEN TAX_MARKET_TOTAL > 0
                      THEN TAX_MARKET_TOTAL END), 0) AS avg_value
        FROM 'data/parquets917/nst.parquet'
        WHERE PARCEL LIKE '%-%-%'
          AND NEIGHBOR10 IS NOT NULL AND TRIM(NEIGHBOR10) != ''
        GROUP BY NEIGHBOR10
        ORDER BY NEIGHBOR10
    """).df()


@st.cache_data
def load_neighborhood_data(hood_name):
    safe = hood_name.replace("'", "''")
    df = duckdb.query(f"""
        SELECT * FROM 'data/parquets917/nst.parquet'
        WHERE PARCEL LIKE '%-%-%'
          AND NEIGHBOR10 = '{safe}'
    """).df()
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].replace('NONE', pd.NA)
    return df


@st.cache_data
def ps_search(query):
    q = query.strip().replace("'", "''")
    return duckdb.query(f"""
        SELECT * FROM 'data/parquets917/nst.parquet'
        WHERE regexp_matches(PARCEL, '^\d{{3}}-\d{{2}}-\d{{3}}')
          AND address IS NOT NULL AND TRIM(address) != ''
          AND (
            UPPER(address) LIKE UPPER('%{q}%')
            OR UPPER(PARCEL) LIKE '%{q.upper()}%'
            OR UPPER(PRIMARY_OWNER_NAME) LIKE UPPER('%{q}%')
            OR UPPER(COALESCE(number,'') || ' ' || COALESCE(street,'')) LIKE UPPER('%{q}%')
          )
        LIMIT 50
    """).df()


@st.cache_data
def ps_value_history(parcel_id):
    safe = parcel_id.replace("'", "''")
    return duckdb.query(f"""
        SELECT taxyr, mktval, mktland, mktbldg, condition, owner, ownerocc
        FROM 'data/parquets917/parcel_history.parquet'
        WHERE parcel = '{safe}' AND taxyr IS NOT NULL AND mktval IS NOT NULL
        ORDER BY taxyr
    """).df()


@st.cache_data
def ps_sales_history(parcel_id):
    safe = parcel_id.replace("'", "''")
    return duckdb.query(f"""
        SELECT YEAR_OF_SALE, MONTH_OF_SALE, SALES_AMOUNT,
               GRANTEE1, GRANTOR1, DEED_TYPE, TRANSFER_TYPE_DESCR, SALE_VALID
        FROM 'data/parquets917/sales.parquet'
        WHERE PROPERTY_NUMBER = '{safe}'
          AND SALES_AMOUNT > 100
        ORDER BY YEAR_OF_SALE DESC, MONTH_OF_SALE DESC
    """).df()


@st.cache_data
def ps_tax_history(parcel_id):
    safe = parcel_id.replace("'", "''")
    return duckdb.query(f"""
        SELECT TAX_YEAR, TAX_MARKET_TOTAL, TAX_MARKET_LAND, TAX_MARKET_IMPROVEMENT,
               NET_TAX_DELQ_DUE, GRAND_TOTAL_OWED, GRAND_TOTAL_PAID, GRAND_TOTAL_BALANCE
        FROM 'data/parquets917/tax_bill.parquet'
        WHERE PROPERTY_NUMBER = '{safe}' AND TAX_YEAR IS NOT NULL
        ORDER BY TAX_YEAR DESC
    """).df()


@st.cache_data
def ps_hood_counts():
    return duckdb.query("""
        SELECT NEIGHBOR10, COUNT(*) AS cnt
        FROM 'data/parquets917/nst.parquet'
        WHERE PARCEL LIKE '%-%-%' AND NEIGHBOR10 IS NOT NULL
        GROUP BY NEIGHBOR10 ORDER BY cnt DESC LIMIT 10
    """).df()


@st.cache_data
def load_oos_data():
    return pd.read_csv("data/nstsample.csv", low_memory=False)


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
