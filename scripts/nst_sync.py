"""
nst_sync.py  --  Run on msassneocandod1 via Windows Task Scheduler (nightly at 3 AM).
Reads SAS source files from the P-drive network share, converts any stale ones to
Parquet, and writes the result to C:\nst\data\ where the Streamlit app can read them.
"""

import os
import pyreadstat
import pandas as pd

# SAS source files live on the shared P-drive (mapped to \\msasspovertyp1\epilots\data).
# Use the raw UNC path so the scheduled task works even when no drive letter is mapped.
SAS_DIR = r'\\msasspovertyp1\epilots\data\\'

# Parquet output goes on the local disk of the app server.
# The Streamlit app reads from this folder via a Windows directory junction at
# C:\nst\app\data\parquets917 -> C:\nst\data  (created once with mklink /J).
OUT_DIR = r'C:\nst\data\\'

os.makedirs(OUT_DIR, exist_ok=True)

# SAS file  →  (output parquet name,  columns to export)
# Column names verified against acrosssource.sas7bdat via pyreadstat metadataonly
EXPORTS = {
    'acrosssource.sas7bdat': ('nst.parquet', [
        # Core identity & geography
        'PARCEL', 'number', 'street', 'address', 'LATITUDE', 'LONGITUDE',
        'NEIGHBOR10', 'PPN', 'cia14_name', 'tract', 'zip', 'cuyregion', 'ward2025',
        # Owner info
        'PRIMARY_OWNER_NAME', 'MAIL_STATE',
        # Property characteristics
        'CLASSIFICATION_DESCR', 'pclass', 'luc', 'zone_desc', 'parcel_status',
        'yrbuilt', 'condition', 'style', 'rextwall', 'numstory', 'basesqft',
        'propsize', 'bedrooms', 'baths', 'units', 'totbldgs',
        # Values & taxes
        'TAX_MARKET_LAND', 'TAX_MARKET_IMPROVEMENT', 'TAX_MARKET_TOTAL',
        'currentvalue2023', 'proposedvalue2024', 'assessment',
        'HOMESTEAD_FLAG', 'PAYMENT_PLAN_FLAG', 'taxabate',
        'NET_TAX_DELQ_DUE', 'CERT_PEND_FLAG', 'CERT_SOLD_FLAG', 'BOR_STATUS',
        # Foreclosure & forfeiture
        'FORECLOSURE_FLAG', 'lstatus', 'caseno', 'cdesig', 'fo_deed_count',
        # Land bank
        'city_lb_flag', 'cclrc', 'disp_status', 'demo_status', 'rehab_status',
        # Vacancy & condemnation
        'combovac', 'vl', 'lbvl', 'unoccupied', 'active_condemn',
        # Lead safe certifications
        'lsc_stat', 'lsc_issue_dt', 'lead_rollout',
        # Violations
        'violation', 'violation_vin', 'violation_file_date',
        'violation_task_status', 'violation_vtype',
        'cdc_comp', 'cdc_comp_file_date',
        'council_comp', 'council_comp_file_date',
        'mayor_comp', 'mayor_comp_file_date',
        'mac_comp', 'mac_comp_file_date',
        'public_comp', 'public_comp_file_date',
        'other_comp', 'other_comp_file_date', 'anycomplaint',
        'cod_condemed_status', 'cod_current_violations', 'cod_current_bh_lead_violations',
        # Evictions
        'cases_filed_2016', 'cases_filed_2017', 'cases_filed_2018',
        'cases_filed_2019', 'cases_filed_2020', 'cases_filed_2021',
        'cases_filed_2022', 'cases_filed_2023', 'cases_filed_2024', 'cases_filed_2025',
        'evict_case_number', 'evict_case_status', 'evict_disp_status', 'evict_yr',
        # Rental & housing programs
        'rentalreg', 'sect8', 'sect8_cnty', 'hud',
        'RR_File_Date', 'RR_units', 'RR_status', 'RR_owner', 'RR_owner_add', 'RR_owner_state',
        # Permits
        'last_permit_per_id', 'last_permit_category', 'last_permit_file_date',
        # WRLC 2023 survey
        'wrlc23_category', 'wrlc23_property_use', 'wrlc23_results',
        'wrlc23_roof', 'wrlc23_siding', 'wrlc23_windows', 'wrlc23_porch',
        'wrlc23_peeling_paint', 'wrlc23_garage', 'wrlc23_dumping',
        # TCI 2015
        'tci2015_survey_grade', 'tci2015_survey_date',
        # Sales
        'date', 'lsaleamt',
        # Compliance
        'compliance_acc', 'compliance_acc_dt',
    ]),
    'tt_bill_sep2026.sas7bdat': ('tax_bill.parquet', [
        'TAX_YEAR', 'PPN', 'PROPERTY_NUMBER', 'PROPERTY_TYPE', 'CLASSIFICATION_DESCR',
        'PRIMARY_OWNER_NAME', 'SECONDARY_OWNER_NAME',
        'MAIL_STREET_NUMBER', 'MAIL_STREET_DIRECTION', 'MAIL_STREET_NAME',
        'MAIL_STREET_SUFFIX', 'MAIL_CITY', 'MAIL_STATE', 'MAIL_ZIPCODE',
        'LENDER',
        'TAX_MARKET_LAND', 'TAX_MARKET_IMPROVEMENT', 'TAX_MARKET_TOTAL',
        'TWOANDONEHALF_CREDIT_1ST', 'NET_TAX_DELQ_DUE',
        'GRAND_TOTAL_OWED', 'GRAND_TOTAL_PAID', 'GRAND_TOTAL_BALANCE',
        'HOMESTEAD_FLAG', 'FORECLOSURE_FLAG', 'PAYMENT_PLAN_FLAG',
        'CERT_PEND_FLAG', 'CERT_SOLD_FLAG', 'BOR_STATUS',
    ]),
    'msales.sas7bdat': ('sales.parquet', [
        'PROPERTY_NUMBER', 'GRANTEE1', 'GRANTOR1', 'mdate',
        'SALES_AMOUNT', 'DEED_TYPE', 'SALE_VALID',
        'multiproperty_sale', 'NUMBER_OF_PROPERTIES_IN_SALE',
        'MONTH_OF_SALE', 'YEAR_OF_SALE',
        'INSTRUMENT_DATE', 'RECORDED_DATE',
        'TRANSFER_TYPE_DESCR', 'EXEMPTCODE_DESCR',
    ]),
    'property.sas7bdat': ('parcel_history.parquet', [
        'parcel', 'taxyr', 'pclass', 'luc', 'owner',
        'propsize', 'totbldgs', 'condition', 'units', 'yrbuilt',
        'style', 'bedrooms', 'baths', 'mktval', 'mktland', 'mktbldg',
        'ownerocc', 'red25', 'homestd', 'taxabate',
    ]),
}

