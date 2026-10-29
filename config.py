"""Shared constants: paths, auth, colors, column groups, mappings."""

PARQUET_DIR = 'data/parquets917'

SITE_PASSWORD = "poverty2026center"

COLOR_NAVY = "#003071"
COLOR_GOLD = "#FFD700"
COLOR_LIGHT_GRAY = "#f8f9fc"

# Columns the Datasets page actually touches; lets DuckDB skip unused columns.
_NEEDED_COLS = {
    'PARCEL', 'address', 'number', 'street', 'NEIGHBOR10', 'CLASSIFICATION_DESCR',
    'condition', 'yrbuilt', 'parcel_status',
    'ward2025', 'zip', 'cuyregion', 'tract', 'cia14_name', 'LATITUDE', 'LONGITUDE',
    'PRIMARY_OWNER_NAME', 'MAIL_STATE', 'lsaleamt', 'date',
    'combovac', 'vl', 'lbvl', 'unoccupied', 'active_condemn', 'city_lb_flag',
    'pclass', 'luc', 'propsize', 'numstory', 'basesqft', 'style', 'rextwall',
    'bedrooms', 'baths', 'totbldgs', 'units', 'zone_desc',
    'TAX_MARKET_TOTAL', 'TAX_MARKET_LAND', 'TAX_MARKET_IMPROVEMENT',
    'currentvalue2023', 'proposedvalue2024', 'NET_TAX_DELQ_DUE', 'assessment',
    'PAYMENT_PLAN_FLAG', 'HOMESTEAD_FLAG', 'taxabate',
    'CERT_PEND_FLAG', 'CERT_SOLD_FLAG', 'BOR_STATUS',
    'FORECLOSURE_FLAG', 'lstatus', 'caseno', 'cdesig', 'fo_deed_count',
    'cclrc', 'disp_status', 'demo_status', 'rehab_status',
    'lsc_stat', 'lsc_issue_dt', 'lead_rollout',
    'violation', 'violation_vin', 'violation_file_date', 'violation_vtype', 'violation_task_status',
    'cdc_comp', 'council_comp', 'mayor_comp', 'mac_comp', 'public_comp',
    'cod_current_bh_lead_violations',
    'evict_case_number', 'evict_case_status', 'evict_yr', 'evict_disp_status',
    'cases_filed_2021', 'cases_filed_2022', 'cases_filed_2023', 'cases_filed_2024', 'cases_filed_2025',
    'rentalreg', 'sect8', 'sect8_cnty', 'hud', 'RR_status', 'RR_owner',
    'last_permit_per_id', 'last_permit_category', 'last_permit_file_date',
    'wrlc23_category', 'wrlc23_property_use', 'wrlc23_results',
    'wrlc23_roof', 'wrlc23_siding', 'wrlc23_windows', 'wrlc23_porch',
    'wrlc23_peeling_paint', 'wrlc23_garage', 'wrlc23_dumping',
}

_PROP_TYPE = {
    'SINGLE FAMILY DWELLING': 'Single-Family Home',
    'TWO FAMILY DWELLING': 'Two-Family Home',
    'THREE FAMILY DWELLING': 'Three-Family Home',
    'RESIDENTIAL CONDOMINIUM': 'Condominium',
    'RESIDENTIAL VACANT LAND': 'Vacant Land (Residential)',
    'COMMERCIAL VACANT LAND': 'Vacant Land (Commercial)',
    'INDUSTRIAL VACANT LAND': 'Vacant Land (Industrial)',
    'LISTED WITH': 'Other / Uncategorized',
    'EXEMPT CITY LANDBANK': 'City Land Bank',
    'EXEMPT COUNTY LANDBANK': 'County Land Bank',
    'EXEMPT OHIO OWNED': 'State Owned',
    'EXEMPT CITY / VILLAGE OWNED': 'City / Village Owned',
    'EXEMPT RELIGIOUS USE': 'Religious Use',
    'EXEMPT CHARITABLE USES': 'Charitable Use',
    'EXEMPT BOE OWNED': 'Board of Education',
    'EXEMPT PARK DISTRICT OWNED': 'Park District',
    'EXEMPT SEWER DISTRICT': 'Sewer District',
    'EXEMPT UTILITY': 'Utility',
    'HOUSE TRAILER': 'Mobile Home',
    'COMMON AREA': 'Common Area',
    'OTHER RESIDENTIAL STRUCTURES': 'Other Residential',
    'OTHER COMMERCIAL STRUCTURES': 'Other Commercial',
    'MANUFACTURING AND ASSEMBLY LIGHT': 'Light Industrial',
    'GENERAL RETAIL WITH WALK-UP APARTMENTS': 'Retail with Apartments',
    'SMALL (UNDER 7500 SF) DETACHED RETAIL STORES': 'Small Retail',
    'COMMERCIAL WAREHOUSE (GEN-UNDER 75 000 SF)': 'Commercial Warehouse',
    'APARTMENTS 1-6 UNITS': 'Apartment (1-6 Units)',
    'APARTMENTS 7-19 (WALK-UP)': 'Apartment (7-19 Units)',
    'OFFICE BUILDINGS - 1 AND 2 STORIES': 'Office Building (1-2 Stories)',
    'AUTO REPAIR GARAGE': 'Auto Repair',
    'SMALL SHOPS (MACHINE TOOL AND DIE ETC.)': 'Small Industrial Shop',
}

