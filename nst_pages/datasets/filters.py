"""All filter widgets and the if-chain that narrows the dataset based on them.

render_filters(df) returns (search_query, state_dict). State is kept in a dict so
page.py can pass it to summary.py and the tab renderers.

apply_filters(df, state) returns the filtered DataFrame (and the derived yr bounds
and sqft bound needed by the summary line).
"""

import streamlit as st

from utils.parcel import strip_suffix, normalize_parcel

from . import presets


_CLE_HEADER = "── Cleveland Neighborhoods ──"
_SUB_HEADER = "── Suburbs ──"


_VALUE_BRACKETS = {
    "Any value":          (0,        99_999_999),
    "Under $50,000":      (0,        50_000),
    "$50,000 - $100,000": (50_000,   100_000),
    "$100,000 - $200,000":(100_000,  200_000),
    "$200,000 - $350,000":(200_000,  350_000),
    "$350,000 - $500,000":(350_000,  500_000),
    "Over $500,000":      (500_000,  99_999_999),
}


def _sorted_opts(series):
    """'All' + distinct non-null string values from a column."""
    return ["All"] + sorted(
        series.dropna().astype(str).replace("nan", "")
        .pipe(lambda s: s[s != ""])
        .unique().tolist()
    )


def render_filters(df):
    """Draw the search box plus all filter widgets. Returns (search_query, state)."""
    search_query = st.text_input(
        "search",
        placeholder="Search by address, parcel ID, or owner name...",
        label_visibility="collapsed",
    )

    state = {}

    # Primary filter row: neighborhood, property type, year built
    sf1, sf2, sf3 = st.columns(3)
    with sf1:
        # Neighborhoods with >50% warded parcels are classified as Cleveland.
        hood_ward_pct = df[df["NEIGHBOR10"].fillna("").str.strip() != ""].groupby("NEIGHBOR10")["is_cleveland"].mean()
        cleveland_hoods = sorted(hood_ward_pct[hood_ward_pct > 0.5].index.tolist())
        suburb_hoods = sorted(hood_ward_pct[hood_ward_pct <= 0.5].index.tolist())
        neighborhood_opts = (
            ["Cleveland (City)", "All of Cuyahoga County", _CLE_HEADER]
            + cleveland_hoods
            + [_SUB_HEADER, "All Suburbs"]
            + suburb_hoods
        )
        f_neighborhood = st.selectbox("Neighborhood / Area", neighborhood_opts, index=0, key="f_nbh")
        if f_neighborhood == _CLE_HEADER:
            f_neighborhood = "Cleveland (City)"
        elif f_neighborhood == _SUB_HEADER:
            f_neighborhood = "All Suburbs"
        state["neighborhood"] = f_neighborhood
    with sf2:
        state["prop_type"] = st.selectbox("Property Type", _sorted_opts(df["CLASSIFICATION_DESCR"]), key="f_ptype")
    with sf3:
        yr_valid = df["yrbuilt"].dropna()
        yr_valid = yr_valid[(yr_valid > 0) & (yr_valid < 9999)]
        yr_min = int(yr_valid.min())
        yr_max = int(yr_valid.max())
        state["yr_min"] = yr_min
        state["yr_max"] = yr_max
        state["year_range"] = st.slider("Year Built", yr_min, yr_max, (yr_min, yr_max), key="f_yr")
        state["yr_include_unknown"] = st.checkbox(
            "Include properties with no year on record", value=True, key="f_yr_unk"
        )

    # Secondary filter row: value bracket, condition
    sf4, sf5 = st.columns(2)
    with sf4:
        state["val_label"] = st.selectbox("Property Value", list(_VALUE_BRACKETS.keys()), key="f_val")
        state["value_range"] = _VALUE_BRACKETS[state["val_label"]]
    with sf5:
        state["condition"] = st.selectbox("Condition", _sorted_opts(df["condition"]), key="f_cond")

    # Advanced filters: grouped expanders
    with st.expander("Advanced Filters"):
        _render_advanced(df, state)

    return search_query, state