FILTER = {
    'property.sas7bdat': ('taxyr', 2010),  # only keep taxyr >= 2010
}


# ── helpers ────────────────────────────────────────────────────────────────────

def is_stale(sas_path, parquet_path):
    """True if parquet doesn't exist or SAS file is newer."""
    if not os.path.exists(parquet_path):
        return True
    return os.path.getmtime(sas_path) > os.path.getmtime(parquet_path)


def safe_cols(wanted, available):
    avail = set(available)
    kept = [c for c in wanted if c in avail]
    missing = [c for c in wanted if c not in avail]
    if missing:
        print(f'  skipped (not in file): {missing}')
    return kept


def export_table(sas_file, out_name, wanted_cols, filter_col=None, filter_min=None, chunksize=50000):
    sas_path = SAS_DIR + sas_file
    out_path = OUT_DIR + out_name

    if not is_stale(sas_path, out_path):
        print(f'  {out_name} up to date, skipping')
        return False

    print(f'  exporting {sas_file} → {out_name}')
    _, meta = pyreadstat.read_sas7bdat(sas_path, metadataonly=True)
    cols = safe_cols(wanted_cols, meta.column_names)

    if filter_col and filter_col in cols:
        chunks = []
        reader = pyreadstat.read_file_in_chunks(
            pyreadstat.read_sas7bdat, sas_path,
            chunksize=chunksize, usecols=cols, encoding='latin1'
        )
        for chunk_df, _ in reader:
            chunk_df = chunk_df[chunk_df[filter_col] >= filter_min]
            if not chunk_df.empty:
                chunks.append(chunk_df)
        df = pd.concat(chunks, ignore_index=True)
    else:
        df, _ = pyreadstat.read_sas7bdat(sas_path, usecols=cols, encoding='latin1')

    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].where(df[col].isna(), df[col].astype(str).str.upper().str.strip())

    df.to_parquet(out_path, compression='snappy', index=False)
    print(f'  wrote {out_path}  ({os.path.getsize(out_path)/1024/1024:.0f} MB)')
    return True


def upload_all():
    # S3 upload is not used in the current internal-hosting setup.
    # Parquet files are written directly to C:\nst\data\ and served from there.
    # Re-enable this (and restore the boto3 import) if we ever move to cloud hosting.
    print('  S3 upload skipped (internal hosting mode)')


# ── main ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('=== NST sync started ===')

    any_updated = False
    for sas_file, (out_name, cols) in EXPORTS.items():
        fc, fm = FILTER.get(sas_file, (None, None))
        updated = export_table(sas_file, out_name, cols, filter_col=fc, filter_min=fm)
        any_updated = any_updated or updated

    if any_updated:
        print('\n=== uploading to S3 ===')
        upload_all()
        print('\n=== sync complete — data updated ===')
    else:
        print('\n=== all tables up to date, nothing uploaded ===')