_COND = {'EX': 'Excellent', 'VG': 'Very Good', 'G': 'Good', 'AVG': 'Average',
         'F': 'Fair', 'P': 'Poor', 'PR': 'Poor', 'VP': 'Very Poor', 'US': 'Unsound'}

COL_GROUPS = {
    "Core": ["PARCEL", "number", "street", "address", "NEIGHBOR10", "CLASSIFICATION_DESCR", "yrbuilt", "condition", "parcel_status"],
    "General Info": ["PRIMARY_OWNER_NAME", "lsaleamt", "date", "MAIL_STATE"],
    "Use / Occupancy": ["combovac", "vl", "lbvl", "unoccupied", "active_condemn", "city_lb_flag"],
    "Property Characteristics": ["pclass", "luc", "propsize", "numstory", "basesqft", "style", "rextwall", "bedrooms", "baths", "totbldgs", "units", "zone_desc"],
    "Values & Taxes": ["TAX_MARKET_TOTAL", "TAX_MARKET_LAND", "TAX_MARKET_IMPROVEMENT", "currentvalue2023", "proposedvalue2024", "lsaleamt", "NET_TAX_DELQ_DUE", "assessment", "PAYMENT_PLAN_FLAG", "HOMESTEAD_FLAG", "taxabate"],
    "Foreclosure & Forfeiture": ["FORECLOSURE_FLAG", "lstatus", "caseno", "cdesig", "fo_deed_count"],
    "Land Bank": ["city_lb_flag", "cclrc", "disp_status", "demo_status", "rehab_status"],
    "Lead Safe Certifications": ["lsc_stat", "lsc_issue_dt", "lead_rollout"],
    "Violations (CLE Only)": ["active_condemn", "violation", "violation_vin", "violation_file_date", "violation_vtype", "violation_task_status", "cdc_comp", "council_comp", "mayor_comp", "mac_comp", "public_comp"],
    "Evictions (CLE Only)": ["evict_case_number", "evict_case_status", "evict_yr", "evict_disp_status", "cases_filed_2021", "cases_filed_2022", "cases_filed_2023", "cases_filed_2024", "cases_filed_2025"],
    "Geographies": ["NEIGHBOR10", "ward2025", "zip", "cuyregion", "tract", "cia14_name", "LATITUDE", "LONGITUDE"],
    "Rental & Housing Programs": ["rentalreg", "sect8", "sect8_cnty", "hud", "RR_status", "RR_owner"],
    "Permits (CLE Only)": ["last_permit_per_id", "last_permit_category", "last_permit_file_date"],
    "WRLC Survey 2023": ["wrlc23_category", "wrlc23_property_use", "wrlc23_results", "wrlc23_roof", "wrlc23_siding", "wrlc23_windows", "wrlc23_porch", "wrlc23_peeling_paint", "wrlc23_garage", "wrlc23_dumping"],
}