def _render_advanced(df, state):
    """Nested expanders inside Advanced Filters. Mutates state dict."""
    with st.expander("Property Characteristics"):
        pc1, pc2, pc3, pc4 = st.columns(4)
        with pc1: state["style"]    = st.selectbox("Style", _sorted_opts(df["style"]), key="adv_style")
        with pc2: state["stories"]  = st.selectbox("# Stories", _sorted_opts(df["numstory"]), key="adv_stories")
        with pc3: state["zone"]     = st.selectbox("Zoning", _sorted_opts(df["zone_desc"]), key="adv_zone")
        with pc4: state["pclass"]   = st.selectbox("Property Class", _sorted_opts(df["pclass"]), key="adv_pclass")
        pc5, pc6, pc7 = st.columns(3)
        with pc5: state["bed"]  = st.selectbox("Bedrooms", _sorted_opts(df["bedrooms"]), key="adv_bed")
        with pc6: state["bath"] = st.selectbox("Bathrooms", _sorted_opts(df["baths"]), key="adv_bath")
        with pc7:
            sqft_max = int(df["basesqft"].dropna().max()) if df["basesqft"].dropna().any() else 10000
            state["sqft_max"] = sqft_max
            state["sqft"] = st.slider("Building Sq Ft", 0, sqft_max, (0, sqft_max), key="adv_sqft")

    with st.expander("Values & Taxes"):
        vt1, vt2, vt3, vt4 = st.columns(4)
        with vt1: state["homestead"]    = st.checkbox("Homestead exemption", key="adv_home")
        with vt2: state["payment_plan"] = st.checkbox("On payment plan", key="adv_pp")
        with vt3: state["cert_pend"]    = st.checkbox("Tax cert. pending", key="adv_cp")
        with vt4: state["cert_sold"]    = st.checkbox("Tax cert. sold", key="adv_cs")
        vt5, _ = st.columns(2)
        with vt5:
            state["taxabate"] = st.selectbox("Tax Abatement Code", _sorted_opts(df["taxabate"]), key="adv_aba")
        state["bor"] = "All"

    with st.expander("Violations (CLE Only)"):
        vc1, vc2, vc3, vc4 = st.columns(4)
        with vc1: state["active_condemn"] = st.checkbox("Active condemnation", key="adv_ac")
        with vc2: state["bh_lead"]        = st.checkbox("B&H lead violation", key="adv_bh")
        with vc3: state["cdc_comp"]       = st.checkbox("CDC complaint", key="adv_cdc")
        with vc4: state["council_comp"]   = st.checkbox("Council complaint", key="adv_council")
        vc5, vc6 = st.columns(2)
        with vc5: state["vtype"] = st.selectbox("Violation Type", _sorted_opts(df["violation_vtype"]), key="adv_vtype")
        with vc6: state["vtask"] = st.selectbox("Violation Task Status", _sorted_opts(df["violation_task_status"]), key="adv_vtask")

    # Eviction columns are fully null in current dataset.
    state["evict_status"] = "All"
    state["evict_disp"]   = "All"
    state["evict_yr"]     = "All"
    state["evict_multi"]  = False

    with st.expander("Lead Safe Certifications"):
        ls1, ls2 = st.columns(2)
        with ls1: state["lsc"]          = st.selectbox("LSC Status", _sorted_opts(df["lsc_stat"]), key="adv_lsc")
        with ls2: state["lead_rollout"] = st.selectbox("Lead Rollout Quarter", _sorted_opts(df["lead_rollout"]), key="adv_lr")

    with st.expander("Foreclosure & Forfeiture"):
        ff1, ff2, ff3 = st.columns(3)
        with ff1: state["fo_status"]   = st.selectbox("Case Status", _sorted_opts(df["lstatus"]), key="adv_fos")
        with ff2: state["cdesig"]      = st.selectbox("Case Designation", _sorted_opts(df["cdesig"]), key="adv_cdesig")
        with ff3: state["has_fo_deed"] = st.checkbox("Has fiscal officer deed", key="adv_fod")

    with st.expander("Land Bank Status"):
        lb1, lb2, lb3 = st.columns(3)
        with lb1: state["city_lb"]     = st.checkbox("City Land Bank", key="adv_clb")
        with lb2: state["cclrc"]       = st.checkbox("CCLRC", key="adv_cclrc")
        with lb3: state["demo_status"] = st.selectbox("Demo Status", _sorted_opts(df["demo_status"]), key="adv_demo")
        lb4, lb5 = st.columns(2)
        with lb4: state["rehab_status"] = st.selectbox("Rehab Status", _sorted_opts(df["rehab_status"]), key="adv_rehab")
        with lb5: state["disp_status"]  = st.selectbox("Disposition Status", _sorted_opts(df["disp_status"]), key="adv_disp")

    with st.expander("Geographies"):
        geo1, geo2, geo3, geo4 = st.columns(4)
        with geo1: state["ward"]   = st.selectbox("Ward (2025)", _sorted_opts(df["ward2025"]), key="adv_ward")
        with geo2: state["zip"]    = st.selectbox("ZIP Code", _sorted_opts(df["zip"]), key="adv_zip")
        with geo3: state["region"] = st.selectbox("Cuyahoga Region", _sorted_opts(df["cuyregion"]), key="adv_reg")
        with geo4: state["cia"]    = st.selectbox("CIA Area", _sorted_opts(df["cia14_name"]), key="adv_cia")

    with st.expander("Rental & Housing Programs"):
        rh1, rh2, rh3, rh4 = st.columns(4)
        with rh1: state["rental"]       = st.checkbox("Rental registered", key="adv_rr")
        with rh2: state["sect8"]        = st.checkbox("Section 8", key="adv_s8")
        with rh3: state["hud"]          = st.checkbox("HUD", key="adv_hud")
        with rh4: state["out_of_state"] = st.checkbox("Out-of-state owner", key="adv_oos")


