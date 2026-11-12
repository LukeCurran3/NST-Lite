"""Core dataset loaders: the full nst.parquet view plus neighborhood aggregates."""

import time
import duckdb
import pandas as pd
import geopandas as gpd
import streamlit as st

from config import _NEEDED_COLS, _PROP_TYPE, _COND, NAME_FIX


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

    # Recode implausible year built values to null (county records pre-1800 are data errors).
    if 'yrbuilt' in df.columns:
        df['yrbuilt'] = df['yrbuilt'].where(df['yrbuilt'] >= 1800, other=pd.NA)

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