PRESET_COLUMNS = {
    "Basic Info": ["PARCEL", "address", "NEIGHBOR10", "CLASSIFICATION_DESCR", "yrbuilt", "condition", "PRIMARY_OWNER_NAME"],
    "For Sale Research": ["PARCEL", "address", "NEIGHBOR10", "CLASSIFICATION_DESCR", "TAX_MARKET_TOTAL", "currentvalue2023", "lsaleamt", "date", "PRIMARY_OWNER_NAME", "FORECLOSURE_FLAG", "city_lb_flag", "lstatus"],
    "Violation Analysis": ["PARCEL", "address", "NEIGHBOR10", "active_condemn", "violation", "violation_vtype", "cdc_comp", "lsc_stat", "cod_current_bh_lead_violations"],
    "Tax Analysis": ["PARCEL", "address", "NEIGHBOR10", "TAX_MARKET_TOTAL", "NET_TAX_DELQ_DUE", "assessment", "HOMESTEAD_FLAG", "taxabate", "PAYMENT_PLAN_FLAG", "FORECLOSURE_FLAG"],
}

COLUMN_LABELS = {
    "PARCEL": "Parcel ID", "number": "Street #", "street": "Street Name",
    "address": "Address", "NEIGHBOR10": "Neighborhood", "LATITUDE": "Latitude",
    "LONGITUDE": "Longitude", "CLASSIFICATION_DESCR": "Property Type",
    "yrbuilt": "Year Built", "condition": "Condition", "parcel_status": "Parcel Status",
    "PRIMARY_OWNER_NAME": "Owner Name", "MAIL_STATE": "Owner State",
    "pclass": "Property Class", "luc": "Land Use Code", "zone_desc": "Zoning",
    "propsize": "Lot Size (sqft)", "numstory": "Stories", "basesqft": "Bldg Sqft",
    "bedrooms": "Bedrooms", "baths": "Bathrooms", "units": "Units",
    "style": "Style", "rextwall": "Exterior Wall", "totbldgs": "# Buildings",
    "TAX_MARKET_TOTAL": "Market Value", "TAX_MARKET_LAND": "Land Value",
    "TAX_MARKET_IMPROVEMENT": "Improvement Value", "currentvalue2023": "Value 2023",
    "proposedvalue2024": "Proposed Value 2024", "NET_TAX_DELQ_DUE": "Tax Delinquent ($)",
    "HOMESTEAD_FLAG": "Homestead", "PAYMENT_PLAN_FLAG": "Payment Plan",
    "taxabate": "Tax Abatement", "FORECLOSURE_FLAG": "In Foreclosure",
    "lstatus": "Foreclosure Status", "caseno": "Case #", "cdesig": "Case Designation",
    "fo_deed_count": "Fiscal Officer Deeds", "city_lb_flag": "City Land Bank",
    "cclrc": "CCLRC", "disp_status": "Disposition Status", "demo_status": "Demo Status",
    "rehab_status": "Rehab Status", "combovac": "Vacant", "vl": "Vacant Lot",
    "lbvl": "Land Bank Vacant Lot", "unoccupied": "Unoccupied", "active_condemn": "Active Condemnation",
    "lsc_stat": "Lead Safe Status", "lsc_issue_dt": "LSC Issue Date", "lead_rollout": "Lead Rollout Quarter",
    "violation": "Has Violation", "violation_vtype": "Violation Type",
    "violation_file_date": "Violation Date", "violation_task_status": "Violation Status",
    "cdc_comp": "CDC Complaint", "council_comp": "Council Complaint",
    "mayor_comp": "Mayor Complaint", "mac_comp": "MAC Complaint", "public_comp": "Public Complaint",
    "anycomplaint": "Any Complaint", "other_comp": "Other Complaint",
    "cod_current_bh_lead_violations": "B&H Lead Violation",
    "cod_condemed_status": "COD Condemned Status", "cod_current_violations": "COD Violations",
    "cases_filed_2016": "Evictions 2016", "cases_filed_2017": "Evictions 2017",
    "cases_filed_2018": "Evictions 2018", "cases_filed_2019": "Evictions 2019",
    "cases_filed_2020": "Evictions 2020", "cases_filed_2021": "Evictions 2021",
    "cases_filed_2022": "Evictions 2022", "cases_filed_2023": "Evictions 2023",
    "cases_filed_2024": "Evictions 2024", "cases_filed_2025": "Evictions 2025",
    "evict_case_number": "Eviction Case #", "evict_case_status": "Eviction Status",
    "evict_disp_status": "Eviction Disposition", "evict_yr": "Eviction Year",
    "rentalreg": "Rental Registered", "sect8": "Section 8", "sect8_cnty": "Section 8 (County)",
    "hud": "HUD", "RR_status": "Rental Registry Status", "RR_owner": "Rental Registry Owner",
    "RR_File_Date": "Rental Registry Date", "RR_units": "Rental Registry Units",
    "RR_owner_add": "Rental Owner Address", "RR_owner_state": "Rental Owner State",
    "last_permit_per_id": "Last Permit ID", "last_permit_category": "Last Permit Type",
    "last_permit_file_date": "Last Permit Date",
    "wrlc23_category": "WRLC Category", "wrlc23_property_use": "WRLC Property Use",
    "wrlc23_results": "WRLC Result", "wrlc23_roof": "Roof", "wrlc23_siding": "Siding",
    "wrlc23_windows": "Windows", "wrlc23_porch": "Porch", "wrlc23_peeling_paint": "Peeling Paint",
    "wrlc23_garage": "Garage", "wrlc23_dumping": "Dumping",
    "tci2015_survey_grade": "TCI 2015 Grade", "tci2015_survey_date": "TCI 2015 Date",
    "ward2025": "Ward (2025)", "zip": "ZIP Code", "cuyregion": "Cuyahoga Region",
    "cia14_name": "CIA Area", "tract": "Census Tract", "PPN": "PPN",
    "assessment": "Assessed Value", "CERT_PEND_FLAG": "Cert Pending",
    "CERT_SOLD_FLAG": "Cert Sold", "BOR_STATUS": "BOR Status",
    "violation_vin": "Violation #", "compliance_acc": "Compliance Accepted",
    "compliance_acc_dt": "Compliance Date",
    "date": "Last Sale Date", "lsaleamt": "Last Sale Price",
}