def apply_filters(df, search_query, state):
    """Narrow df by the search query and every filter in state."""
    df = presets.apply(df)

    if search_query:
        q = search_query.strip()
        q_stripped = strip_suffix(q)
        parcel_norm = normalize_parcel(q)
        parcel_col = df["PARCEL"].fillna("").astype(str)
        mask = (
            df["address"].fillna("").str.contains(q, case=False, regex=False)
            | df["address"].fillna("").str.contains(q_stripped, case=False, regex=False)
            | parcel_col.str.contains(q, case=False, regex=False)
            | (parcel_col.str.contains(parcel_norm, case=False, regex=False) if parcel_norm else False)
            | df["PRIMARY_OWNER_NAME"].fillna("").str.contains(q, case=False, regex=False)
        )
        df = df[mask]

    nbh = state["neighborhood"]
    if nbh == "Cleveland (City)":
        df = df[df["is_cleveland"]]
    elif nbh == "All of Cuyahoga County":
        pass
    elif nbh == "All Suburbs":
        df = df[~df["is_cleveland"]]
    else:
        df = df[df["NEIGHBOR10"].astype(str) == nbh]

    if state["prop_type"] != "All":
        df = df[df["CLASSIFICATION_DESCR"].astype(str) == state["prop_type"]]
    if state["condition"] != "All":
        df = df[df["condition"].astype(str) == state["condition"]]

    yr_full = (state["yr_min"], state["yr_max"])
    if state["year_range"] != yr_full or not state["yr_include_unknown"]:
        yr = df["yrbuilt"]
        in_range = (yr >= state["year_range"][0]) & (yr <= state["year_range"][1]) & (yr > 0) & (yr < 9999)
        unknown = yr.isna() | (yr <= 0) | (yr >= 9999)
        df = df[in_range | (unknown & state["yr_include_unknown"])]

    vrange = state["value_range"]
    df = df[
        (df["TAX_MARKET_TOTAL"].fillna(0) >= vrange[0]) &
        (df["TAX_MARKET_TOTAL"].fillna(0) <= vrange[1])
    ]

    for key, col in [("style","style"), ("stories","numstory"), ("zone","zone_desc"),
                     ("pclass","pclass"), ("bed","bedrooms"), ("bath","baths")]:
        if state[key] != "All":
            df = df[df[col].astype(str) == state[key]]

    df = df[
        (df["basesqft"].fillna(0) >= state["sqft"][0]) &
        (df["basesqft"].fillna(0) <= state["sqft"][1])
    ]

    if state["homestead"]:      df = df[df["HOMESTEAD_FLAG"].fillna(0) == 1]
    if state["payment_plan"]:   df = df[df["PAYMENT_PLAN_FLAG"].fillna(0) == 1]
    if state["cert_pend"]:      df = df[df["CERT_PEND_FLAG"].fillna(0) == 1]
    if state["cert_sold"]:      df = df[df["CERT_SOLD_FLAG"].fillna(0) == 1]
    if state["taxabate"] != "All":
        df = df[df["taxabate"].astype(str) == state["taxabate"]]
    if state["bor"] != "All":
        df = df[df["BOR_STATUS"].astype(str) == state["bor"]]

    if state["active_condemn"]: df = df[df["active_condemn"].fillna(0) == 1]
    if state["bh_lead"]:        df = df[df["cod_current_bh_lead_violations"].fillna(0) == 1]
    if state["cdc_comp"]:       df = df[df["cdc_comp"].fillna(0) == 1]
    if state["council_comp"]:   df = df[df["council_comp"].fillna(0) == 1]
    if state["vtype"] != "All": df = df[df["violation_vtype"].astype(str) == state["vtype"]]
    if state["vtask"] != "All": df = df[df["violation_task_status"].astype(str) == state["vtask"]]

    if state["evict_status"] != "All":
        df = df[df["evict_case_status"].astype(str) == state["evict_status"]]
    if state["evict_disp"] != "All":
        df = df[df["evict_disp_status"].astype(str) == state["evict_disp"]]
    if state["evict_yr"] != "All":
        df = df[df["evict_yr"].astype(str) == state["evict_yr"]]
    if state["evict_multi"]:
        df = df[df["evict_case_number"].fillna("").astype(str).str.contains(",", regex=False)]

    if state["lsc"] != "All":
        df = df[df["lsc_stat"].astype(str) == state["lsc"]]
    if state["lead_rollout"] != "All":
        df = df[df["lead_rollout"].astype(str) == state["lead_rollout"]]

    if state["fo_status"] != "All":
        df = df[df["lstatus"].astype(str) == state["fo_status"]]
    if state["cdesig"] != "All":
        df = df[df["cdesig"].astype(str) == state["cdesig"]]
    if state["has_fo_deed"]:
        df = df[df["fo_deed_count"].fillna(0) > 0]

    if state["city_lb"]: df = df[df["city_lb_flag"].fillna(0) == 1]
    if state["cclrc"]:   df = df[df["cclrc"].fillna(0) == 1]
    if state["demo_status"] != "All":
        df = df[df["demo_status"].astype(str) == state["demo_status"]]
    if state["rehab_status"] != "All":
        df = df[df["rehab_status"].astype(str) == state["rehab_status"]]
    if state["disp_status"] != "All":
        df = df[df["disp_status"].astype(str) == state["disp_status"]]

    if state["ward"]   != "All": df = df[df["ward2025"].astype(str)   == state["ward"]]
    if state["zip"]    != "All": df = df[df["zip"].astype(str)        == state["zip"]]
    if state["region"] != "All": df = df[df["cuyregion"].astype(str)  == state["region"]]
    if state["cia"]    != "All": df = df[df["cia14_name"].astype(str) == state["cia"]]

    if state["rental"]:       df = df[df["rentalreg"].fillna(0) == 1]
    if state["sect8"]:        df = df[df["sect8"].fillna(0) == 1]
    if state["hud"]:          df = df[df["hud"].fillna(0) == 1]
    if state["out_of_state"]: df = df[~df["MAIL_STATE"].fillna("").isin(["OH", "/", ""])]

    return df


def sort_by_completeness(df):
    """Sort improved residential first, scoring by data completeness."""
    addr_s = df["address"].fillna("")
    return df.assign(
        _sort_score=(
            # Starts with a digit AND is not all zeros (excludes "00000" placeholders)
            (addr_s.str.match(r"^\d") & ~addr_s.str.match(r"^0+$")).astype(int)
            + df["condition"].notna().astype(int)
            + df["yrbuilt"].fillna(0).gt(0).astype(int)
        )
    ).sort_values(
        by=["_sort_score", "address"],
        ascending=[False, True],
        na_position="last",
    ).drop(columns=["_sort_score"]).reset_index(drop=True)
