"""Loaders for the Property Search page: fuzzy search and per-parcel history pulls."""

import duckdb
import streamlit as st

from utils.parcel import strip_suffix, normalize_parcel


@st.cache_data
def ps_search(query):
    q = query.strip().replace("'", "''")
    q_stripped = strip_suffix(query.strip()).replace("'", "''")
    extra_clause = f"OR UPPER(address) LIKE UPPER('%{q_stripped}%')" if q_stripped.upper() != q.upper() else ""
    normalized = normalize_parcel(query.strip())
    parcel_clause = f"OR UPPER(PARCEL) LIKE '%{normalized.upper()}%'" if normalized else ""
    return duckdb.query(f"""
        SELECT * FROM 'data/parquets917/nst.parquet'
        WHERE regexp_matches(PARCEL, '^\d{{3}}-\d{{2}}-\d{{3}}')
          AND (
            (address IS NOT NULL AND TRIM(address) != '' AND UPPER(address) LIKE UPPER('%{q}%'))
            {f"OR (address IS NOT NULL AND TRIM(address) != '' AND UPPER(address) LIKE UPPER('%{q_stripped}%'))" if q_stripped.upper() != q.upper() else ""}
            OR UPPER(PARCEL) LIKE '%{q.upper()}%'
            {parcel_clause}
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