# Neighborhood shapefile name differences from the parcel dataset.
NAME_FIX = {
    "KAMM'S": "KAMMS",
    "CHAGRIN FALLS": "CHAGRIN FALLS TOWNSHIP",
    "MAYFIELD": "MAYFIELD VILLAGE",
    "OLMSTED": "OLMSTED TOWNSHIP",
}

# Distressed-rentals date window (matches the R reference implementation).
DR_START = "2021-01-01"
DR_END = "2026-07-31"

_OWNER_PATTERNS = {
    # Order matters: non-profit/govt first so a LAND BANK LLC maps to Non-Profit
    "Non-Profit/Government": (
        r"CITY OF|COUNTY OF|STATE OF|TOWNSHIP|DEPARTMENT|DEPT|AUTHORITY|"
        r"COMMISSION|BOARD OF|UNITED STATES|FEDERAL|MUNICIPAL|CHURCH|"
        r"DIOCESE|PARISH|MINISTRY|MINISTRIES|FOUNDATION|CHARITABLE|"
        r"NONPROFIT|NON-PROFIT|HABITAT FOR HUMANITY|LAND BANK|PUBLIC|"
        r"SCHOOL|UNIVERSITY|COLLEGE|HOSPITAL|HEALTH SYSTEM|CMHA|CHN"
    ),
    "Corporate Entity": (
        r"LLC|L\.L\.C|INC|CORP|CO\.|LTD|LP|L\.P|HOLDINGS|PROPERTIES|"
        r"REALTY|INVESTMENTS|VENTURES|PARTNERS|PARTNERSHIP|GROUP|"
        r"ENTERPRISES|ASSOCIATES|MGMT|MANAGEMENT|DEVELOPMENT|DEVELOPERS|"
        r"REAL ESTATE|ACQUISITIONS|CAPITAL|ASSETS|SOLUTIONS|SERVICES|"
        r"FUND|EQUITY|PORTFOLIO|COMPANIES|BANK"
    ),
    "Trust": r"TRUST|TRUSTEE| TR | T\.R\.|LIVING TRUST|FAMILY TRUST|REVOCABLE|IRREVOCABLE",
    "Joint Ownership": r" & | AND |\bJT\b|JOINT|JTWROS|JT TEN|JT\. TEN",
}
