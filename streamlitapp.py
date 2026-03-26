"""
NST 2.0 — Cleveland Neighborhood Strategy Technology
=====================================================
Streamlit web app for exploring Cleveland property data.
Developed by CWRU Poverty Center.

DATA SOURCE: data/nst_sample_data.csv (5,000 synthetic properties, 35 columns)
    See data/sampledatadictionary.md for column definitions.
    Replace with real DB queries for production.

ROUTING: Single-file app using URL query params for page navigation.
    ?page=home              → Home / landing page (default)
    ?page=datasets          → Dataset browser with filters + export
    ?page=maps              → Map explorer (all neighborhoods)
    ?page=maps&hood=<name>  → Neighborhood profile (stats + download)
    ?page=property-search   → Single property lookup

IMPORTANT: All <a> tags MUST use target="_self" or they open in a new tab
    (Streamlit runs inside an iframe).

COLOR SCHEME: Navy #003071, Gold #FFD700, Light gray #f8f9fc
FONT: Inter (Google Fonts)
"""

# ============================================================
#  IMPORTS
# ============================================================
import streamlit as st
import base64
import pandas as pd
import json
import io
import zipfile

# ============================================================
#  SETUP — Assets, page config, routing
# ============================================================

# Load logo images and encode as base64 for use in HTML
def get_base64_image(image_path):
    """Convert an image file to a base64 string for embedding in HTML."""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

navbar_logo_base64 = get_base64_image("assets/upperleft logo.jpg")
hero_backdrop_base64 = get_base64_image("assets/cleveland backdrop.jpg")
partner_cleveland_base64 = get_base64_image("assets/partner_cleveland.svg")
partner_cuyahoga_base64 = get_base64_image("assets/updated_Cuyahoga_County_logo.svg")
partner_cclrc_base64 = get_base64_image("assets/partner_cclrc.svg")
partner_census_base64 = get_base64_image("assets/partner_census.svg")

