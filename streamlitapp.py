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
from PIL import Image
import base64
import pandas as pd
import json
import io
import zipfile

# ============================================================
#  SETUP — Assets, page config, routing
# ============================================================

# Load logo images and encode as base64 for use in HTML
logo = Image.open("assets/logo.jpg")

def get_base64_image(image_path):
    """Convert an image file to a base64 string for embedding in HTML."""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

navbar_logo_base64 = get_base64_image("assets/upperleft logo.jpg")
hero_backdrop_base64 = get_base64_image("assets/cleveland backdrop.jpg")

# Streamlit page config (must be first st. call)
st.set_page_config(
    page_title="Cleveland NST 2.0",
    page_icon=logo,
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
#  To add a new page: add a dropdown-item with href="?page=<name>"
#  IMPORTANT: always include target="_self" on links
# ============================================================
st.markdown(f"""
    <div class="navbar">
        <div class="navbar-container">
            <div class="navbar-brand">
                <a href="?page=home" target="_self"><img src="data:image/jpeg;base64,{navbar_logo_base64}" alt="Cleveland NST Logo"></a>
            </div>
            <ul class="navbar-menu">
                <li class="navbar-item">
                    <a href="?page=home" target="_self" class="navbar-link navbar-link-home">Home</a>
                </li>
                <li class="navbar-item">
                    <a href="#" class="navbar-link">Data</a>
                    <div class="dropdown-menu">
                        <a href="?page=datasets" target="_self" class="dropdown-item">
                            <div class="dropdown-item-title">Datasets</div>
                            <div class="dropdown-item-description">Browse and download comprehensive neighborhood data</div>
                        </a>
                        <a href="?page=maps" target="_self" class="dropdown-item">
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
                        <a href="?page=methodology" target="_self" class="dropdown-item">
                            <div class="dropdown-item-title">Methodology</div>
                            <div class="dropdown-item-description">Our data collection and analysis approach</div>
                        </a>
                        <a href="?page=projects" target="_self" class="dropdown-item">
                            <div class="dropdown-item-title">Projects</div>
                            <div class="dropdown-item-description">Dedicated pages for each of our projects</div>
                        </a>
                    </div>
                </li>
                <li class="navbar-item">
                    <a href="#" class="navbar-link">Resources</a>
                    <div class="dropdown-menu">
                        <a href="?page=resources" target="_self" class="dropdown-item">
                            <div class="dropdown-item-title">Resources</div>
                            <div class="dropdown-item-description">Tools and guides for using NST data</div>
                        </a>
                        <a href="https://case.edu/socialwork/povertycenter/about/contact-us" target="_blank" class="dropdown-item">
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
#    2. Add a navbar link with href="?page=your-page"
# ############################################################

if current_page == "datasets":
    # ========================================================
    #  DATASETS PAGE — Browse, filter, and export property data
    #  Two search modes: Guided Search (simple) and Advanced Filters (power user)
    #  Results shown in tabs: Table, Map, Charts, Summary
    # ========================================================

    # -- Load data (cached so it only reads CSV once) --
    @st.cache_data
    def load_data():
        return pd.read_csv("data/nst_sample_data.csv")

    df = load_data()

    # -- Page-specific CSS --
    st.markdown("""
        <style>
        .breadcrumb {
            font-size: 0.95rem;
            color: #666;
            margin-bottom: 1.5rem;
        }
        .breadcrumb a {
            color: #003071;
            text-decoration: none;
        }
        .breadcrumb a:hover {
            text-decoration: underline;
        }
        .page-header {
            font-size: 2.5rem;
            font-weight: 700;
            color: #003071;
            margin-bottom: 0.3rem;
        }
        .page-subtitle {
            font-size: 1.1rem;
            color: #666;
            margin-bottom: 1rem;
        }
        .stat-box {
            background: #f8f9fc;
            border-left: 4px solid #003071;
            padding: 1rem 1.2rem;
            border-radius: 4px;
        }
        .stat-box .stat-value {
            font-size: 1.6rem;
            font-weight: 700;
            color: #003071;
        }
        .stat-box .stat-label {
            font-size: 0.85rem;
            color: #666;
        }
        </style>
    """, unsafe_allow_html=True)

    # -- Breadcrumb --
    st.markdown("""
        <div class="breadcrumb">
            <a href="?page=home" target="_self">Home</a> &nbsp;/&nbsp; <strong>Datasets</strong>
        </div>
    """, unsafe_allow_html=True)

    # -- Page header --
    st.markdown("""
        <div class="page-header">Datasets</div>
        <div class="page-subtitle">Browse and download comprehensive neighborhood data for Cleveland and Cuyahoga County.</div>
    """, unsafe_allow_html=True)

    # -- Search bar (searches combined "house_number street_name" or parcel_number) --
    search_query = st.text_input(
        "Search by address or parcel ID",
        placeholder="e.g. 1725 Pearl Rd or 754-24-125",
        label_visibility="collapsed",
    )

    st.markdown("---")

    # -- Two-path toggle: Guided Search vs Advanced Filters --
    search_mode = st.radio(
        "Choose how to search",
        ["Guided Search", "Advanced Filters"],
        horizontal=True,
        label_visibility="collapsed",
    )

    # -- Apply address/parcel search first --
    filtered_df = df.copy()
    if search_query:
        full_address = filtered_df["house_number"].astype(str) + " " + filtered_df["street_name"].fillna("")
        mask = (
            full_address.str.contains(search_query, case=False, na=False)
            | filtered_df["parcel_number"].str.contains(search_query, case=False, na=False)
        )
        filtered_df = filtered_df[mask]

    # -- PATH 1: GUIDED SEARCH --
    # Shows different filter sets based on what the user is looking for.
    if search_mode == "Guided Search":
        guided_choice = st.radio(
            "What are you looking for?",
            [
                "Properties in a specific neighborhood",
                "Properties with certain characteristics",
                "Properties by owner type",
                "Properties with violations or permits",
                "Custom advanced search",
            ],
        )

        if guided_choice == "Properties in a specific neighborhood":
            g_col1, g_col2 = st.columns(2)
            with g_col1:
                g_neighborhood = st.selectbox("Neighborhood", ["All"] + sorted(df["neighborhood"].unique().tolist()))
            with g_col2:
                g_ward = st.selectbox("Ward", ["All"] + sorted(df["ward"].dropna().unique().astype(int).astype(str).tolist()))
            if g_neighborhood != "All":
                filtered_df = filtered_df[filtered_df["neighborhood"] == g_neighborhood]
            if g_ward != "All":
                filtered_df = filtered_df[filtered_df["ward"] == int(g_ward)]

        elif guided_choice == "Properties with certain characteristics":
            g_col1, g_col2, g_col3 = st.columns(3)
            with g_col1:
                g_prop_type = st.selectbox("Property Type", ["All"] + sorted(df["property_type"].unique().tolist()))
            with g_col2:
                yr_min, yr_max = int(df["year_built"].min()), int(df["year_built"].max())
                g_year_range = st.slider("Year Built", yr_min, yr_max, (yr_min, yr_max))
            with g_col3:
                g_condition = st.selectbox("Condition", ["All"] + sorted(df["property_condition"].dropna().unique().tolist()))
            if g_prop_type != "All":
                filtered_df = filtered_df[filtered_df["property_type"] == g_prop_type]
            filtered_df = filtered_df[(filtered_df["year_built"] >= g_year_range[0]) & (filtered_df["year_built"] <= g_year_range[1])]
            if g_condition != "All":
                filtered_df = filtered_df[filtered_df["property_condition"] == g_condition]

        elif guided_choice == "Properties by owner type":
            g_col1, g_col2 = st.columns(2)
            with g_col1:
                g_owner = st.selectbox("Owner Type", ["All"] + sorted(df["owner_type"].unique().tolist()))
            with g_col2:
                g_vacancy = st.selectbox("Vacancy Status", ["All"] + sorted(df["vacancy_status"].dropna().unique().tolist()))
            if g_owner != "All":
                filtered_df = filtered_df[filtered_df["owner_type"] == g_owner]
            if g_vacancy != "All":
                filtered_df = filtered_df[filtered_df["vacancy_status"] == g_vacancy]

        elif guided_choice == "Properties with violations or permits":
            g_col1, g_col2, g_col3 = st.columns(3)
            with g_col1:
                g_lead = st.checkbox("Has lead violations")
            with g_col2:
                g_building = st.checkbox("Has building violations")
            with g_col3:
                g_code = st.checkbox("Has code violations")
            if g_lead:
                filtered_df = filtered_df[filtered_df["lead_violations"] > 0]
            if g_building:
                filtered_df = filtered_df[filtered_df["building_violations"] > 0]
            if g_code:
                filtered_df = filtered_df[filtered_df["code_violations"] > 0]

            g_col4, g_col5 = st.columns(2)
            with g_col4:
                g_foreclosure = st.selectbox("Foreclosure Status", ["All"] + sorted(df["foreclosure_status"].dropna().unique().tolist()))
            with g_col5:
                g_tax_del = st.checkbox("Tax delinquent only")
            if g_foreclosure != "All":
                filtered_df = filtered_df[filtered_df["foreclosure_status"] == g_foreclosure]
            if g_tax_del:
                filtered_df = filtered_df[filtered_df["tax_delinquent"] == True]

        else:  # "Custom advanced search"
            st.info("Use the Advanced Filters tab for full control over all filters.")

    # -- PATH 2: ADVANCED FILTERS --
    # All filters visible at once, with an expandable "More Filters" section.
    else:
        # Quick filters (always visible)
        qf1, qf2, qf3 = st.columns(3)
        with qf1:
            adv_neighborhood = st.selectbox("Neighborhood", ["All"] + sorted(df["neighborhood"].unique().tolist()), key="adv_n")
        with qf2:
            adv_prop_type = st.selectbox("Property Type", ["All"] + sorted(df["property_type"].unique().tolist()), key="adv_pt")
        with qf3:
            yr_min, yr_max = int(df["year_built"].min()), int(df["year_built"].max())
            adv_year_range = st.slider("Year Built", yr_min, yr_max, (yr_min, yr_max), key="adv_yr")

        if adv_neighborhood != "All":
            filtered_df = filtered_df[filtered_df["neighborhood"] == adv_neighborhood]
        if adv_prop_type != "All":
            filtered_df = filtered_df[filtered_df["property_type"] == adv_prop_type]
        filtered_df = filtered_df[(filtered_df["year_built"] >= adv_year_range[0]) & (filtered_df["year_built"] <= adv_year_range[1])]

        # Expandable extra filters
        with st.expander("More Filters"):
            af1, af2, af3, af4 = st.columns(4)
            with af1:
                adv_owner = st.selectbox("Owner Type", ["All"] + sorted(df["owner_type"].unique().tolist()), key="adv_ot")
            with af2:
                adv_vacancy = st.selectbox("Vacancy Status", ["All"] + sorted(df["vacancy_status"].dropna().unique().tolist()), key="adv_vs")
            with af3:
                adv_condition = st.selectbox("Condition", ["All"] + sorted(df["property_condition"].dropna().unique().tolist()), key="adv_cond")
            with af4:
                adv_foreclosure = st.selectbox("Foreclosure", ["All"] + sorted(df["foreclosure_status"].dropna().unique().tolist()), key="adv_fc")

            af5, af6, af7 = st.columns(3)
            with af5:
                val_min, val_max = int(df["property_value"].min()), int(df["property_value"].max())
                adv_value_range = st.slider("Property Value ($)", val_min, val_max, (val_min, val_max), step=5000, key="adv_val")
            with af6:
                adv_lead = st.checkbox("Has lead violations", key="adv_lead")
            with af7:
                adv_tax_del = st.checkbox("Tax delinquent only", key="adv_tax")

            if adv_owner != "All":
                filtered_df = filtered_df[filtered_df["owner_type"] == adv_owner]
            if adv_vacancy != "All":
                filtered_df = filtered_df[filtered_df["vacancy_status"] == adv_vacancy]
            if adv_condition != "All":
                filtered_df = filtered_df[filtered_df["property_condition"] == adv_condition]
            if adv_foreclosure != "All":
                filtered_df = filtered_df[filtered_df["foreclosure_status"] == adv_foreclosure]
            filtered_df = filtered_df[(filtered_df["property_value"] >= adv_value_range[0]) & (filtered_df["property_value"] <= adv_value_range[1])]
            if adv_lead:
                filtered_df = filtered_df[filtered_df["lead_violations"] > 0]
            if adv_tax_del:
                filtered_df = filtered_df[filtered_df["tax_delinquent"] == True]

    # -- RESULTS SECTION --
    st.markdown("---")

    # Summary stat boxes
    total = len(filtered_df)
    avg_val = int(filtered_df["property_value"].mean()) if total > 0 else 0
    vacancy_rate = round((filtered_df["vacancy_status"] == "Vacant").sum() / total * 100, 1) if total > 0 else 0
    total_violations = int(filtered_df["lead_violations"].sum() + filtered_df["building_violations"].sum() + filtered_df["code_violations"].sum()) if total > 0 else 0

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(f"""<div class="stat-box"><div class="stat-value">{total:,}</div><div class="stat-label">Properties</div></div>""", unsafe_allow_html=True)
    with s2:
        st.markdown(f"""<div class="stat-box"><div class="stat-value">${avg_val:,}</div><div class="stat-label">Avg Value</div></div>""", unsafe_allow_html=True)
    with s3:
        st.markdown(f"""<div class="stat-box"><div class="stat-value">{vacancy_rate}%</div><div class="stat-label">Vacancy Rate</div></div>""", unsafe_allow_html=True)
    with s4:
        st.markdown(f"""<div class="stat-box"><div class="stat-value">{total_violations:,}</div><div class="stat-label">Total Violations</div></div>""", unsafe_allow_html=True)

    st.markdown("")

    # Column picker — lets user choose which columns to show in the table
    all_columns = filtered_df.columns.tolist()
    default_columns = ["parcel_number", "house_number", "street_name", "neighborhood", "property_type", "property_value", "owner_type", "vacancy_status"]
    display_columns = st.multiselect(
        "Select columns to display",
        all_columns,
        default=[c for c in default_columns if c in all_columns],
    )
    if not display_columns:
        display_columns = default_columns

    # Results tabs
    tab_table, tab_map, tab_charts, tab_summary = st.tabs(["Table View", "Map View", "Charts", "Summary"])

    with tab_table:
        st.dataframe(
            filtered_df[display_columns].reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
            height=500,
        )

    with tab_map:
        if total > 0 and total <= 5000:
            st.map(
                filtered_df[["latitude", "longitude"]].dropna(),
                latitude="latitude",
                longitude="longitude",
            )
        elif total > 5000:
            st.warning("Too many points to display. Apply more filters to narrow results.")
        else:
            st.info("No properties to display on the map.")

    with tab_charts:
        if total > 0:
            ch1, ch2 = st.columns(2)
            with ch1:
                type_counts = filtered_df["property_type"].value_counts()
                st.bar_chart(type_counts, color="#003071")
                st.caption("Properties by Type")
            with ch2:
                owner_counts = filtered_df["owner_type"].value_counts()
                st.bar_chart(owner_counts, color="#003071")
                st.caption("Properties by Owner Type")

            ch3, ch4 = st.columns(2)
            with ch3:
                vacancy_counts = filtered_df["vacancy_status"].value_counts()
                st.bar_chart(vacancy_counts, color="#003071")
                st.caption("Vacancy Status")
            with ch4:
                condition_counts = filtered_df["property_condition"].value_counts()
                st.bar_chart(condition_counts, color="#003071")
                st.caption("Property Condition")
        else:
            st.info("No data to chart. Adjust your filters.")

    with tab_summary:
        if total > 0:
            su1, su2 = st.columns(2)
            with su1:
                st.markdown("**Value Statistics**")
                st.dataframe(
                    filtered_df[["property_value", "assessed_value", "annual_tax", "last_sale_price"]].describe().round(0),
                    use_container_width=True,
                )
            with su2:
                st.markdown("**Top Neighborhoods**")
                top_neighborhoods = filtered_df["neighborhood"].value_counts().head(10)
                st.dataframe(top_neighborhoods, use_container_width=True)

            su3, su4 = st.columns(2)
            with su3:
                st.markdown("**Violation Breakdown**")
                violation_summary = pd.DataFrame({
                    "Violation Type": ["Lead", "Building", "Code"],
                    "Properties Affected": [
                        int((filtered_df["lead_violations"] > 0).sum()),
                        int((filtered_df["building_violations"] > 0).sum()),
                        int((filtered_df["code_violations"] > 0).sum()),
                    ],
                    "Total Count": [
                        int(filtered_df["lead_violations"].sum()),
                        int(filtered_df["building_violations"].sum()),
                        int(filtered_df["code_violations"].sum()),
                    ],
                })
                st.dataframe(violation_summary, use_container_width=True, hide_index=True)
            with su4:
                st.markdown("**Foreclosure Status**")
                fc_counts = filtered_df["foreclosure_status"].value_counts()
                st.dataframe(fc_counts, use_container_width=True)
        else:
            st.info("No data to summarize. Adjust your filters.")

    # -- EXPORT SECTION --
    # Supports CSV, GeoJSON, and Shapefile (requires geopandas).
    st.markdown("---")
    st.markdown("""
        <style>
        [data-testid="stExpander"] details summary p {
            font-size: 1.5rem !important;
            font-weight: 700 !important;
            color: #003071 !important;
        }
        [data-testid="stExpander"] details {
            border: 2px solid #003071 !important;
            border-radius: 8px !important;
            padding: 0.3rem !important;
        }
        </style>
    """, unsafe_allow_html=True)
    with st.expander("Export Options"):
        ex_col1, ex_col2 = st.columns(2)
        with ex_col1:
            export_format = st.radio(
                "Format",
                ["CSV (Excel-friendly)", "GeoJSON (mapping)", "Shapefile (GIS software)"],
                key="export_fmt",
            )
        with ex_col2:
            export_columns = st.radio(
                "Columns",
                ["Selected columns only", "All available columns"],
                key="export_cols",
            )

        export_df = filtered_df if export_columns == "All available columns" else filtered_df[display_columns]

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
            source_df = filtered_df
            features = []
            for _, row in source_df.iterrows():
                lat = row.get("latitude")
                lon = row.get("longitude")
                if pd.notna(lat) and pd.notna(lon):
                    if export_columns == "Selected columns only":
                        props = {c: (row[c].item() if hasattr(row[c], "item") else row[c]) for c in display_columns if c not in ("latitude", "longitude")}
                    else:
                        props = {c: (row[c].item() if hasattr(row[c], "item") else row[c]) for c in all_columns if c not in ("latitude", "longitude")}
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
        else:  # Shapefile — requires geopandas + shapely
            try:
                import geopandas as gpd
                from shapely.geometry import Point

                geo_rows = filtered_df.dropna(subset=["latitude", "longitude"])
                geometry = [Point(lon, lat) for lat, lon in zip(geo_rows["latitude"], geo_rows["longitude"])]
                if export_columns == "Selected columns only":
                    cols = [c for c in display_columns if c not in ("latitude", "longitude")]
                else:
                    cols = [c for c in all_columns if c not in ("latitude", "longitude")]
                gdf = gpd.GeoDataFrame(geo_rows[cols].reset_index(drop=True), geometry=geometry, crs="EPSG:4326")

                import tempfile, os, glob as glob_mod
                with tempfile.TemporaryDirectory() as tmpdir:
                    shp_path = os.path.join(tmpdir, "nst_export.shp")
                    gdf.to_file(shp_path, driver="ESRI Shapefile")
                    buf = io.BytesIO()
                    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                        for f in glob_mod.glob(os.path.join(tmpdir, "nst_export.*")):
                            zf.write(f, os.path.basename(f))
                    buf.seek(0)
                st.download_button(
                    label=f"Download {len(geo_rows):,} features as Shapefile (.zip)",
                    data=buf.getvalue(),
                    file_name="nst_export_shp.zip",
                    mime="application/zip",
                )
            except ImportError:
                st.warning("Shapefile export requires `geopandas` and `shapely`. Install them with:")
                st.code("pip install geopandas shapely", language="bash")

    # -- Footer --
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #666; padding: 2rem 0;">
            <p>Powered by CWRU Poverty Center | Last Updated: January 2026</p>
        </div>
    """, unsafe_allow_html=True)


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

    # -- Load data --
    @st.cache_data
    def load_map_data():
        return pd.read_csv("data/nst_sample_data.csv")

    df_map = load_map_data()

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

    # --------------------------------------------------------
    #  STATE 1: NEIGHBORHOOD PROFILE (when ?hood= is set)
    # --------------------------------------------------------
    if selected_hood and selected_hood in df_map["neighborhood"].unique():
        hood_df = df_map[df_map["neighborhood"] == selected_hood]

        # Breadcrumb
        st.markdown(f"""
            <div class="breadcrumb">
                <a href="?page=home" target="_self">Home</a> &nbsp;/&nbsp;
                <a href="?page=maps" target="_self">Map Explorer</a> &nbsp;/&nbsp;
                <strong>{selected_hood}</strong>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<a href="?page=maps" target="_self" class="hood-back-link">&larr; Back to Map</a>', unsafe_allow_html=True)

        # Header with ward/zip info
        wards_in_hood = sorted(hood_df["ward"].dropna().unique().astype(int).tolist())
        zips_in_hood = sorted(hood_df["zip_code"].dropna().unique().astype(int).tolist())
        st.markdown(f'<div class="hood-profile-header">{selected_hood}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="hood-profile-sub">Ward{"s" if len(wards_in_hood) > 1 else ""} {", ".join(str(w) for w in wards_in_hood)} &nbsp;|&nbsp; ZIP{"s" if len(zips_in_hood) > 1 else ""} {", ".join(str(z) for z in zips_in_hood)}</div>', unsafe_allow_html=True)

        # -- Key metrics (3x3 grid) --
        n_total = len(hood_df)
        n_avg_val = int(hood_df["property_value"].mean()) if n_total > 0 else 0
        n_median_val = int(hood_df["property_value"].median()) if n_total > 0 else 0
        n_vacancy = round((hood_df["vacancy_status"] == "Vacant").sum() / n_total * 100, 1) if n_total > 0 else 0
        n_violations = int(hood_df["lead_violations"].sum() + hood_df["building_violations"].sum() + hood_df["code_violations"].sum()) if n_total > 0 else 0
        n_foreclosure = int((hood_df["foreclosure_status"] != "None").sum()) if n_total > 0 else 0
        n_tax_del = int(hood_df["tax_delinquent"].sum()) if n_total > 0 else 0
        n_median_income = int(hood_df["median_income_tract"].mean()) if n_total > 0 else 0
        n_poverty_rate = round(hood_df["poverty_rate_tract"].mean(), 1) if n_total > 0 else 0

        st.markdown(f"""
            <div class="hood-stat-grid">
                <div class="hood-stat-card">
                    <div class="hood-stat-card-value">{n_total:,}</div>
                    <div class="hood-stat-card-label">Total Properties</div>
                </div>
                <div class="hood-stat-card">
                    <div class="hood-stat-card-value">${n_avg_val:,}</div>
                    <div class="hood-stat-card-label">Avg Property Value</div>
                </div>
                <div class="hood-stat-card">
                    <div class="hood-stat-card-value">${n_median_val:,}</div>
                    <div class="hood-stat-card-label">Median Property Value</div>
                </div>
                <div class="hood-stat-card">
                    <div class="hood-stat-card-value">{n_vacancy}%</div>
                    <div class="hood-stat-card-label">Vacancy Rate</div>
                </div>
                <div class="hood-stat-card">
                    <div class="hood-stat-card-value">{n_violations:,}</div>
                    <div class="hood-stat-card-label">Total Violations</div>
                </div>
                <div class="hood-stat-card">
                    <div class="hood-stat-card-value">{n_foreclosure:,}</div>
                    <div class="hood-stat-card-label">Foreclosures</div>
                </div>
                <div class="hood-stat-card">
                    <div class="hood-stat-card-value">{n_tax_del:,}</div>
                    <div class="hood-stat-card-label">Tax Delinquent</div>
                </div>
                <div class="hood-stat-card">
                    <div class="hood-stat-card-value">${n_median_income:,}</div>
                    <div class="hood-stat-card-label">Median Income (Tract)</div>
                </div>
                <div class="hood-stat-card">
                    <div class="hood-stat-card-value">{n_poverty_rate}%</div>
                    <div class="hood-stat-card-label">Poverty Rate (Tract)</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # -- Tabs: Overview, Property Data, Download --
        tab_overview, tab_data, tab_download = st.tabs(["Overview", "Property Data", "Download"])

        with tab_overview:
            # Charts: property type + owner type
            st.markdown('<div class="hood-section-title">Property Breakdown</div>', unsafe_allow_html=True)
            ov1, ov2 = st.columns(2)
            with ov1:
                st.bar_chart(hood_df["property_type"].value_counts(), color="#003071")
                st.caption("Properties by Type")
            with ov2:
                st.bar_chart(hood_df["owner_type"].value_counts(), color="#003071")
                st.caption("Properties by Owner Type")

            # Charts: vacancy + condition
            st.markdown('<div class="hood-section-title">Property Status</div>', unsafe_allow_html=True)
            ov3, ov4 = st.columns(2)
            with ov3:
                st.bar_chart(hood_df["vacancy_status"].value_counts(), color="#003071")
                st.caption("Vacancy Status")
            with ov4:
                st.bar_chart(hood_df["property_condition"].value_counts(), color="#003071")
                st.caption("Property Condition")

            # Violations table + foreclosure chart
            st.markdown('<div class="hood-section-title">Violations & Foreclosure</div>', unsafe_allow_html=True)
            ov5, ov6 = st.columns(2)
            with ov5:
                violation_summary = pd.DataFrame({
                    "Type": ["Lead", "Building", "Code"],
                    "Properties Affected": [
                        int((hood_df["lead_violations"] > 0).sum()),
                        int((hood_df["building_violations"] > 0).sum()),
                        int((hood_df["code_violations"] > 0).sum()),
                    ],
                })
                st.dataframe(violation_summary, use_container_width=True, hide_index=True)
            with ov6:
                st.bar_chart(hood_df["foreclosure_status"].value_counts(), color="#003071")
                st.caption("Foreclosure Status")

            # Value statistics table
            st.markdown('<div class="hood-section-title">Value Statistics</div>', unsafe_allow_html=True)
            st.dataframe(
                hood_df[["property_value", "assessed_value", "annual_tax", "last_sale_price"]].describe().round(0),
                use_container_width=True,
            )

            # Folium map zoomed into this neighborhood
            st.markdown('<div class="hood-section-title">Neighborhood Map</div>', unsafe_allow_html=True)
            hood_map_data = hood_df[["latitude", "longitude"]].dropna()
            if len(hood_map_data) > 0:
                center_lat = hood_map_data["latitude"].mean()
                center_lon = hood_map_data["longitude"].mean()
                m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles="CartoDB positron")
                for _, prop in hood_df.iterrows():
                    if pd.notna(prop["latitude"]) and pd.notna(prop["longitude"]):
                        folium.CircleMarker(
                            location=[prop["latitude"], prop["longitude"]],
                            radius=5,
                            color="#003071",
                            fill=True,
                            fillColor="#003071",
                            fillOpacity=0.5,
                            tooltip=f"{int(prop['house_number'])} {prop['street_name']}",
                            popup=folium.Popup(
                                f"<b>{int(prop['house_number'])} {prop['street_name']}</b><br>"
                                f"Type: {prop['property_type']}<br>"
                                f"Value: ${int(prop['property_value']):,}<br>"
                                f"Owner: {prop['owner_type']}<br>"
                                f"Status: {prop['vacancy_status']}",
                                max_width=200,
                            ),
                        ).add_to(m)
                st_folium(m, width=None, height=450, use_container_width=True)

        with tab_data:
            st.markdown(f"**{n_total:,} properties in {selected_hood}**")

            # Column picker
            all_cols = hood_df.columns.tolist()
            default_cols = ["parcel_number", "house_number", "street_name", "property_type", "property_value", "owner_type", "vacancy_status", "property_condition"]
            show_cols = st.multiselect("Select columns to display", all_cols, default=[c for c in default_cols if c in all_cols], key="hood_cols")
            if not show_cols:
                show_cols = default_cols

            st.dataframe(
                hood_df[show_cols].reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
                height=500,
            )

        with tab_download:
            st.markdown(f"### Download {selected_hood} Data")
            st.markdown(f"Export all **{n_total:,} properties** in {selected_hood}.")

            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                dl_format = st.radio("Format", ["CSV (Excel-friendly)", "GeoJSON (mapping)"], key="hood_dl_fmt")
            with dl_col2:
                dl_columns = st.radio("Columns", ["All columns", "Selected columns only"], key="hood_dl_cols")

            if dl_columns == "Selected columns only":
                export_hood_df = hood_df[show_cols] if 'show_cols' in dir() else hood_df
            else:
                export_hood_df = hood_df

            if dl_format == "CSV (Excel-friendly)":
                csv_data = export_hood_df.to_csv(index=False)
                st.download_button(
                    label=f"Download {n_total:,} properties as CSV",
                    data=csv_data,
                    file_name=f"nst_{selected_hood.lower().replace(' ', '_')}.csv",
                    mime="text/csv",
                )
            else:  # GeoJSON
                features = []
                for _, row in hood_df.iterrows():
                    lat = row.get("latitude")
                    lon = row.get("longitude")
                    if pd.notna(lat) and pd.notna(lon):
                        if dl_columns == "Selected columns only" and 'show_cols' in dir():
                            props = {c: (row[c].item() if hasattr(row[c], "item") else row[c]) for c in show_cols if c not in ("latitude", "longitude")}
                        else:
                            props = {c: (row[c].item() if hasattr(row[c], "item") else row[c]) for c in all_cols if c not in ("latitude", "longitude")}
                        features.append({
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
                            "properties": props,
                        })
                geojson = json.dumps({"type": "FeatureCollection", "features": features})
                st.download_button(
                    label=f"Download {len(features):,} features as GeoJSON",
                    data=geojson,
                    file_name=f"nst_{selected_hood.lower().replace(' ', '_')}.geojson",
                    mime="application/geo+json",
                )

    # --------------------------------------------------------
    #  STATE 2: MAP OVERVIEW (default — no hood selected)
    # --------------------------------------------------------
    else:
        # Breadcrumb
        st.markdown("""
            <div class="breadcrumb">
                <a href="?page=home" target="_self">Home</a> &nbsp;/&nbsp; <strong>Map Explorer</strong>
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
            neighborhoods = sorted(df_map["neighborhood"].unique().tolist())
            selected_from_dropdown = st.selectbox("Or select a neighborhood", [""] + neighborhoods, key="map_hood_select", format_func=lambda x: "Choose a neighborhood..." if x == "" else x)
            if selected_from_dropdown:
                st.query_params["page"] = "maps"
                st.query_params["hood"] = selected_from_dropdown
                st.rerun()

            st.markdown("---")

            # Scrollable neighborhood list with property counts
            st.markdown("**All Neighborhoods**")
            hood_counts = df_map["neighborhood"].value_counts().sort_index()
            hood_list_html = ""
            for hood_name, count in hood_counts.items():
                hood_list_html += f'<a href="?page=maps&hood={hood_name}" target="_self" class="hood-list-item">{hood_name}<span class="hood-list-item-count">{count}</span></a>'
            st.markdown(f'<div style="max-height:400px;overflow-y:auto;border:1px solid #e0e0e0;border-radius:6px;">{hood_list_html}</div>', unsafe_allow_html=True)

        with map_col:
            # Aggregate stats per neighborhood for circle markers
            hood_summary = df_map.groupby("neighborhood").agg(
                lat=("latitude", "mean"),
                lon=("longitude", "mean"),
                count=("parcel_number", "count"),
                avg_value=("property_value", "mean"),
                vacancy_pct=("vacancy_status", lambda x: (x == "Vacant").mean() * 100),
            ).reset_index()

            # Assign a unique color to each neighborhood
            hood_colors = [
                "#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6",
                "#1abc9c", "#e67e22", "#2980b9", "#c0392b", "#27ae60",
                "#d35400", "#8e44ad", "#16a085", "#f1c40f", "#2c3e50",
                "#7f8c8d", "#e84393", "#00cec9", "#6c5ce7", "#fdcb6e",
            ]
            hood_color_map = {name: hood_colors[i % len(hood_colors)] for i, name in enumerate(sorted(df_map["neighborhood"].unique()))}

            # Build folium map centered on Cleveland
            m = folium.Map(location=[41.4993, -81.6944], zoom_start=12, tiles="CartoDB positron")

            for _, row in hood_summary.iterrows():
                color = hood_color_map.get(row["neighborhood"], "#003071")
                radius = max(15, min(35, row["count"] / 10))  # Scale circle size by property count

                # Circle marker — tooltip MUST match neighborhood name exactly for click detection
                folium.CircleMarker(
                    location=[row["lat"], row["lon"]],
                    radius=radius,
                    tooltip=row["neighborhood"],
                    color=color,
                    weight=2,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.5,
                ).add_to(m)

                # Text label on top of circle
                folium.Marker(
                    location=[row["lat"], row["lon"]],
                    icon=folium.DivIcon(
                        html=f'<div style="font-size:11px;font-weight:bold;color:#333;text-align:center;white-space:nowrap;text-shadow:1px 1px 2px white,-1px -1px 2px white,1px -1px 2px white,-1px 1px 2px white;">{row["neighborhood"]}</div>',
                        icon_size=(120, 20),
                        icon_anchor=(60, 10),
                    ),
                ).add_to(m)

            # Render map and capture click data
            map_data = st_folium(m, width=None, height=650, use_container_width=True)

            # Navigate to neighborhood profile when a circle is clicked
            if map_data and map_data.get("last_object_clicked_tooltip"):
                clicked_hood = map_data["last_object_clicked_tooltip"]
                if clicked_hood in df_map["neighborhood"].unique():
                    st.query_params["page"] = "maps"
                    st.query_params["hood"] = clicked_hood
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

    # -- Load data --
    @st.cache_data
    def load_property_data():
        return pd.read_csv("data/nst_sample_data.csv")

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
    st.markdown('<div class="breadcrumb"><a href="?page=home" target="_self">Home</a> &nbsp;/&nbsp; <strong>Property Search</strong></div>', unsafe_allow_html=True)
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
                st.markdown(f'<a href="?page=datasets" target="_self" style="color:#003071;text-decoration:none;font-weight:500;">{hood}</a> <span style="color:#999;font-size:0.85rem;">({count})</span>', unsafe_allow_html=True)

    # -- Footer --
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #666; padding: 2rem 0;">
            <p>Powered by CWRU Poverty Center | Last Updated: January 2026</p>
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
                    <a href="?page=datasets" target="_self" class="hero-button">Find Data</a>
                    <a href="#" class="hero-button">Popular Projects</a>
                    <a href="#" class="hero-button">Learn More</a>
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
            <a href="?page=maps" target="_self" class="data-card" style="text-decoration:none;">
                <div class="data-card-title">Map Explorer</div>
                <p style="color: #666; font-size: 1.1rem; margin-top: 1rem;">
                    Visualize neighborhood data on interactive maps
                </p>
            </a>
            <a href="?page=datasets" target="_self" class="data-card" style="text-decoration:none;">
                <div class="data-card-title">Browse Data</div>
                <p style="color: #666; font-size: 1.1rem; margin-top: 1rem;">
                    Explore comprehensive datasets and statistics
                </p>
            </a>
            <a href="?page=property-search" target="_self" class="data-card" style="text-decoration:none;">
                <div class="data-card-title">Search Properties</div>
                <p style="color: #666; font-size: 1.1rem; margin-top: 1rem;">
                    Find detailed information on specific properties
                </p>
            </a>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Partners section — replace placeholders with real logos
    st.markdown("""
        <div class="partners-section-title">OUR DATA PARTNERS</div>
        <div class="partners-grid">
            <div class="partner-logo">
                <p style="color: #999; font-size: 0.9rem;">Partner 1</p>
            </div>
            <div class="partner-logo">
                <p style="color: #999; font-size: 0.9rem;">Partner 2</p>
            </div>
            <div class="partner-logo">
                <p style="color: #999; font-size: 0.9rem;">Partner 3</p>
            </div>
            <div class="partner-logo">
                <p style="color: #999; font-size: 0.9rem;">Partner 4</p>
            </div>
            <div class="partner-logo">
                <p style="color: #999; font-size: 0.9rem;">Partner 5</p>
            </div>
            <div class="partner-logo">
                <p style="color: #999; font-size: 0.9rem;">Partner 6</p>
            </div>
            <div class="partner-logo">
                <p style="color: #999; font-size: 0.9rem;">Partner 7</p>
            </div>
            <div class="partner-logo">
                <p style="color: #999; font-size: 0.9rem;">Partner 8</p>
            </div>
            <div class="partner-logo">
                <p style="color: #999; font-size: 0.9rem;">Partner 9</p>
            </div>
            <div class="partner-logo">
                <p style="color: #999; font-size: 0.9rem;">Partner 10</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Contribute CTA
    st.markdown("""
        <div class="contribute-section">
            <div class="contribute-title">Want to share data through your organization?</div>
            <a href="#" class="contribute-button">TALK WITH US</a>
        </div>
    """, unsafe_allow_html=True)

    # -- Footer --
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #666; padding: 2rem 0;">
            <p>Powered by CWRU Poverty Center | Last Updated: January 2026</p>
        </div>
    """, unsafe_allow_html=True)