# Streamlit page config (must be first st. call)
st.set_page_config(
    page_title="Cleveland NST 2.0",
    page_icon="assets/updated_nst_favicon.svg",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
#  PASSWORD GATE
#  Uses an &auth=1 query param so navigation links keep the
#  user logged in across page reloads.
# ============================================================
SITE_PASSWORD = "poverty2026center"  # Change this!

def check_password():
    """Returns True if the user is authenticated."""
    # Already authenticated via query param
    if st.query_params.get("auth") == "1":
        return True

    def password_entered():
        if st.session_state["password"] == SITE_PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            # Add auth=1 to current URL so it persists across link clicks
            params = dict(st.query_params)
            params["auth"] = "1"
            st.query_params.update(params)
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct"):
        return True

    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("Password incorrect")
    return False

if not check_password():
    st.stop()

# Read URL query params to determine which page to show
query_params = st.query_params
current_page = query_params.get("page", "home")

# ============================================================
#  GLOBAL CSS — Shared styles across all pages
#  Includes: navbar, hero, data cards, partners, buttons
# ============================================================
st.markdown("""
    <style>
    /* --- Font --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    /* --- Navbar ---
       Uses negative margins to break out of Streamlit's container padding.
       Dropdowns are full-width overlays (position: fixed). */
    .navbar {
        background-color: white;
        padding: 0;
        margin: 0;
        margin-top: -80px;
        margin-left: -100px;
        margin-right: -100px;
        border-bottom: 2px solid #000000;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .navbar-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 3rem;
    }
    .navbar-brand {
        display: flex;
        align-items: center;
    }
    .navbar-brand img {
        height: 80px;
        width: auto;
    }
    .navbar-menu {
        display: flex;
        list-style: none;
        margin: 0;
        padding: 0;
        gap: 2rem;
        align-items: center;
    }
    .navbar-item {
        position: relative;
        display: inline-block;
    }
    .navbar-link {
        color: #003071;
        text-decoration: none !important;
        padding: 1rem 0;
        display: inline-block;
        font-size: 1.4rem;
        font-weight: 600;
        transition: color 0.2s;
        cursor: pointer;
    }
    .navbar-link:link, .navbar-link:visited, .navbar-link:active {
        text-decoration: none !important;
    }
    .navbar-link:hover {
        color: #003071;
    }
    /* Dropdown arrow after nav links (except Home) */
    .navbar-link::after {
        content: " ▼";
        font-size: 0.7rem;
        margin-left: 0.4rem;
    }
    .navbar-link-home::after {
        content: none;
    }
    /* Full-width dropdown panel */
    .dropdown-menu {
        display: none;
        position: fixed;
        background-color: white;
        width: 100vw;
        left: 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border-top: 2px solid #000000;
        z-index: 1001;
        padding: 3rem 6rem;
    }
    .navbar-item:hover .dropdown-menu {
        display: block;
    }
    .dropdown-item {
        color: #003071 !important;
        padding: 1.5rem 0;
        text-decoration: none !important;
        display: block;
        transition: all 0.2s;
        border-bottom: 1px solid #e0e0e0;
    }
    .dropdown-item:last-child {
        border-bottom: none;
    }
    .dropdown-item:hover {
        padding-left: 0.5rem;
    }
    .dropdown-item-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: #003071;
        margin-bottom: 0.3rem;
    }
    .dropdown-item-description {
        font-size: 1rem;
        font-weight: 400;
        color: #666;
        line-height: 1.4;
    }
    .dropdown-item:hover .dropdown-item-title {
        color: #FFD700;
    }

    /* --- Hero Section (home page banner) --- */
    .hero-section {
        position: relative;
        width: calc(100% + 200px);
        margin-left: -100px;
        margin-right: -100px;
        margin-top: 0;
        height: 500px;
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
    }
    .hero-overlay {
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0, 48, 113, 0.6);
    }
    .hero-content {
        position: relative;
        z-index: 1;
        color: white;
        padding: 2rem;
    }
    .hero-subtitle {
        font-size: 1.5rem;
        font-weight: 600;
        letter-spacing: 3px;
        margin-bottom: 1rem;
        color: #FFD700;
    }
    .hero-title {
        font-size: 4rem;
        font-weight: 700;
        line-height: 1.2;
        margin-bottom: 2rem;
        text-transform: uppercase;
    }
    .hero-buttons {
        display: flex;
        gap: 2rem;
        justify-content: center;
        margin-top: 2rem;
    }
    .hero-button {
        padding: 1rem 2.5rem;
        border: 2px solid white;
        background-color: transparent;
        color: white !important;
        font-size: 1.3rem;
        font-weight: 600;
        text-decoration: none !important;
        transition: all 0.3s;
        cursor: pointer;
    }
    .hero-button:hover {
        background-color: white;
        color: #003071;
    }

    /* --- Get Started Cards (home page) --- */
    .data-section-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        color: #003071;
        margin: 3rem 0 2rem 0;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .data-cards-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 2rem;
        margin: 2rem 0;
    }
    .data-card {
        background-color: white;
        border: 2px solid #003071;
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
        transition: transform 0.3s, box-shadow 0.3s;
    }
    .data-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0,48,113,0.2);
    }
    .data-card-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        color: #003071;
    }
    .data-card-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #003071;
        margin-bottom: 1.5rem;
        text-transform: uppercase;
    }
    .data-card-links {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    .data-card-link {
        padding: 0.5rem 0;
        border-bottom: 1px solid #e0e0e0;
    }
    .data-card-link:last-child {
        border-bottom: none;
    }
    .data-card-link a {
        color: #003071;
        text-decoration: none;
        font-weight: 500;
        transition: color 0.2s;
    }
    .data-card-link a:hover {
        color: #FFD700;
    }

    /* --- Partners Section (home page) --- */
    .partners-section-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        color: #003071;
        margin: 3rem 0 3rem 0;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .partners-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 3rem;
        margin: 3rem auto;
        max-width: 1400px;
        align-items: center;
    }
    .partner-logo {
        background-color: transparent;
        padding: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100px;
        transition: transform 0.3s;
    }
    .partner-logo:hover {
        transform: scale(1.05);
    }
    .partner-logo img {
        max-width: 100%;
        max-height: 80px;
        object-fit: contain;
    }

    /* --- Contribute Section (home page) --- */
    .contribute-section {
        background-color: #f5f5f5;
        padding: 4rem 3rem;
        text-align: center;
        margin: 4rem 0;
    }
    .contribute-title {
        font-size: 1.8rem;
        font-weight: 500;
        color: #333;
        margin-bottom: 2rem;
        font-family: 'Inter', sans-serif;
    }
    .contribute-button {
        display: inline-block;
        padding: 1rem 2.5rem;
        background-color: #FFD700;
        color: #003071 !important;
        font-size: 1.2rem;
        font-weight: 700;
        text-decoration: none !important;
        border: 2px solid #333;
        transition: all 0.3s;
        cursor: pointer;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .contribute-button:hover {
        background-color: #FFC700;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }

    /* --- Layout overrides --- */
    .main .block-container {
        padding-top: 0rem;
    }
    .main-header {
        text-align: center;
        padding: 2rem 0;
    }
    .main-title {
        font-size: 3.5rem;
        font-weight: bold;
        color: #003071;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.5rem;
        color: #666;
        margin-bottom: 3rem;
    }
    .nav-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
        padding: 2rem 0;
    }
    .stButton > button {
        width: 100%;
        height: 150px;
        font-size: 1.5rem;
        font-weight: bold;
        border-radius: 10px;
        border: 2px solid #003071;
        background-color: white;
        color: #003071;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #003071;
        color: white;
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================
#  NAVBAR — Shown on every page
#  To add a new page: add a dropdown-item with href="?auth=1&page=<name>"
#  IMPORTANT: always include target="_self" on links
# ============================================================
st.markdown(f"""
    <div class="navbar">
        <div class="navbar-container">
            <div class="navbar-brand">
                <a href="?auth=1&page=home" target="_self"><img src="data:image/jpeg;base64,{navbar_logo_base64}" alt="Cleveland NST Logo"></a>
            </div>
            <ul class="navbar-menu">
                <li class="navbar-item">
                    <a href="?auth=1&page=home" target="_self" class="navbar-link navbar-link-home">Home</a>
                </li>
                <li class="navbar-item">
                    <a href="#" class="navbar-link">Data</a>
                    <div class="dropdown-menu">
                        <a href="?auth=1&page=datasets" target="_self" class="dropdown-item">
                            <div class="dropdown-item-title">Datasets</div>
                            <div class="dropdown-item-description">Browse and download comprehensive neighborhood data</div>
                        </a>
                        <a href="?auth=1&page=maps" target="_self" class="dropdown-item">
                            <div class="dropdown-item-title">Interactive Maps</div>
                            <div class="dropdown-item-description">Visualize Cleveland data on interactive maps</div>
                        </a>
                    </div>
                </li>
                <li class="navbar-item">
                    <a href="#" class="navbar-link">Our Work</a>
                    <div class="dropdown-menu">
                        <a href="https://case.edu/socialwork/povertycenter/about" target="_blank" class="dropdown-item">
                            <div class="dropdown-item-title">About</div>
                            <div class="dropdown-item-description">Learn about NST and our mission</div>
                        </a>
                        <a href="?auth=1&page=methodology" target="_self" class="dropdown-item">
                            <div class="dropdown-item-title">Methodology</div>
                            <div class="dropdown-item-description">Our data collection and analysis approach</div>
                        </a>
                        <a href="?auth=1&page=projects" target="_self" class="dropdown-item">
                            <div class="dropdown-item-title">Projects</div>
                            <div class="dropdown-item-description">Dedicated pages for each of our projects</div>
                        </a>
                    </div>
                </li>
                <li class="navbar-item">
                    <a href="#" class="navbar-link">Resources</a>
                    <div class="dropdown-menu">
                        <a href="?auth=1&page=resources" target="_self" class="dropdown-item">
                            <div class="dropdown-item-title">Resources</div>
                            <div class="dropdown-item-description">Tools and guides for using NST data</div>
                        </a>
                        <a href="?auth=1&page=contact" target="_self" class="dropdown-item">
                            <div class="dropdown-item-title">Contact</div>
                            <div class="dropdown-item-description">How to reach us or work with us</div>
                        </a>
                    </div>
                </li>
            </ul>
        </div>
    </div>
""", unsafe_allow_html=True)


# ############################################################
#  PAGE ROUTING
#  Each page is an if/elif block. To add a new page:
#    1. Add elif current_page == "your-page":
#    2. Add a navbar link with href="?auth=1&page=your-page"
# ############################################################

if current_page == "datasets":
    # ========================================================
    #  DATASETS PAGE — Browse, filter, and export property data
    #  Simple filters always visible; Advanced filters in expanders.
    #  Filter presets for common research tasks.
    #  Column selector with presets.
    #  Results: Table, Map, Charts, Summary tabs + Export.
    # ========================================================

    @st.cache_data
    def load_data():
        return pd.read_csv("data/nstsample.csv", low_memory=False)

    df = load_data()

    # ---- Column groups for the column selector ----
    COL_GROUPS = {
        "Core": ["PARCEL", "number", "street", "address", "NEIGHBOR10", "CLASSIFICATION_DESCR", "yrbuilt", "condition", "parcel_status"],
        "General Info": ["PRIMARY_OWNER_NAME", "towner", "lsaleamt", "date", "deed", "LENDER", "MAIL_STATE", "MAIL_CITY", "ownerupdate"],
        "Use / Occupancy": ["vacantlot_type", "combovac", "vl", "lbvl", "unoccupied", "active_condemn", "city_lb_flag"],
        "Property Characteristics": ["pclass", "luc", "propsize", "front", "depth", "lotshape", "numstory", "basesqft", "totusabl", "style", "rextwall", "bedrooms", "baths", "halfbath", "totbldgs", "units", "zone_desc"],
        "Values & Taxes": ["TAX_MARKET_TOTAL", "TAX_MARKET_LAND", "TAX_MARKET_IMPROVEMENT", "currentvalue2023", "proposedvalue2024", "lsaleamt", "NET_TAX_DELQ_DUE", "GRAND_TOTAL_BALANCE", "GRAND_TOTAL_OWED", "GRAND_TOTAL_PAID", "PAYMENT_PLAN_FLAG", "HOMESTEAD_FLAG", "taxabate"],
        "Foreclosure & Forfeiture": ["FORECLOSURE_FLAG", "lstatus", "caseno", "cdesig", "fo_deed_count", "fo_last_year", "forf_deed_count", "forf_last_year", "forf_status"],
        "Land Bank": ["city_lb_flag", "city_lb_city_land_bank_type", "city_lb_transdt", "city_lb_deeded_owner", "cclrc", "disp_status", "p_source", "demo_status", "rehab_status", "public_status"],
        "Lead Safe Certifications": ["lsc_stat", "lsc_issue_dt", "lead_rollout"],
        "Violations (CLE Only)": ["active_condemn", "violation", "violation_vin", "violation_file_date", "violation_vtype", "violation_task_status", "cdc_comp", "council_comp", "mayor_comp", "mac_comp", "public_comp"],
        "Evictions (CLE Only)": ["evict_case_number", "evict_case_status", "evict_yr", "evict_disp_status", "evict_plntf_name", "cases_filed_2023", "cases_filed_2024", "evict_case_file_dt"],
        "Geographies": ["NEIGHBOR10", "ward2025", "ward", "zip", "cuyregion", "tract", "BLOCK10", "BLOCKGR10", "cia14_name", "LATITUDE", "LONGITUDE"],
        "Rental & Housing Programs": ["rentalreg", "sect8", "sect8_cnty", "hud", "RR_status", "RR_owner"],
        "Permits (CLE Only)": ["last_permit_per_id", "last_permit_category", "last_permit_file_date", "demo_per_id", "demo_per_appstatus", "bd_per_id", "bd_per_appstatus"],
        "WRLC Survey 2023": ["wrlc23_category", "wrlc23_property_use", "wrlc23_results", "wrlc23_roof", "wrlc23_siding", "wrlc23_windows", "wrlc23_porch", "wrlc23_peeling_paint", "wrlc23_garage", "wrlc23_dumping"],
    }

    PRESET_COLUMNS = {
        "Basic Info": ["PARCEL", "address", "NEIGHBOR10", "CLASSIFICATION_DESCR", "yrbuilt", "condition", "PRIMARY_OWNER_NAME", "LATITUDE", "LONGITUDE"],
        "For Sale Research": ["PARCEL", "address", "NEIGHBOR10", "CLASSIFICATION_DESCR", "TAX_MARKET_TOTAL", "currentvalue2023", "lsaleamt", "date", "PRIMARY_OWNER_NAME", "FORECLOSURE_FLAG", "city_lb_flag", "lstatus"],
        "Violation Analysis": ["PARCEL", "address", "NEIGHBOR10", "active_condemn", "violation", "violation_vtype", "cdc_comp", "lsc_stat", "cod_current_bh_lead_violations", "cod_current_cdph_lead_violations"],
        "Tax Analysis": ["PARCEL", "address", "NEIGHBOR10", "TAX_MARKET_TOTAL", "NET_TAX_DELQ_DUE", "GRAND_TOTAL_BALANCE", "GRAND_TOTAL_OWED", "GRAND_TOTAL_PAID", "PAYMENT_PLAN_FLAG", "FORECLOSURE_FLAG"],
    }

    # ---- Page CSS ----
    st.markdown("""
        <style>
        .breadcrumb { font-size: 0.95rem; color: #666; margin-bottom: 1.5rem; }
        .breadcrumb a { color: #003071; text-decoration: none; }
        .breadcrumb a:hover { text-decoration: underline; }
        .page-header { font-size: 2.5rem; font-weight: 700; color: #003071; margin-bottom: 0.3rem; }
        .page-subtitle { font-size: 1.1rem; color: #666; margin-bottom: 1rem; }
        .stat-box { background: #f8f9fc; border-left: 4px solid #003071; padding: 1rem 1.2rem; border-radius: 4px; }
        .stat-box .stat-value { font-size: 1.6rem; font-weight: 700; color: #003071; }
        .stat-box .stat-label { font-size: 0.85rem; color: #666; }
        .preset-section { margin-bottom: 0.75rem; }
        </style>
    """, unsafe_allow_html=True)

    # ---- Breadcrumb & Header ----
    st.markdown('<div class="breadcrumb"><a href="?auth=1&page=home" target="_self">Home</a> &nbsp;/&nbsp; <strong>Datasets</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Datasets</div><div class="page-subtitle">Browse and download comprehensive property data for Cleveland and Cuyahoga County.</div>', unsafe_allow_html=True)

    # ---- Filter Preset Buttons ----
    if "ds_preset" not in st.session_state:
        st.session_state.ds_preset = None

    st.markdown('<div class="preset-section">', unsafe_allow_html=True)
    pr1, pr2, pr3, pr4, pr5, pr6 = st.columns(6)
    preset_map = {
        "Vacant Properties": pr1,
        "With Violations": pr2,
        "Tax Delinquent": pr3,
        "Out-of-State Owners": pr4,
        "In Foreclosure": pr5,
        "Lead Issues": pr6,
    }
    for p_label, p_col in preset_map.items():
        with p_col:
            is_active = st.session_state.ds_preset == p_label
            btn_label = f"✓ {p_label}" if is_active else p_label
            if st.button(btn_label, use_container_width=True, key=f"preset_{p_label}"):
                st.session_state.ds_preset = None if is_active else p_label
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ---- Search Bar ----
    search_query = st.text_input(
        "search",
        placeholder="Search by address, parcel ID, or owner name...",
        label_visibility="collapsed",
    )

    # ---- Always-Visible Simple Filters ----
    sf1, sf2, sf3 = st.columns(3)
    with sf1:
        neighborhoods = ["All"] + sorted(df["NEIGHBOR10"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
        f_neighborhood = st.selectbox("Neighborhood", neighborhoods, key="f_nbh")
    with sf2:
        prop_types = ["All"] + sorted(df["CLASSIFICATION_DESCR"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
        f_prop_type = st.selectbox("Property Type", prop_types, key="f_ptype")
    with sf3:
        yr_min_data = int(df["yrbuilt"].dropna().min())
        yr_max_data = int(df["yrbuilt"].dropna().max())
        f_year_range = st.slider("Year Built", yr_min_data, yr_max_data, (yr_min_data, yr_max_data), key="f_yr")

    sf4, sf5 = st.columns(2)
    with sf4:
        val_max_data = int(df["TAX_MARKET_TOTAL"].dropna().max())
        f_value_range = st.slider("Property Value ($)", 0, val_max_data, (0, val_max_data), step=5000, format="$%d", key="f_val")
    with sf5:
        conditions = ["All"] + sorted(df["condition"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
        f_condition = st.selectbox("Condition", conditions, key="f_cond")

    # Quick toggles
    tg1, tg2, tg3, tg4 = st.columns(4)
    with tg1: f_vacant = st.checkbox("Vacant only", key="f_vac")
    with tg2: f_violations = st.checkbox("Has violations", key="f_viol")
    with tg3: f_tax_del = st.checkbox("Tax delinquent", key="f_tax")
    with tg4: f_foreclosure_flag = st.checkbox("In foreclosure", key="f_fore")

    # ---- Advanced Filters ----
    with st.expander("Advanced Filters"):
        with st.expander("Property Characteristics"):
            pc1, pc2, pc3, pc4 = st.columns(4)
            with pc1:
                styles = ["All"] + sorted(df["style"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                f_style = st.selectbox("Style", styles, key="adv_style")
            with pc2:
                story_vals = sorted(df["numstory"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                story_opts = ["All"] + story_vals
                f_stories = st.selectbox("# Stories", story_opts, key="adv_stories")
            with pc3:
                zones = ["All"] + sorted(df["zone_desc"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                f_zone = st.selectbox("Zoning", zones, key="adv_zone")
            with pc4:
                pclass_vals = ["All"] + sorted(df["pclass"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                f_pclass = st.selectbox("Property Class", pclass_vals, key="adv_pclass")
            pc5, pc6, pc7 = st.columns(3)
            with pc5:
                bed_vals = sorted(df["bedrooms"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                bed_opts = ["All"] + bed_vals
                f_bed = st.selectbox("Bedrooms", bed_opts, key="adv_bed")
            with pc6:
                bath_vals = sorted(df["baths"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                bath_opts = ["All"] + bath_vals
                f_bath = st.selectbox("Bathrooms", bath_opts, key="adv_bath")
            with pc7:
                sqft_max = int(df["basesqft"].dropna().max()) if df["basesqft"].dropna().any() else 10000
                f_sqft = st.slider("Building Sq Ft", 0, sqft_max, (0, sqft_max), key="adv_sqft")

        with st.expander("Values & Taxes"):
            vt1, vt2, vt3, vt4 = st.columns(4)
            with vt1: f_homestead = st.checkbox("Homestead exemption", key="adv_home")
            with vt2: f_payment_plan = st.checkbox("On payment plan", key="adv_pp")
            with vt3: f_cert_pend = st.checkbox("Tax cert. pending", key="adv_cp")
            with vt4: f_cert_sold = st.checkbox("Tax cert. sold", key="adv_cs")
            vt5, vt6 = st.columns(2)
            with vt5:
                tax_abate_vals = ["All"] + sorted(df["taxabate"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                f_taxabate = st.selectbox("Tax Abatement Code", tax_abate_vals, key="adv_aba")
            with vt6:
                bor_vals = ["All"] + sorted(df["BOR_STATUS"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                f_bor = st.selectbox("BOR Status", bor_vals, key="adv_bor")

        with st.expander("Violations (CLE Only)"):
            vc1, vc2, vc3, vc4 = st.columns(4)
            with vc1: f_active_condemn = st.checkbox("Active condemnation", key="adv_ac")
            with vc2: f_bh_lead = st.checkbox("B&H lead violation", key="adv_bh")
            with vc3: f_cdc_comp = st.checkbox("CDC complaint", key="adv_cdc")
            with vc4: f_council_comp = st.checkbox("Council complaint", key="adv_council")
            vc5, vc6 = st.columns(2)
            with vc5:
                vtype_vals = ["All"] + sorted(df["violation_vtype"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                f_vtype = st.selectbox("Violation Type", vtype_vals, key="adv_vtype")
            with vc6:
                vtask_vals = ["All"] + sorted(df["violation_task_status"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                f_vtask = st.selectbox("Violation Task Status", vtask_vals, key="adv_vtask")

        with st.expander("Evictions (CLE Only)"):
            ev1, ev2 = st.columns(2)
            with ev1:
                evs_vals = ["All"] + sorted(df["evict_case_status"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                f_evict_status = st.selectbox("Eviction Status", evs_vals, key="adv_evs")
            with ev2:
                evd_vals = ["All"] + sorted(df["evict_disp_status"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                f_evict_disp = st.selectbox("Eviction Disposition", evd_vals, key="adv_evd")
            ev3, ev4 = st.columns(2)
            with ev3:
                evyr_vals = sorted(df["evict_yr"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist(), reverse=True)
                evyr_opts = ["All"] + evyr_vals
                f_evict_yr = st.selectbox("Eviction Year", evyr_opts, key="adv_evy")
            with ev4:
                f_evict_multi = st.checkbox("Multi-case evictions only", key="adv_evm")

        with st.expander("Lead Safe Certifications"):
            ls1, ls2 = st.columns(2)
            with ls1:
                lsc_vals = ["All"] + sorted(df["lsc_stat"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                f_lsc = st.selectbox("LSC Status", lsc_vals, key="adv_lsc")
            with ls2:
                lr_vals = ["All"] + sorted(df["lead_rollout"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                f_lead_rollout = st.selectbox("Lead Rollout Quarter", lr_vals, key="adv_lr")

        with st.expander("Foreclosure & Forfeiture"):
            ff1, ff2, ff3 = st.columns(3)
            with ff1:
                fo_vals = ["All"] + sorted(df["lstatus"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                f_fo_status = st.selectbox("Case Status", fo_vals, key="adv_fos")
            with ff2:
                fcdesig_vals = ["All"] + sorted(df["cdesig"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                f_cdesig = st.selectbox("Case Designation", fcdesig_vals, key="adv_cdesig")
            with ff3: f_has_fo_deed = st.checkbox("Has fiscal officer deed", key="adv_fod")

        with st.expander("Land Bank Status"):
            lb1, lb2, lb3 = st.columns(3)
            with lb1: f_city_lb = st.checkbox("City Land Bank", key="adv_clb")
            with lb2: f_cclrc = st.checkbox("CCLRC", key="adv_cclrc")
            with lb3:
                demo_vals = ["All"] + sorted(df["demo_status"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                f_demo_status = st.selectbox("Demo Status", demo_vals, key="adv_demo")
            lb4, lb5 = st.columns(2)
            with lb4:
                rehab_vals = ["All"] + sorted(df["rehab_status"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                f_rehab_status = st.selectbox("Rehab Status", rehab_vals, key="adv_rehab")
            with lb5:
                disp_vals = ["All"] + sorted(df["disp_status"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                f_disp_status = st.selectbox("Disposition Status", disp_vals, key="adv_disp")

        with st.expander("Geographies"):
            geo1, geo2, geo3, geo4 = st.columns(4)
            with geo1:
                ward_vals = sorted(df["ward2025"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                ward_opts = ["All"] + ward_vals
                f_ward = st.selectbox("Ward (2025)", ward_opts, key="adv_ward")
            with geo2:
                zip_vals = sorted(df["zip"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                zip_opts = ["All"] + zip_vals
                f_zip = st.selectbox("ZIP Code", zip_opts, key="adv_zip")
            with geo3:
                region_vals = ["All"] + sorted(df["cuyregion"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                f_region = st.selectbox("Cuyahoga Region", region_vals, key="adv_reg")
            with geo4:
                cia_vals = ["All"] + sorted(df["cia14_name"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                f_cia = st.selectbox("CIA Area", cia_vals, key="adv_cia")

        with st.expander("Rental & Housing Programs"):
            rh1, rh2, rh3, rh4 = st.columns(4)
            with rh1: f_rental = st.checkbox("Rental registered", key="adv_rr")
            with rh2: f_sect8 = st.checkbox("Section 8", key="adv_s8")
            with rh3: f_hud = st.checkbox("HUD", key="adv_hud")
            with rh4: f_out_of_state = st.checkbox("Out-of-state owner", key="adv_oos")

    # ---- Apply All Filters ----
    filtered_df = df.copy()

    # Preset overrides
    p = st.session_state.ds_preset
    if p == "Vacant Properties":
        filtered_df = filtered_df[filtered_df["combovac"].fillna(0) == 1]
    elif p == "With Violations":
        filtered_df = filtered_df[filtered_df["violation"].fillna(0) == 1]
    elif p == "Tax Delinquent":
        filtered_df = filtered_df[filtered_df["NET_TAX_DELQ_DUE"].fillna(0) > 0]
    elif p == "Out-of-State Owners":
        filtered_df = filtered_df[~filtered_df["MAIL_STATE"].fillna("").isin(["OH", "/", ""])]
    elif p == "In Foreclosure":
        filtered_df = filtered_df[filtered_df["FORECLOSURE_FLAG"].fillna(0) == 1]
    elif p == "Lead Issues":
        filtered_df = filtered_df[filtered_df["lsc_stat"].fillna("").astype(str) == "FAIL"]

    # Search
    if search_query:
        q = search_query.strip()
        mask = (
            filtered_df["address"].fillna("").str.contains(q, case=False, regex=False)
            | filtered_df["PARCEL"].fillna("").astype(str).str.contains(q, case=False, regex=False)
            | filtered_df["PRIMARY_OWNER_NAME"].fillna("").str.contains(q, case=False, regex=False)
        )
        filtered_df = filtered_df[mask]

    # Simple filters
    if f_neighborhood != "All":
        filtered_df = filtered_df[filtered_df["NEIGHBOR10"].astype(str) == f_neighborhood]
    if f_prop_type != "All":
        filtered_df = filtered_df[filtered_df["CLASSIFICATION_DESCR"].astype(str) == f_prop_type]
    if f_condition != "All":
        filtered_df = filtered_df[filtered_df["condition"].astype(str) == f_condition]
    filtered_df = filtered_df[
        (filtered_df["yrbuilt"].fillna(0) >= f_year_range[0]) &
        (filtered_df["yrbuilt"].fillna(9999) <= f_year_range[1])
    ]
    filtered_df = filtered_df[
        (filtered_df["TAX_MARKET_TOTAL"].fillna(0) >= f_value_range[0]) &
        (filtered_df["TAX_MARKET_TOTAL"].fillna(0) <= f_value_range[1])
    ]

    # Quick toggles
    if f_vacant:
        filtered_df = filtered_df[filtered_df["combovac"].fillna(0) == 1]
    if f_violations:
        filtered_df = filtered_df[filtered_df["violation"].fillna(0) == 1]
    if f_tax_del:
        filtered_df = filtered_df[filtered_df["NET_TAX_DELQ_DUE"].fillna(0) > 0]
    if f_foreclosure_flag:
        filtered_df = filtered_df[filtered_df["FORECLOSURE_FLAG"].fillna(0) == 1]

    # Advanced: Property Characteristics
    if f_style != "All":
        filtered_df = filtered_df[filtered_df["style"].astype(str) == f_style]
    if f_stories != "All":
        filtered_df = filtered_df[filtered_df["numstory"].astype(str) == f_stories]
    if f_zone != "All":
        filtered_df = filtered_df[filtered_df["zone_desc"].astype(str) == f_zone]
    if f_pclass != "All":
        filtered_df = filtered_df[filtered_df["pclass"].astype(str) == f_pclass]
    if f_bed != "All":
        filtered_df = filtered_df[filtered_df["bedrooms"].astype(str) == f_bed]
    if f_bath != "All":
        filtered_df = filtered_df[filtered_df["baths"].astype(str) == f_bath]
    filtered_df = filtered_df[
        (filtered_df["basesqft"].fillna(0) >= f_sqft[0]) &
        (filtered_df["basesqft"].fillna(0) <= f_sqft[1])
    ]

    # Advanced: Values & Taxes
    if f_homestead:
        filtered_df = filtered_df[filtered_df["HOMESTEAD_FLAG"].fillna(0) == 1]
    if f_payment_plan:
        filtered_df = filtered_df[filtered_df["PAYMENT_PLAN_FLAG"].fillna(0) == 1]
    if f_cert_pend:
        filtered_df = filtered_df[filtered_df["CERT_PEND_FLAG"].fillna(0) == 1]
    if f_cert_sold:
        filtered_df = filtered_df[filtered_df["CERT_SOLD_FLAG"].fillna(0) == 1]
    if f_taxabate != "All":
        filtered_df = filtered_df[filtered_df["taxabate"].astype(str) == f_taxabate]
    if f_bor != "All":
        filtered_df = filtered_df[filtered_df["BOR_STATUS"].astype(str) == f_bor]

    # Advanced: Violations
    if f_active_condemn:
        filtered_df = filtered_df[filtered_df["active_condemn"].fillna(0) == 1]
    if f_bh_lead:
        filtered_df = filtered_df[filtered_df["cod_current_bh_lead_violations"].fillna("").astype(str).str.strip().replace("nan","") != ""]
    if f_cdc_comp:
        filtered_df = filtered_df[filtered_df["cdc_comp"].fillna(0) == 1]
    if f_council_comp:
        filtered_df = filtered_df[filtered_df["council_comp"].fillna(0) == 1]
    if f_vtype != "All":
        filtered_df = filtered_df[filtered_df["violation_vtype"].astype(str) == f_vtype]
    if f_vtask != "All":
        filtered_df = filtered_df[filtered_df["violation_task_status"].astype(str) == f_vtask]

    # Advanced: Evictions
    if f_evict_status != "All":
        filtered_df = filtered_df[filtered_df["evict_case_status"].astype(str) == f_evict_status]
    if f_evict_disp != "All":
        filtered_df = filtered_df[filtered_df["evict_disp_status"].astype(str) == f_evict_disp]
    if f_evict_yr != "All":
        filtered_df = filtered_df[filtered_df["evict_yr"].astype(str) == f_evict_yr]
    if f_evict_multi:
        filtered_df = filtered_df[filtered_df["evict_case_number"].fillna("").astype(str).str.contains(",", regex=False)]

    # Advanced: Lead
    if f_lsc != "All":
        filtered_df = filtered_df[filtered_df["lsc_stat"].astype(str) == f_lsc]
    if f_lead_rollout != "All":
        filtered_df = filtered_df[filtered_df["lead_rollout"].astype(str) == f_lead_rollout]

    # Advanced: Foreclosure & Forfeiture
    if f_fo_status != "All":
        filtered_df = filtered_df[filtered_df["lstatus"].astype(str) == f_fo_status]
    if f_cdesig != "All":
        filtered_df = filtered_df[filtered_df["cdesig"].astype(str) == f_cdesig]
    if f_has_fo_deed:
        filtered_df = filtered_df[filtered_df["fo_deed_count"].fillna(0) > 0]

    # Advanced: Land Bank
    if f_city_lb:
        filtered_df = filtered_df[filtered_df["city_lb_flag"].fillna(0) == 1]
    if f_cclrc:
        filtered_df = filtered_df[filtered_df["cclrc"].fillna(0) == 1]
    if f_demo_status != "All":
        filtered_df = filtered_df[filtered_df["demo_status"].astype(str) == f_demo_status]
    if f_rehab_status != "All":
        filtered_df = filtered_df[filtered_df["rehab_status"].astype(str) == f_rehab_status]
    if f_disp_status != "All":
        filtered_df = filtered_df[filtered_df["disp_status"].astype(str) == f_disp_status]

    # Advanced: Geographies
    if f_ward != "All":
        filtered_df = filtered_df[filtered_df["ward2025"].astype(str) == f_ward]
    if f_zip != "All":
        filtered_df = filtered_df[filtered_df["zip"].astype(str) == f_zip]
    if f_region != "All":
        filtered_df = filtered_df[filtered_df["cuyregion"].astype(str) == f_region]
    if f_cia != "All":
        filtered_df = filtered_df[filtered_df["cia14_name"].astype(str) == f_cia]

    # Advanced: Rental & Housing
    if f_rental:
        filtered_df = filtered_df[filtered_df["rentalreg"].fillna(0) == 1]
    if f_sect8:
        filtered_df = filtered_df[filtered_df["sect8"].fillna(0) == 1]
    if f_hud:
        filtered_df = filtered_df[filtered_df["hud"].fillna(0) == 1]
    if f_out_of_state:
        filtered_df = filtered_df[~filtered_df["MAIL_STATE"].fillna("").isin(["OH", "/", ""])]

    # ---- Results Header Stats ----
    st.markdown("---")
    total = len(filtered_df)
    avg_val = int(filtered_df["TAX_MARKET_TOTAL"].mean()) if total > 0 else 0
    vacancy_pct = round(filtered_df["combovac"].fillna(0).sum() / total * 100, 1) if total > 0 else 0
    violation_ct = int(filtered_df["violation"].fillna(0).sum()) if total > 0 else 0

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(f'<div class="stat-box"><div class="stat-value">{total:,}</div><div class="stat-label">Properties</div></div>', unsafe_allow_html=True)
    with s2:
        st.markdown(f'<div class="stat-box"><div class="stat-value">${avg_val:,}</div><div class="stat-label">Avg Market Value</div></div>', unsafe_allow_html=True)
    with s3:
        st.markdown(f'<div class="stat-box"><div class="stat-value">{vacancy_pct}%</div><div class="stat-label">Vacancy Rate</div></div>', unsafe_allow_html=True)
    with s4:
        st.markdown(f'<div class="stat-box"><div class="stat-value">{violation_ct:,}</div><div class="stat-label">Properties w/ Violations</div></div>', unsafe_allow_html=True)

    st.markdown("")

    # ---- Column Selector ----
    with st.expander("Customize Columns"):
        preset_sel = st.radio(
            "Column preset",
            list(PRESET_COLUMNS.keys()) + ["Custom"],
            horizontal=True,
            key="col_preset",
        )
        if preset_sel != "Custom":
            # Use preset; filter to cols that actually exist
            display_columns = [c for c in PRESET_COLUMNS[preset_sel] if c in df.columns]
        else:
            custom_selections = []
            for group_name, group_cols in COL_GROUPS.items():
                valid_cols = [c for c in group_cols if c in df.columns]
                if not valid_cols:
                    continue
                with st.expander(f"{group_name}"):
                    gcol1, gcol2 = st.columns([1, 3])
                    with gcol1:
                        sel_all = st.button("All", key=f"all_{group_name}")
                        sel_none = st.button("None", key=f"none_{group_name}")
                    with gcol2:
                        default_checked = valid_cols if group_name == "Core" else []
                        selected = st.multiselect(
                            group_name,
                            valid_cols,
                            default=default_checked,
                            label_visibility="collapsed",
                            key=f"ms_{group_name}",
                        )
                    custom_selections.extend(selected)
            display_columns = custom_selections if custom_selections else [c for c in PRESET_COLUMNS["Basic Info"] if c in df.columns]

    # ---- Results Tabs ----
    tab_table, tab_map, tab_charts, tab_summary = st.tabs(["Table View", "Map View", "Charts", "Summary"])

    with tab_table:
        if total > 0:
            st.dataframe(
                filtered_df[display_columns].reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
                height=520,
            )
        else:
            st.info("No properties match your filters.")

    with tab_map:
        _MAP_LIMIT = 2000
        if total == 0:
            st.info("No properties to display. Adjust your filters.")
        elif total > _MAP_LIMIT:
            st.warning(f"{total:,} properties match — narrow your filters to {_MAP_LIMIT:,} or fewer to display on the map.")
        else:
            import folium
            from streamlit_folium import st_folium
            import geopandas as gpd

            _map_cols = ["LATITUDE", "LONGITUDE", "NEIGHBOR10", "number", "street", "TAX_MARKET_TOTAL", "combovac"]
            map_df = filtered_df[[c for c in _map_cols if c in filtered_df.columns]].copy()
            map_df = map_df.dropna(subset=["LATITUDE", "LONGITUDE"])

            if map_df.empty:
                st.info("No properties with coordinates to display.")
            else:
                center_lat = map_df["LATITUDE"].mean()
                center_lng = map_df["LONGITUDE"].mean()

                m = folium.Map(
                    location=[center_lat, center_lng],
                    zoom_start=13,
                    tiles="CartoDB positron",
                )

                # Neighbourhood polygon outlines for spatial context
                @st.cache_data
                def _load_hoods_ctx():
                    gdf = gpd.read_file("data/cuy_nei20_NAD83.shp")
                    return gdf.to_crs(epsg=4326)

                gdf_ctx = _load_hoods_ctx()
                folium.GeoJson(
                    gdf_ctx.__geo_interface__,
                    style_function=lambda x: {
                        "fillColor": "transparent",
                        "color": "#aaaaaa",
                        "weight": 1,
                        "fillOpacity": 0,
                    },
                ).add_to(m)

                # Property dots, coloured by vacancy
                for _, row in map_df.iterrows():
                    is_vacant = int(row.get("combovac", 0) or 0) == 1
                    color = "#e03127" if is_vacant else "#003071"
                    num = str(row.get("number", "")).strip()
                    street = str(row.get("street", "")).strip()
                    address = f"{num} {street}".strip() or "Unknown Address"
                    val = row.get("TAX_MARKET_TOTAL")
                    val_str = f"${int(val):,}" if pd.notna(val) and val > 0 else "N/A"
                    vacant_label = '<span style="color:#e03127">&#9888; Vacant</span>' if is_vacant else "Occupied"
                    tip = (
                        f"<b>{address}</b><br>"
                        f"{row.get('NEIGHBOR10', '')}<br>"
                        f"Market Value: {val_str}<br>"
                        f"{vacant_label}"
                    )
                    folium.CircleMarker(
                        location=[row["LATITUDE"], row["LONGITUDE"]],
                        radius=5,
                        color=None,
                        fill=True,
                        fill_color=color,
                        fill_opacity=0.75,
                        tooltip=folium.Tooltip(tip),
                    ).add_to(m)

                # Legend
                legend_html = """
                <div style="position:fixed;bottom:30px;right:30px;z-index:9999;background:white;
                     padding:10px 14px;border-radius:8px;border:1px solid #ddd;font-size:12px;
                     font-family:Arial,sans-serif;box-shadow:0 2px 8px rgba(0,0,0,0.12);">
                    <div style="font-weight:700;margin-bottom:6px;color:#003071;">Vacancy Status</div>
                    <div><span style="display:inline-block;width:11px;height:11px;border-radius:50%;
                         background:#003071;margin-right:7px;vertical-align:middle;"></span>Occupied</div>
                    <div style="margin-top:4px"><span style="display:inline-block;width:11px;height:11px;
                         border-radius:50%;background:#e03127;margin-right:7px;vertical-align:middle;"></span>Vacant</div>
                </div>
                """
                m.get_root().html.add_child(folium.Element(legend_html))

                st.caption(f"Showing {len(map_df):,} properties  ·  Navy = Occupied  ·  Red = Vacant")
                st_folium(m, width=None, height=520, use_container_width=True, returned_objects=[])

    with tab_charts:
        if total > 0:
            import plotly.express as px

            ch1, ch2 = st.columns(2)
            with ch1:
                type_counts = filtered_df["CLASSIFICATION_DESCR"].value_counts().head(10)
                df_p = type_counts.reset_index()
                df_p.columns = ["Category", "Count"]
                df_p = df_p.sort_values("Count", ascending=True)
                fig = px.bar(
                    df_p, x="Count", y="Category", orientation="h",
                    title="Properties by Type (top 10)",
                    color_discrete_sequence=["#003071"],
                )
                fig.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white", height=320,
                    font=dict(family="Inter, Arial, sans-serif", size=12),
                    title_font=dict(size=13, color="#003071"),
                    margin=dict(l=10, r=20, t=40, b=10),
                    xaxis_title="", yaxis_title="",
                )
                fig.update_traces(hovertemplate="%{y}<br><b>%{x:,}</b><extra></extra>")
                st.plotly_chart(fig, use_container_width=True)
            with ch2:
                nbh_counts = filtered_df["NEIGHBOR10"].value_counts().head(10)
                st.bar_chart(nbh_counts, color="#FFD700")
                st.caption("Properties by Neighborhood (top 10)")

            ch3, ch4 = st.columns(2)
            with ch3:
                cond_counts = filtered_df["condition"].value_counts()
                st.bar_chart(cond_counts, color="#003071")
                st.caption("Property Condition")
            with ch4:
                region_counts = filtered_df["cuyregion"].value_counts()
                st.bar_chart(region_counts, color="#FFD700")
                st.caption("By Cuyahoga Region")
        else:
            st.info("No data to chart. Adjust your filters.")

    with tab_summary:
        if total > 0:
            su1, su2 = st.columns(2)
            with su1:
                st.markdown("**Value Statistics**")
                val_cols = [c for c in ["TAX_MARKET_TOTAL", "TAX_MARKET_LAND", "TAX_MARKET_IMPROVEMENT", "currentvalue2023", "lsaleamt"] if c in filtered_df.columns]
                st.dataframe(filtered_df[val_cols].describe().round(0), use_container_width=True)
            with su2:
                st.markdown("**Top Neighborhoods**")
                st.dataframe(filtered_df["NEIGHBOR10"].value_counts().head(10).rename("Count"), use_container_width=True)
            su3, su4 = st.columns(2)
            with su3:
                st.markdown("**Vacancy & Distress**")
                distress = {
                    "Vacant (combovac)": int(filtered_df["combovac"].fillna(0).sum()),
                    "Vacant Lot (vl)": int(filtered_df["vl"].fillna(0).sum()),
                    "Active Condemnation": int(filtered_df["active_condemn"].fillna(0).sum()),
                    "In Foreclosure": int(filtered_df["FORECLOSURE_FLAG"].fillna(0).sum()),
                    "Tax Delinquent": int((filtered_df["NET_TAX_DELQ_DUE"].fillna(0) > 0).sum()),
                    "Has Violation": int(filtered_df["violation"].fillna(0).sum()),
                    "City Land Bank": int(filtered_df["city_lb_flag"].fillna(0).sum()),
                }
                st.dataframe(pd.DataFrame.from_dict(distress, orient="index", columns=["Count"]), use_container_width=True)
            with su4:
                st.markdown("**Foreclosure Cases**")
                fo_counts = filtered_df["lstatus"].value_counts()
                st.dataframe(fo_counts.rename("Count"), use_container_width=True)
        else:
            st.info("No data to summarize. Adjust your filters.")

    # ---- Export ----
    st.markdown("---")
    with st.expander("Export Options"):
        ex_col1, ex_col2 = st.columns(2)
        with ex_col1:
            export_format = st.radio(
                "Format",
                ["CSV (Excel-friendly)", "GeoJSON (mapping)", "Shapefile (GIS software)"],
                key="export_fmt",
            )
        with ex_col2:
            export_columns_opt = st.radio(
                "Columns",
                ["Selected columns only", "All available columns"],
                key="export_cols",
            )

        all_columns = filtered_df.columns.tolist()
        export_df = filtered_df if export_columns_opt == "All available columns" else filtered_df[display_columns]

        if total == 0:
            st.warning("No data to export. Adjust your filters first.")
        elif export_format == "CSV (Excel-friendly)":
            csv_data = export_df.to_csv(index=False)
            st.download_button(
                label=f"Download {total:,} results as CSV",
                data=csv_data,
                file_name="nst_export.csv",
                mime="text/csv",
            )
        elif export_format == "GeoJSON (mapping)":
            features = []
            for _, row in filtered_df.iterrows():
                lat = row.get("LATITUDE")
                lon = row.get("LONGITUDE")
                if pd.notna(lat) and pd.notna(lon):
                    cols_to_use = display_columns if export_columns_opt == "Selected columns only" else all_columns
                    props = {c: (row[c].item() if hasattr(row[c], "item") else row[c]) for c in cols_to_use if c not in ("LATITUDE", "LONGITUDE")}
                    features.append({
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
                        "properties": props,
                    })
            geojson = json.dumps({"type": "FeatureCollection", "features": features})
            st.download_button(
                label=f"Download {len(features):,} features as GeoJSON",
                data=geojson,
                file_name="nst_export.geojson",
                mime="application/geo+json",
            )
        else:  # Shapefile
            try:
                import geopandas as gpd
                from shapely.geometry import Point
                geo_rows = filtered_df.dropna(subset=["LATITUDE", "LONGITUDE"])
                geometry = [Point(lon, lat) for lat, lon in zip(geo_rows["LONGITUDE"], geo_rows["LATITUDE"])]
                cols_to_use = [c for c in (display_columns if export_columns_opt == "Selected columns only" else all_columns) if c not in ("LATITUDE", "LONGITUDE")]
                gdf = gpd.GeoDataFrame(geo_rows[cols_to_use].reset_index(drop=True), geometry=geometry, crs="EPSG:4326")
                import tempfile, os, glob as glob_mod
                with tempfile.TemporaryDirectory() as tmpdir:
                    shp_path = os.path.join(tmpdir, "nst_export.shp")
                    gdf.to_file(shp_path, driver="ESRI Shapefile")
                    buf = io.BytesIO()
                    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                        for f_path in glob_mod.glob(os.path.join(tmpdir, "nst_export.*")):
                            zf.write(f_path, os.path.basename(f_path))
                    buf.seek(0)
                st.download_button(
                    label=f"Download {len(geo_rows):,} features as Shapefile (.zip)",
                    data=buf.getvalue(),
                    file_name="nst_export_shp.zip",
                    mime="application/zip",
                )
            except ImportError:
                st.warning("Shapefile export requires `geopandas` and `shapely`.")
                st.code("pip install geopandas shapely", language="bash")

    # ---- Footer ----
    st.markdown("---")
    st.markdown('<div style="text-align: center; color: #666; padding: 2rem 0;"><p>Powered by CWRU Poverty Center | Last Updated: March 2026</p></div>', unsafe_allow_html=True)


elif current_page == "maps":
    # ========================================================
    #  MAP EXPLORER PAGE
    #  Two states controlled by URL params:
    #    ?page=maps              → Map overview with all neighborhood zones
    #    ?page=maps&hood=<name>  → Neighborhood profile with stats + download
    #
    #  Map clicks are detected via st_folium return data (tooltip match).
    #  Dropdown and sidebar list also navigate to profiles.
    # ========================================================
    import folium
    from streamlit_folium import st_folium
    import geopandas as gpd

    # -- Load data --
    @st.cache_data
    def load_neighborhoods():
        gdf = gpd.read_file("data/cuy_nei20_NAD83.shp")
        return gdf.to_crs(epsg=4326)

    @st.cache_data
    def load_map_data():
        return pd.read_csv("data/nstsample.csv", low_memory=False)

    df_map = load_map_data()
    gdf_hoods = load_neighborhoods()

    # Check if a specific neighborhood was selected via URL
    selected_hood = query_params.get("hood", None)

    # -- Page CSS --
    st.markdown("""
        <style>
        .map-page-header {
            font-size: 2.5rem;
            font-weight: 700;
            color: #003071;
            margin-bottom: 0.3rem;
        }
        .map-page-subtitle {
            font-size: 1.1rem;
            color: #666;
            margin-bottom: 1rem;
        }
        .map-sidebar-prompt {
            background: #f0f4fa;
            border: 2px dashed #003071;
            border-radius: 8px;
            padding: 2rem 1.5rem;
            text-align: center;
            margin: 1rem 0;
        }
        .map-sidebar-prompt-icon {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        .map-sidebar-prompt-text {
            font-size: 1.1rem;
            font-weight: 600;
            color: #003071;
        }
        /* Sidebar neighborhood list links */
        .hood-list-item {
            display: block;
            padding: 0.7rem 1rem;
            border-bottom: 1px solid #e8e8e8;
            color: #003071 !important;
            text-decoration: none !important;
            font-weight: 500;
            font-size: 1rem;
            transition: background 0.2s, padding-left 0.2s;
        }
        .hood-list-item:hover {
            background: #f0f4fa;
            padding-left: 1.4rem;
        }
        .hood-list-item-count {
            float: right;
            color: #999;
            font-weight: 400;
            font-size: 0.9rem;
        }
        /* Neighborhood profile styles */
        .hood-profile-header {
            font-size: 2.2rem;
            font-weight: 700;
            color: #003071;
            margin-bottom: 0.2rem;
        }
        .hood-profile-sub {
            font-size: 1rem;
            color: #666;
            margin-bottom: 1.5rem;
        }
        .hood-stat-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .hood-stat-card {
            background: #f8f9fc;
            border-left: 4px solid #003071;
            padding: 1rem 1.2rem;
            border-radius: 4px;
        }
        .hood-stat-card-value {
            font-size: 1.6rem;
            font-weight: 700;
            color: #003071;
        }
        .hood-stat-card-label {
            font-size: 0.85rem;
            color: #666;
        }
        .hood-section-title {
            font-size: 1.3rem;
            font-weight: 600;
            color: #003071;
            margin: 1.5rem 0 0.8rem 0;
            padding-bottom: 0.4rem;
            border-bottom: 2px solid #003071;
        }
        .hood-back-link {
            display: inline-block;
            color: #003071 !important;
            text-decoration: none !important;
            font-weight: 600;
            font-size: 1rem;
            margin-bottom: 1rem;
            padding: 0.4rem 0;
        }
        .hood-back-link:hover {
            color: #FFD700 !important;
        }
        .breadcrumb { font-size: 0.95rem; color: #666; margin-bottom: 1.5rem; }
        .breadcrumb a { color: #003071; text-decoration: none; }
        .breadcrumb a:hover { text-decoration: underline; }
        </style>
    """, unsafe_allow_html=True)

    # Map overview — always shown; clicks navigate to the dedicated neighborhood page
    # Breadcrumb
    st.markdown("""
        <div class="breadcrumb">
            <a href="?auth=1&page=home" target="_self">Home</a> &nbsp;/&nbsp; <strong>Map Explorer</strong>
        </div>
    """, unsafe_allow_html=True)

    # Layout: left sidebar (1) + map (2.5)
    panel_col, map_col = st.columns([1, 2.5])

    with panel_col:
        st.markdown('<div class="map-page-header" style="font-size:1.6rem;">Map Explorer</div>', unsafe_allow_html=True)
        st.markdown('<div class="map-page-subtitle" style="font-size:0.95rem;">Cleveland Neighborhood Data</div>', unsafe_allow_html=True)

        # Prompt box
        st.markdown("""
            <div class="map-sidebar-prompt">
                <div class="map-sidebar-prompt-icon">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#003071" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                        <circle cx="12" cy="10" r="3"></circle>
                    </svg>
                </div>
                <div class="map-sidebar-prompt-text">Click on a Neighborhood<br>to view its data</div>
            </div>
        """, unsafe_allow_html=True)

        # Dropdown selector (navigates via st.query_params on selection)
        neighborhoods = sorted(df_map["NEIGHBOR10"].dropna().unique().tolist())
        selected_from_dropdown = st.selectbox("Or select a neighborhood", [""] + neighborhoods, key="map_hood_select", format_func=lambda x: "Choose a neighborhood..." if x == "" else x)
        if selected_from_dropdown:
            st.query_params["page"] = "neighborhood"
            st.query_params["hood"] = selected_from_dropdown
            st.rerun()

        st.markdown("---")

        # Scrollable neighborhood list with property counts
        st.markdown("**All Neighborhoods**")
        hood_counts = df_map["NEIGHBOR10"].value_counts().sort_index()
        hood_list_html = ""
        for hood_name, count in hood_counts.items():
            hood_list_html += f'<a href="?auth=1&page=neighborhood&hood={hood_name}" target="_self" class="hood-list-item">{hood_name}<span class="hood-list-item-count">{count}</span></a>'
        st.markdown(f'<div style="max-height:400px;overflow-y:auto;border:1px solid #e0e0e0;border-radius:6px;">{hood_list_html}</div>', unsafe_allow_html=True)

    with map_col:
        # Property counts per neighborhood for tooltips
        hood_counts_map = df_map["NEIGHBOR10"].value_counts().to_dict()
        hoods_with_data = set(df_map["NEIGHBOR10"].dropna().unique())

        # Color palette for neighborhoods with data
        hood_colors = [
            "#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6",
            "#1abc9c", "#e67e22", "#2980b9", "#c0392b", "#27ae60",
            "#d35400", "#8e44ad", "#16a085", "#f1c40f", "#2c3e50",
            "#7f8c8d", "#e84393", "#00cec9", "#6c5ce7", "#fdcb6e",
        ]
        hood_color_map = {name: hood_colors[i % len(hood_colors)] for i, name in enumerate(sorted(hoods_with_data))}

        # Build folium map centered on Cleveland
        m = folium.Map(location=[41.4993, -81.6944], zoom_start=11, tiles="CartoDB positron")

        # Draw all neighborhood polygons from shapefile
        for _, row in gdf_hoods.iterrows():
            hood_name = row["NEIGHBOR20"]
            has_data = hood_name in hoods_with_data
            count = hood_counts_map.get(hood_name, 0)

            if has_data:
                fill_color = hood_color_map.get(hood_name, "#003071")
                fill_opacity = 0.45
                border_color = "#003071"
                border_weight = 2
                tooltip_text = f"{hood_name} — {count:,} properties"
            else:
                fill_color = "#dddddd"
                fill_opacity = 0.25
                border_color = "#aaaaaa"
                border_weight = 1
                tooltip_text = hood_name

            folium.GeoJson(
                data=row.geometry.__geo_interface__,
                style_function=lambda x, fc=fill_color, fo=fill_opacity, bc=border_color, bw=border_weight: {
                    "fillColor": fc,
                    "color": bc,
                    "weight": bw,
                    "fillOpacity": fo,
                },
                highlight_function=lambda x: {
                    "weight": 3,
                    "color": "#003071",
                    "fillOpacity": 0.65,
                },
                tooltip=tooltip_text,
                # Store just the name so click detection can match it
                name=hood_name,
            ).add_to(m)

        # Render map and capture click data
        map_data = st_folium(m, width=None, height=650, use_container_width=True)

        # Navigate to neighborhood profile when a polygon is clicked
        # Uses point-in-polygon on last_clicked since GeoJson tooltips aren't
        # reliably returned by st_folium's last_object_clicked_tooltip.
        if "last_map_click" not in st.session_state:
            st.session_state["last_map_click"] = None

        if map_data:
            click = map_data.get("last_clicked")
            if click and isinstance(click, dict):
                lat = click.get("lat")
                lng = click.get("lng")
                if lat is not None and lng is not None:
                    click_key = f"{lat:.6f},{lng:.6f}"
                    if click_key != st.session_state.get("last_map_click"):
                        st.session_state["last_map_click"] = click_key
                        from shapely.geometry import Point
                        pt = Point(lng, lat)
                        match = gdf_hoods[gdf_hoods.geometry.contains(pt)]
                        if not match.empty:
                            clicked_hood = match.iloc[0]["NEIGHBOR20"]
                            if clicked_hood in hoods_with_data:
                                st.query_params.update({"auth": "1", "page": "neighborhood", "hood": clicked_hood})
                                st.rerun()

    # -- Footer --
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #666; padding: 2rem 0;">
            <p>Powered by CWRU Poverty Center | Last Updated: January 2026</p>
        </div>
    """, unsafe_allow_html=True)


elif current_page == "property-search":
    # ========================================================
    #  PROPERTY SEARCH PAGE — Look up a single property by address or parcel
    #  Shows a detailed profile card with all property attributes.
    # ========================================================

    @st.cache_data
    def load_property_data():
        return pd.read_csv("data/nstsample.csv", low_memory=False)

    df_ps = load_property_data()

    # -- Page CSS --
    st.markdown("""
        <style>
        .breadcrumb { font-size: 0.95rem; color: #666; margin-bottom: 1.5rem; }
        .breadcrumb a { color: #003071; text-decoration: none; }
        .breadcrumb a:hover { text-decoration: underline; }
        .page-header { font-size: 2.5rem; font-weight: 700; color: #003071; margin-bottom: 0.3rem; }
        .page-subtitle { font-size: 1.1rem; color: #666; margin-bottom: 1rem; }
        .property-card {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }
        .property-card-header {
            font-size: 1.5rem;
            font-weight: 700;
            color: #003071;
            margin-bottom: 0.3rem;
        }
        .property-card-parcel {
            font-size: 0.9rem;
            color: #999;
            margin-bottom: 1rem;
        }
        .property-detail-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
        }
        .property-detail {
            padding: 0.8rem;
            background: #f8f9fc;
            border-radius: 4px;
        }
        .property-detail-label {
            font-size: 0.8rem;
            color: #666;
            margin-bottom: 0.2rem;
        }
        .property-detail-value {
            font-size: 1.1rem;
            font-weight: 600;
            color: #003071;
        }
        .section-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: #003071;
            margin: 1.5rem 0 0.8rem 0;
            padding-bottom: 0.4rem;
            border-bottom: 2px solid #003071;
        }
        </style>
    """, unsafe_allow_html=True)

    # -- Breadcrumb + header --
    st.markdown('<div class="breadcrumb"><a href="?auth=1&page=home" target="_self">Home</a> &nbsp;/&nbsp; <strong>Property Search</strong></div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="page-header">Property Search</div>
        <div class="page-subtitle">Look up detailed information for a specific property.</div>
    """, unsafe_allow_html=True)

    # -- Search input --
    ps_query = st.text_input(
        "Search by address or parcel number",
        placeholder="e.g. 1725 Pearl Rd or 754-24-125",
        key="ps_search",
    )

    if ps_query:
        # Search against combined "house_number street_name" and parcel_number
        full_address = df_ps["house_number"].astype(str) + " " + df_ps["street_name"].fillna("")
        mask = (
            full_address.str.contains(ps_query, case=False, na=False)
            | df_ps["parcel_number"].str.contains(ps_query, case=False, na=False)
        )
        results = df_ps[mask]

        if len(results) == 0:
            st.warning("No properties found. Try a different search term.")
        elif len(results) > 1 and len(results) <= 20:
            st.markdown(f"**{len(results)} properties found.** Select one:")
            options = [f"{int(r['house_number'])} {r['street_name']} ({r['parcel_number']})" for _, r in results.iterrows()]
            selected_option = st.selectbox("Select a property", options, label_visibility="collapsed")
            selected_idx = options.index(selected_option)
            prop = results.iloc[selected_idx]
        elif len(results) > 20:
            st.warning(f"{len(results)} results found. Please be more specific.")
            prop = None
        else:
            prop = results.iloc[0]

        # -- Property profile card --
        if len(results) >= 1 and len(results) <= 20:
            if len(results) == 1:
                prop = results.iloc[0]

            # Address header
            st.markdown(f"""
                <div class="property-card">
                    <div class="property-card-header">{int(prop['house_number'])} {prop['street_name']}</div>
                    <div class="property-card-parcel">Parcel: {prop['parcel_number']} &nbsp;|&nbsp; {prop['neighborhood']} &nbsp;|&nbsp; Ward {int(prop['ward'])} &nbsp;|&nbsp; ZIP {int(prop['zip_code'])}</div>
                </div>
            """, unsafe_allow_html=True)

            # Section: Property Details
            st.markdown('<div class="section-title">Property Details</div>', unsafe_allow_html=True)
            st.markdown(f"""
                <div class="property-detail-grid">
                    <div class="property-detail">
                        <div class="property-detail-label">Property Type</div>
                        <div class="property-detail-value">{prop['property_type']}</div>
                    </div>
                    <div class="property-detail">
                        <div class="property-detail-label">Year Built</div>
                        <div class="property-detail-value">{int(prop['year_built'])}</div>
                    </div>
                    <div class="property-detail">
                        <div class="property-detail-label">Condition</div>
                        <div class="property-detail-value">{prop['property_condition']}</div>
                    </div>
                    <div class="property-detail">
                        <div class="property-detail-label">Bedrooms</div>
                        <div class="property-detail-value">{int(prop['bedrooms'])}</div>
                    </div>
                    <div class="property-detail">
                        <div class="property-detail-label">Bathrooms</div>
                        <div class="property-detail-value">{prop['bathrooms']}</div>
                    </div>
                    <div class="property-detail">
                        <div class="property-detail-label">Square Feet</div>
                        <div class="property-detail-value">{int(prop['square_feet']):,}</div>
                    </div>
                    <div class="property-detail">
                        <div class="property-detail-label">Lot Size (sq ft)</div>
                        <div class="property-detail-value">{int(prop['lot_size_sqft']):,}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Section: Value & Tax
            st.markdown('<div class="section-title">Value & Tax Information</div>', unsafe_allow_html=True)
            st.markdown(f"""
                <div class="property-detail-grid">
                    <div class="property-detail">
                        <div class="property-detail-label">Market Value</div>
                        <div class="property-detail-value">${int(prop['property_value']):,}</div>
                    </div>
                    <div class="property-detail">
                        <div class="property-detail-label">Assessed Value</div>
                        <div class="property-detail-value">${int(prop['assessed_value']):,}</div>
                    </div>
                    <div class="property-detail">
                        <div class="property-detail-label">Annual Tax</div>
                        <div class="property-detail-value">${int(prop['annual_tax']):,}</div>
                    </div>
                    <div class="property-detail">
                        <div class="property-detail-label">Tax Delinquent</div>
                        <div class="property-detail-value">{"Yes - $" + str(int(prop['delinquent_amount'])) if prop['tax_delinquent'] else "No"}</div>
                    </div>
                    <div class="property-detail">
                        <div class="property-detail-label">Last Sale Year</div>
                        <div class="property-detail-value">{int(prop['last_sale_year'])}</div>
                    </div>
                    <div class="property-detail">
                        <div class="property-detail-label">Last Sale Price</div>
                        <div class="property-detail-value">${int(prop['last_sale_price']):,}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Section: Ownership
            st.markdown('<div class="section-title">Ownership & Occupancy</div>', unsafe_allow_html=True)
            st.markdown(f"""
                <div class="property-detail-grid">
                    <div class="property-detail">
                        <div class="property-detail-label">Owner Type</div>
                        <div class="property-detail-value">{prop['owner_type']}</div>
                    </div>
                    <div class="property-detail">
                        <div class="property-detail-label">Owner</div>
                        <div class="property-detail-value">{prop['owner_name']}</div>
                    </div>
                    <div class="property-detail">
                        <div class="property-detail-label">Vacancy Status</div>
                        <div class="property-detail-value">{prop['vacancy_status']}</div>
                    </div>
                    <div class="property-detail">
                        <div class="property-detail-label">Foreclosure Status</div>
                        <div class="property-detail-value">{prop['foreclosure_status']}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Section: Violations & Permits
            st.markdown('<div class="section-title">Violations & Permits</div>', unsafe_allow_html=True)
            st.markdown(f"""
                <div class="property-detail-grid">
                    <div class="property-detail">
                        <div class="property-detail-label">Lead Violations</div>
                        <div class="property-detail-value">{int(prop['lead_violations'])}</div>
                    </div>
                    <div class="property-detail">
                        <div class="property-detail-label">Building Violations</div>
                        <div class="property-detail-value">{int(prop['building_violations'])}</div>
                    </div>
                    <div class="property-detail">
                        <div class="property-detail-label">Code Violations</div>
                        <div class="property-detail-value">{int(prop['code_violations'])}</div>
                    </div>
                    <div class="property-detail">
                        <div class="property-detail-label">Lead Safe Certified</div>
                        <div class="property-detail-value">{"Yes" if prop['lead_safe_certified'] else "No"}</div>
                    </div>
                    <div class="property-detail">
                        <div class="property-detail-label">Permits Issued (5yr)</div>
                        <div class="property-detail-value">{int(prop['permits_issued'])}</div>
                    </div>
                    <div class="property-detail">
                        <div class="property-detail-label">Last Inspection</div>
                        <div class="property-detail-value">{int(prop['last_inspection_year']) if pd.notna(prop['last_inspection_year']) else "N/A"}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Section: Neighborhood Context
            st.markdown('<div class="section-title">Neighborhood Context</div>', unsafe_allow_html=True)
            st.markdown(f"""
                <div class="property-detail-grid">
                    <div class="property-detail">
                        <div class="property-detail-label">Median Income (Tract)</div>
                        <div class="property-detail-value">${int(prop['median_income_tract']):,}</div>
                    </div>
                    <div class="property-detail">
                        <div class="property-detail-label">Poverty Rate (Tract)</div>
                        <div class="property-detail-value">{prop['poverty_rate_tract']}%</div>
                    </div>
                    <div class="property-detail">
                        <div class="property-detail-label">School Rating</div>
                        <div class="property-detail-value">{int(prop['school_rating'])} / 10</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Mini map showing property location
            st.markdown('<div class="section-title">Location</div>', unsafe_allow_html=True)
            if pd.notna(prop["latitude"]) and pd.notna(prop["longitude"]):
                st.map(
                    pd.DataFrame({"latitude": [prop["latitude"]], "longitude": [prop["longitude"]]}),
                    latitude="latitude",
                    longitude="longitude",
                    zoom=15,
                )

    else:
        # No search yet — show quick links to browse by neighborhood
        st.markdown("")
        st.markdown("**Quick links — browse by neighborhood:**")
        hood_counts = df_ps["neighborhood"].value_counts().head(10)
        cols = st.columns(5)
        for i, (hood, count) in enumerate(hood_counts.items()):
            with cols[i % 5]:
                st.markdown(f'<a href="?auth=1&page=datasets" target="_self" style="color:#003071;text-decoration:none;font-weight:500;">{hood}</a> <span style="color:#999;font-size:0.85rem;">({count})</span>', unsafe_allow_html=True)

    # -- Footer --
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #666; padding: 2rem 0;">
            <p>Powered by CWRU Poverty Center | Last Updated: January 2026</p>
        </div>
    """, unsafe_allow_html=True)


elif current_page == "neighborhood":
    # ========================================================
    #  NEIGHBORHOOD PROFILE PAGE
    #  URL: ?auth=1&page=neighborhood&hood=<name>
    # ========================================================
    import folium
    from streamlit_folium import st_folium

    selected_hood = query_params.get("hood", None)

    @st.cache_data
    def load_neighborhood_data():
        return pd.read_csv("data/nstsample.csv", low_memory=False)

    df_n = load_neighborhood_data()

    st.markdown("""
        <style>
        .breadcrumb { font-size: 0.95rem; color: #666; margin-bottom: 1.5rem; }
        .breadcrumb a { color: #003071; text-decoration: none; }
        .breadcrumb a:hover { text-decoration: underline; }
        .hood-profile-header { font-size: 2.4rem; font-weight: 700; color: #003071; margin-bottom: 0.2rem; }
        .hood-profile-sub { font-size: 1rem; color: #666; margin-bottom: 1.5rem; }
        .hood-stat-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .hood-stat-card {
            background: #f8f9fc;
            border-left: 4px solid #003071;
            padding: 1rem 1.2rem;
            border-radius: 4px;
        }
        .hood-stat-card-value { font-size: 1.6rem; font-weight: 700; color: #003071; }
        .hood-stat-card-label { font-size: 0.85rem; color: #666; }
        .hood-section-title {
            font-size: 1.3rem;
            font-weight: 600;
            color: #003071;
            margin: 1.5rem 0 0.8rem 0;
            padding-bottom: 0.4rem;
            border-bottom: 2px solid #003071;
        }
        .hood-back-link {
            display: inline-block;
            color: #003071 !important;
            text-decoration: none !important;
            font-weight: 600;
            font-size: 1rem;
            margin-bottom: 1rem;
        }
        .hood-back-link:hover { color: #FFD700 !important; }
        </style>
    """, unsafe_allow_html=True)

    if not selected_hood or selected_hood not in df_n["NEIGHBOR10"].unique():
        st.warning("No neighborhood selected. Please choose one from the Map Explorer.")
        st.markdown('<a href="?auth=1&page=maps" target="_self">← Back to Map Explorer</a>', unsafe_allow_html=True)
    else:
        hood_df = df_n[df_n["NEIGHBOR10"] == selected_hood].copy()

        # Breadcrumb
        st.markdown(f"""
            <div class="breadcrumb">
                <a href="?auth=1&page=home">Home</a> &rsaquo;
                <a href="?auth=1&page=maps">Map Explorer</a> &rsaquo;
                <strong>{selected_hood}</strong>
            </div>
        """, unsafe_allow_html=True)
        st.markdown('<a href="?auth=1&page=maps" class="hood-back-link" target="_self">&larr; Back to Map</a>', unsafe_allow_html=True)

        # Header
        wards_in_hood = sorted(hood_df["ward2025"].dropna().unique().astype(int).tolist())
        zips_in_hood = sorted(hood_df["zip"].dropna().astype(str).str.split(".").str[0].unique().tolist())
        st.markdown(f'<div class="hood-profile-header">{selected_hood}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="hood-profile-sub">Ward{"s" if len(wards_in_hood) > 1 else ""} {", ".join(str(w) for w in wards_in_hood)} &nbsp;|&nbsp; ZIP{"s" if len(zips_in_hood) > 1 else ""} {", ".join(str(z) for z in zips_in_hood)}</div>', unsafe_allow_html=True)

        # Key metrics
        n_total = len(hood_df)
        def _safe_int(val, default=0):
            import math
            try:
                return default if (val is None or (isinstance(val, float) and math.isnan(val))) else int(val)
            except (TypeError, ValueError):
                return default

        n_avg_val = _safe_int(pd.to_numeric(hood_df["TAX_MARKET_TOTAL"], errors="coerce").mean()) if n_total > 0 else 0
        n_median_val = _safe_int(pd.to_numeric(hood_df["TAX_MARKET_TOTAL"], errors="coerce").median()) if n_total > 0 else 0
        n_vacancy = round((hood_df["combovac"] == 1).sum() / n_total * 100, 1) if n_total > 0 else 0
        n_violations = int((hood_df["violation"] == 1).sum()) if n_total > 0 else 0
        n_foreclosure = int((hood_df["FORECLOSURE_FLAG"] == 1).sum()) if n_total > 0 else 0
        n_tax_del = int((pd.to_numeric(hood_df["NET_TAX_DELQ_DUE"], errors="coerce") > 0).sum()) if n_total > 0 else 0
        n_avg_assessment = _safe_int(pd.to_numeric(hood_df["assessment"], errors="coerce").mean()) if n_total > 0 else 0
        n_land_bank = int((hood_df["vl"] == 1).sum()) if n_total > 0 else 0

        st.markdown(f"""
            <div class="hood-stat-grid">
                <div class="hood-stat-card">
                    <div class="hood-stat-card-value">{n_total:,}</div>
                    <div class="hood-stat-card-label">Total Properties</div>
                </div>
                <div class="hood-stat-card">
                    <div class="hood-stat-card-value">${n_avg_val:,}</div>
                    <div class="hood-stat-card-label">Avg Market Value</div>
                </div>
                <div class="hood-stat-card">
                    <div class="hood-stat-card-value">${n_median_val:,}</div>
                    <div class="hood-stat-card-label">Median Market Value</div>
                </div>
                <div class="hood-stat-card">
                    <div class="hood-stat-card-value">{n_vacancy}%</div>
                    <div class="hood-stat-card-label">Vacancy Rate</div>
                </div>
                <div class="hood-stat-card">
                    <div class="hood-stat-card-value">{n_violations:,}</div>
                    <div class="hood-stat-card-label">Properties w/ Violations</div>
                </div>
                <div class="hood-stat-card">
                    <div class="hood-stat-card-value">{n_foreclosure:,}</div>
                    <div class="hood-stat-card-label">In Foreclosure</div>
                </div>
                <div class="hood-stat-card">
                    <div class="hood-stat-card-value">{n_tax_del:,}</div>
                    <div class="hood-stat-card-label">Tax Delinquent</div>
                </div>
                <div class="hood-stat-card">
                    <div class="hood-stat-card-value">${n_avg_assessment:,}</div>
                    <div class="hood-stat-card-label">Avg Assessment</div>
                </div>
                <div class="hood-stat-card">
                    <div class="hood-stat-card-value">{n_land_bank:,}</div>
                    <div class="hood-stat-card-label">Land Bank Properties</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Tabs
        tab_overview, tab_map, tab_data, tab_download = st.tabs(["Overview", "Map", "Property Data", "Download"])

        with tab_overview:
            st.markdown('<div class="hood-section-title">Property Breakdown</div>', unsafe_allow_html=True)
            ov1, ov2 = st.columns(2)
            with ov1:
                st.bar_chart(hood_df["CLASSIFICATION_DESCR"].value_counts(), color="#003071")
                st.caption("Properties by Classification")
            with ov2:
                st.bar_chart(hood_df["condition"].dropna().value_counts(), color="#003071")
                st.caption("Properties by Condition")

            st.markdown('<div class="hood-section-title">Property Status</div>', unsafe_allow_html=True)
            ov3, ov4 = st.columns(2)
            with ov3:
                vac_counts = hood_df["combovac"].map({1: "Vacant", 0: "Occupied"}).value_counts()
                st.bar_chart(vac_counts, color="#003071")
                st.caption("Vacancy Status")
            with ov4:
                delq = pd.to_numeric(hood_df["NET_TAX_DELQ_DUE"], errors="coerce")
                delq_counts = pd.Series({"Delinquent": int((delq > 0).sum()), "Current": int((delq <= 0).sum())})
                st.bar_chart(delq_counts, color="#003071")
                st.caption("Tax Delinquency")

            st.markdown('<div class="hood-section-title">Violations & Foreclosure</div>', unsafe_allow_html=True)
            ov5, ov6 = st.columns(2)
            with ov5:
                violation_summary = pd.DataFrame({
                    "Status": ["With Violations", "No Violations"],
                    "Properties": [int((hood_df["violation"] == 1).sum()), int((hood_df["violation"] != 1).sum())],
                })
                st.dataframe(violation_summary, use_container_width=True, hide_index=True)
            with ov6:
                fc_counts = hood_df["FORECLOSURE_FLAG"].map({1: "In Foreclosure", 0: "Not in Foreclosure"}).value_counts()
                st.bar_chart(fc_counts, color="#003071")
                st.caption("Foreclosure Status")

            st.markdown('<div class="hood-section-title">Value Statistics</div>', unsafe_allow_html=True)
            val_cols = [c for c in ["TAX_MARKET_TOTAL", "assessment", "lsaleamt", "NET_TAX_DELQ_DUE"] if c in hood_df.columns]
            st.dataframe(
                hood_df[val_cols].apply(pd.to_numeric, errors="coerce").describe().round(0),
                use_container_width=True,
            )

        with tab_map:
            hood_map_data = hood_df[["LATITUDE", "LONGITUDE"]].apply(pd.to_numeric, errors="coerce").dropna()
            if len(hood_map_data) > 0:
                center_lat = hood_map_data["LATITUDE"].mean()
                center_lon = hood_map_data["LONGITUDE"].mean()
                m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles="CartoDB positron")
                for _, prop in hood_df.iterrows():
                    lat = pd.to_numeric(prop["LATITUDE"], errors="coerce")
                    lon = pd.to_numeric(prop["LONGITUDE"], errors="coerce")
                    if pd.notna(lat) and pd.notna(lon):
                        addr = f"{prop.get('number', '')} {prop.get('street', '')}".strip()
                        val = prop.get("TAX_MARKET_TOTAL", "N/A")
                        try:
                            val_str = f"${int(float(val)):,}"
                        except (ValueError, TypeError):
                            val_str = "N/A"
                        folium.CircleMarker(
                            location=[lat, lon],
                            radius=5,
                            color="#003071",
                            fill=True,
                            fillColor="#FFD700",
                            fillOpacity=0.7,
                            tooltip=addr,
                            popup=folium.Popup(
                                f"<b>{addr}</b><br>"
                                f"Class: {prop.get('CLASSIFICATION_DESCR', 'N/A')}<br>"
                                f"Market Value: {val_str}<br>"
                                f"Condition: {prop.get('condition', 'N/A')}<br>"
                                f"Vacant: {'Yes' if prop.get('combovac') == 1 else 'No'}",
                                max_width=220,
                            ),
                        ).add_to(m)
                st_folium(m, width=None, height=500, use_container_width=True)
            else:
                st.info("No geocoded properties available for this neighborhood.")

        with tab_data:
            st.markdown(f"**{n_total:,} properties in {selected_hood}**")
            all_cols = hood_df.columns.tolist()
            default_cols = ["PARCEL", "number", "street", "CLASSIFICATION_DESCR", "TAX_MARKET_TOTAL", "condition", "combovac", "FORECLOSURE_FLAG"]
            show_cols = st.multiselect("Columns to display", all_cols, default=[c for c in default_cols if c in all_cols], key="hood_cols")
            if not show_cols:
                show_cols = default_cols
            st.dataframe(hood_df[show_cols].reset_index(drop=True), use_container_width=True, hide_index=True, height=500)

        with tab_download:
            st.markdown(f"Export all **{n_total:,} properties** in {selected_hood}.")
            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                dl_format = st.radio("Format", ["CSV", "GeoJSON"], key="hood_dl_fmt")
            with dl_col2:
                dl_columns = st.radio("Columns", ["All columns", "Selected columns only"], key="hood_dl_cols")

            export_hood_df = hood_df[show_cols] if dl_columns == "Selected columns only" and 'show_cols' in dir() else hood_df

            if dl_format == "CSV":
                st.download_button(
                    label=f"Download {n_total:,} properties as CSV",
                    data=export_hood_df.to_csv(index=False),
                    file_name=f"nst_{selected_hood.lower().replace(' ', '_')}.csv",
                    mime="text/csv",
                )
            else:
                features = []
                export_all_cols = hood_df.columns.tolist()
                for _, row in hood_df.iterrows():
                    lat = pd.to_numeric(row.get("LATITUDE"), errors="coerce")
                    lon = pd.to_numeric(row.get("LONGITUDE"), errors="coerce")
                    if pd.notna(lat) and pd.notna(lon):
                        cols_to_use = show_cols if dl_columns == "Selected columns only" and 'show_cols' in dir() else export_all_cols
                        props = {c: (row[c].item() if hasattr(row[c], "item") else row[c]) for c in cols_to_use if c not in ("LATITUDE", "LONGITUDE")}
                        features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]}, "properties": props})
                st.download_button(
                    label=f"Download {len(features):,} features as GeoJSON",
                    data=json.dumps({"type": "FeatureCollection", "features": features}),
                    file_name=f"nst_{selected_hood.lower().replace(' ', '_')}.geojson",
                    mime="application/geo+json",
                )

    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #666; padding: 2rem 0;">
            <p>Powered by CWRU Poverty Center | Last Updated: March 2026</p>
        </div>
    """, unsafe_allow_html=True)


elif current_page == "contact":
    # ========================================================
    #  CONTACT / TALK WITH US PAGE
    # ========================================================

    st.markdown("""
        <style>
        .breadcrumb { font-size: 0.95rem; color: #666; margin-bottom: 1.5rem; }
        .breadcrumb a { color: #003071; text-decoration: none; }
        .breadcrumb a:hover { text-decoration: underline; }
        .page-header { font-size: 2.5rem; font-weight: 700; color: #003071; margin-bottom: 0.3rem; }
        .page-subtitle { font-size: 1.1rem; color: #666; margin-bottom: 2rem; }
        .contact-card {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 2rem;
            margin-bottom: 1.5rem;
        }
        .contact-card-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: #003071;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 2px solid #FFD700;
            padding-bottom: 0.5rem;
            margin-bottom: 1.2rem;
        }
        .contact-org {
            font-size: 1rem;
            font-weight: 700;
            color: #003071;
            margin-bottom: 0.2rem;
        }
        .contact-school {
            font-size: 0.9rem;
            color: #444;
            font-style: italic;
            margin-bottom: 0.15rem;
        }
        .contact-univ {
            font-size: 0.9rem;
            color: #444;
            margin-bottom: 0.15rem;
        }
        .contact-addr {
            font-size: 0.9rem;
            color: #555;
            line-height: 1.6;
            margin-bottom: 0.8rem;
        }
        .contact-detail {
            font-size: 0.9rem;
            color: #555;
            margin-bottom: 0.2rem;
        }
        .contact-detail a { color: #003071; text-decoration: none; }
        .contact-detail a:hover { text-decoration: underline; }
        .contact-link-btn {
            display: inline-block;
            margin-top: 1rem;
            padding: 0.6rem 1.4rem;
            background: #003071;
            color: white !important;
            border-radius: 4px;
            font-size: 0.9rem;
            font-weight: 600;
            text-decoration: none;
            letter-spacing: 0.5px;
        }
        .contact-link-btn:hover { background: #00245a; text-decoration: none !important; }
        .contact-link-btn.gold { background: #FFD700; color: #003071 !important; }
        .contact-link-btn.gold:hover { background: #e6c200; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="breadcrumb"><a href="?auth=1&page=home">Home</a> &rsaquo; Talk With Us</div>
        <div class="page-header">Talk With Us</div>
        <div class="page-subtitle">Reach out to the Center on Poverty &amp; Community Development at Case Western Reserve University.</div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
            <div class="contact-card">
                <div class="contact-card-title">Mailing Address</div>
                <div class="contact-org">Center on Poverty &amp; Community Development</div>
                <div class="contact-school">Jack, Joseph and Morton Mandel School of Applied Social Sciences</div>
                <div class="contact-univ">Case Western Reserve University</div>
                <div class="contact-addr">
                    10900 Euclid Avenue<br>
                    Cleveland, Ohio 44106-7167
                </div>
                <div class="contact-detail">Tel: <a href="tel:2163686946">216.368.6946</a></div>
                <div class="contact-detail">Fax: 216.368.8592</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="contact-card">
                <div class="contact-card-title">Location &amp; Visitor Address</div>
                <div class="contact-org">Center on Poverty &amp; Community Development</div>
                <div class="contact-school">Jack, Joseph and Morton Mandel Community Studies Center</div>
                <div class="contact-univ">Case Western Reserve University</div>
                <div class="contact-addr">
                    11402 Bellflower Road<br>
                    Cleveland, Ohio 44106-7167
                </div>
                <div class="contact-detail">Tel: <a href="tel:2163686946">216.368.6946</a></div>
                <div class="contact-detail">Fax: 216.368.8592</div>
                <div class="contact-detail">Email: <a href="mailto:povcenter@case.edu">povcenter@case.edu</a></div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("""
        <div class="contact-card" style="text-align:center; padding: 2rem;">
            <div class="contact-card-title" style="text-align:center; border-bottom:none; margin-bottom:0.8rem;">Get in Touch</div>
            <p style="color:#555; font-size:0.95rem; margin-bottom:1.5rem;">
                Visit the Poverty Center's website to learn more about our research and team,
                or go directly to our faculty and staff directory to reach a specific person.
            </p>
            <a href="https://case.edu/socialwork/povertycenter/" target="_blank" class="contact-link-btn" style="margin-right:1rem;">
                Poverty Center Website
            </a>
            <a href="https://case.edu/socialwork/povertycenter/about/faculty-staff" target="_blank" class="contact-link-btn gold">
                Faculty &amp; Staff Directory
            </a>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #666; padding: 2rem 0;">
            <p>Powered by CWRU Poverty Center | Last Updated: March 2026</p>
        </div>
    """, unsafe_allow_html=True)


else:
    # ========================================================
    #  HOME PAGE — Landing page with hero, cards, partners
    # ========================================================

    # Hero banner with backdrop image
    st.markdown(f"""
        <div class="hero-section" style="background-image: url('data:image/jpeg;base64,{hero_backdrop_base64}');">
            <div class="hero-overlay"></div>
            <div class="hero-content">
                <div class="hero-subtitle">POVERTY CENTER AT CASE WESTERN RESERVE UNIVERSITY</div>
                <div class="hero-title">CLEVELAND'S<br>NEIGHBORHOOD STRATEGY TECHNOLOGY</div>
                <div class="hero-buttons">
                    <a href="?auth=1&page=datasets" target="_self" class="hero-button">Find Data</a>
                    <a href="#" class="hero-button">Popular Projects</a>
                    <a href="https://case.edu/socialwork/povertycenter/about" target="_blank" class="hero-button">Learn More</a>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Welcome text
    st.markdown("""
    ### Welcome to NST!

    The Neighborhood Strategy Technology Web Application (NST) enables a diverse group of
    government and community agencies to collaborate in improving the communities of Cleveland
    and Cuyahoga County. Quickly access information on property ownership, occupancy and vacancy,
    foreclosure, sheriff's sale, and REO history, detailed tax information, code enforcement
    information, demolition information, property surveys conducted by area agencies, and more.
    In addition to linking and making data available, NST also serves as a communication platform
    and place for agencies to house their own data. Users can access, filter, and map data, as
    well as save custom queries and download spreadsheets of data.
    """)

    st.markdown("---")

    # Get Started cards — link to main features
    st.markdown("""
        <div class="data-section-title">GET STARTED</div>
        <div class="data-cards-container">
            <a href="?auth=1&page=maps" target="_self" class="data-card" style="text-decoration:none;">
                <div class="data-card-title">Map Explorer</div>
                <p style="color: #666; font-size: 1.1rem; margin-top: 1rem;">
                    Visualize neighborhood data on interactive maps
                </p>
            </a>
            <a href="?auth=1&page=datasets" target="_self" class="data-card" style="text-decoration:none;">
                <div class="data-card-title">Browse Data</div>
                <p style="color: #666; font-size: 1.1rem; margin-top: 1rem;">
                    Explore comprehensive datasets and statistics
                </p>
            </a>
            <a href="?auth=1&page=property-search" target="_self" class="data-card" style="text-decoration:none;">
                <div class="data-card-title">Search Properties</div>
                <p style="color: #666; font-size: 1.1rem; margin-top: 1rem;">
                    Find detailed information on specific properties
                </p>
            </a>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Partners section
    st.markdown(f"""
        <div class="partners-section-title">OUR DATA PARTNERS</div>
        <div class="partners-grid" style="grid-template-columns: repeat(4, 1fr);">
            <div class="partner-logo">
                <a href="https://clevelandohio.gov" target="_blank" rel="noopener">
                    <img src="data:image/svg+xml;base64,{partner_cleveland_base64}" alt="City of Cleveland" style="max-height:70px;">
                </a>
            </div>
            <div class="partner-logo">
                <a href="https://www.cuyahogacounty.gov/fiscal-officer" target="_blank" rel="noopener">
                    <img src="data:image/svg+xml;base64,{partner_cuyahoga_base64}" alt="Cuyahoga County" style="max-height:70px;">
                </a>
            </div>
            <div class="partner-logo">
                <a href="https://cuyahogalandbank.org" target="_blank" rel="noopener">
                    <img src="data:image/svg+xml;base64,{partner_cclrc_base64}" alt="Cuyahoga Land Bank" style="max-height:70px;">
                </a>
            </div>
            <div class="partner-logo">
                <a href="https://www.census.gov" target="_blank" rel="noopener">
                    <img src="data:image/svg+xml;base64,{partner_census_base64}" alt="U.S. Census Bureau" style="max-height:70px;">
                </a>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Contribute CTA
    st.markdown("""
        <div class="contribute-section">
            <div class="contribute-title">Want to share data through your organization?</div>
            <a href="?auth=1&page=contact" target="_self" class="contribute-button">TALK WITH US</a>
        </div>
    """, unsafe_allow_html=True)

    # -- Footer --
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #666; padding: 2rem 0;">
            <p>Powered by CWRU Poverty Center | Last Updated: January 2026</p>
        </div>
    """, unsafe_allow_html=True)


