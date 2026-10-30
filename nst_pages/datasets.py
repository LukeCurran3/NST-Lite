"""Datasets page: browse, filter, and export property data."""

import io
import json
import zipfile

import pandas as pd
import streamlit as st

from config import COL_GROUPS, PRESET_COLUMNS, COLUMN_LABELS
from loaders import load_data


def render():
    df = load_data()

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

    st.markdown('<div class="breadcrumb"><a href="?auth=1&page=home" target="_self">Home</a> &nbsp;/&nbsp; <strong>Datasets</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Datasets</div><div class="page-subtitle">Browse and download comprehensive property data for Cleveland and Cuyahoga County.</div>', unsafe_allow_html=True)

    if "ds_presets" not in st.session_state:
        st.session_state.ds_presets = set()

    st.markdown('<div class="preset-section">', unsafe_allow_html=True)
    pr1, pr2, pr3, pr4, pr5, pr6 = st.columns(6)
    preset_map = {
        "Vacant Properties": pr1,
        "With Violations": pr2,
        "Tax Delinquent": pr3,
        "Out-of-State Owners": pr4,
        "In Foreclosure": pr5,
        "Failed Lead Cert": pr6,
    }
    for p_label, p_col in preset_map.items():
        with p_col:
            is_active = p_label in st.session_state.ds_presets
            btn_label = f"✓ {p_label}" if is_active else p_label
            if st.button(btn_label, use_container_width=True, key=f"preset_{p_label}"):
                if is_active:
                    st.session_state.ds_presets.discard(p_label)
                else:
                    st.session_state.ds_presets.add(p_label)
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    search_query = st.text_input(
        "search",
        placeholder="Search by address, parcel ID, or owner name...",
        label_visibility="collapsed",
    )

    sf1, sf2, sf3 = st.columns(3)
    with sf1:
        # Neighborhoods with >50% warded parcels are classified as Cleveland.
        hood_ward_pct = df[df["NEIGHBOR10"].fillna("").str.strip() != ""].groupby("NEIGHBOR10")["is_cleveland"].mean()
        cleveland_hoods = sorted(hood_ward_pct[hood_ward_pct > 0.5].index.tolist())
        suburb_hoods = sorted(hood_ward_pct[hood_ward_pct <= 0.5].index.tolist())
        neighborhood_opts = (
            ["Cleveland (City)", "All of Cuyahoga County"]
            + cleveland_hoods
            + suburb_hoods
        )
        f_neighborhood = st.selectbox("Neighborhood / Area", neighborhood_opts, index=0, key="f_nbh")
    with sf2:
        prop_types = ["All"] + sorted(df["CLASSIFICATION_DESCR"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
        f_prop_type = st.selectbox("Property Type", prop_types, key="f_ptype")
    with sf3:
        yr_valid = df["yrbuilt"].dropna()
        yr_valid = yr_valid[(yr_valid > 0) & (yr_valid < 9999)]
        yr_min_data = int(yr_valid.min())
        yr_max_data = int(yr_valid.max())
        f_year_range = st.slider("Year Built", yr_min_data, yr_max_data, (yr_min_data, yr_max_data), key="f_yr")

    sf4, sf5 = st.columns(2)
    with sf4:
        _val_brackets = {
            "Any value":          (0,        99_999_999),
            "Under $50,000":      (0,        50_000),
            "$50,000 - $100,000": (50_000,   100_000),
            "$100,000 - $200,000":(100_000,  200_000),
            "$200,000 - $350,000":(200_000,  350_000),
            "$350,000 - $500,000":(350_000,  500_000),
            "Over $500,000":      (500_000,  99_999_999),
        }
        f_val_label = st.selectbox("Property Value", list(_val_brackets.keys()), key="f_val")
        f_value_range = _val_brackets[f_val_label]
    with sf5:
        conditions = ["All"] + sorted(df["condition"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
        f_condition = st.selectbox("Condition", conditions, key="f_cond")

    tg1, tg2, tg3, tg4 = st.columns(4)
    with tg1: f_vacant = st.checkbox("Vacant only", key="f_vac")
    with tg2: f_violations = st.checkbox("Has violations", key="f_viol")
    with tg3: f_tax_del = st.checkbox("Tax delinquent", key="f_tax")
    with tg4: f_foreclosure_flag = st.checkbox("In foreclosure", key="f_fore")

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
            vt5, _ = st.columns(2)
            with vt5:
                tax_abate_vals = ["All"] + sorted(df["taxabate"].dropna().astype(str).replace("nan","").pipe(lambda s: s[s != ""]).unique().tolist())
                f_taxabate = st.selectbox("Tax Abatement Code", tax_abate_vals, key="adv_aba")
            f_bor = "All"

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

        # Eviction columns are fully null in current dataset.
        f_evict_status = "All"
        f_evict_disp = "All"
        f_evict_yr = "All"
        f_evict_multi = False

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

    filtered_df = df.copy()

    active_presets = st.session_state.ds_presets
    if "Vacant Properties" in active_presets:
        filtered_df = filtered_df[filtered_df["combovac"].fillna(0) == 1]
    if "With Violations" in active_presets:
        filtered_df = filtered_df[filtered_df["violation"].fillna(0) == 1]
    if "Tax Delinquent" in active_presets:
        filtered_df = filtered_df[filtered_df["NET_TAX_DELQ_DUE"].fillna(0) > 0]
    if "Out-of-State Owners" in active_presets:
        filtered_df = filtered_df[~filtered_df["MAIL_STATE"].fillna("").isin(["OH", "/", ""])]
    if "In Foreclosure" in active_presets:
        filtered_df = filtered_df[filtered_df["FORECLOSURE_FLAG"].fillna(0) == 1]
    if "Failed Lead Cert" in active_presets:
        filtered_df = filtered_df[filtered_df["lsc_stat"].fillna("").astype(str).isin(["FAIL", "REVOKED"])]

    if search_query:
        q = search_query.strip()
        mask = (
            filtered_df["address"].fillna("").str.contains(q, case=False, regex=False)
            | filtered_df["PARCEL"].fillna("").astype(str).str.contains(q, case=False, regex=False)
            | filtered_df["PRIMARY_OWNER_NAME"].fillna("").str.contains(q, case=False, regex=False)
        )
        filtered_df = filtered_df[mask]

    if f_neighborhood == "Cleveland (City)":
        filtered_df = filtered_df[filtered_df["is_cleveland"]]
    elif f_neighborhood == "All of Cuyahoga County":
        pass
    else:
        filtered_df = filtered_df[filtered_df["NEIGHBOR10"].astype(str) == f_neighborhood]
    if f_prop_type != "All":
        filtered_df = filtered_df[filtered_df["CLASSIFICATION_DESCR"].astype(str) == f_prop_type]
    if f_condition != "All":
        filtered_df = filtered_df[filtered_df["condition"].astype(str) == f_condition]
    if f_year_range != (yr_min_data, yr_max_data):
        filtered_df = filtered_df[
            (filtered_df["yrbuilt"] >= f_year_range[0]) &
            (filtered_df["yrbuilt"] <= f_year_range[1]) &
            (filtered_df["yrbuilt"] > 0) &
            (filtered_df["yrbuilt"] < 9999)
        ]
    filtered_df = filtered_df[
        (filtered_df["TAX_MARKET_TOTAL"].fillna(0) >= f_value_range[0]) &
        (filtered_df["TAX_MARKET_TOTAL"].fillna(0) <= f_value_range[1])
    ]

    if f_vacant:
        filtered_df = filtered_df[filtered_df["combovac"].fillna(0) == 1]
    if f_violations:
        filtered_df = filtered_df[filtered_df["violation"].fillna(0) == 1]
    if f_tax_del:
        filtered_df = filtered_df[filtered_df["NET_TAX_DELQ_DUE"].fillna(0) > 0]
    if f_foreclosure_flag:
        filtered_df = filtered_df[filtered_df["FORECLOSURE_FLAG"].fillna(0) == 1]

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

    if f_active_condemn:
        filtered_df = filtered_df[filtered_df["active_condemn"].fillna(0) == 1]
    if f_bh_lead:
        filtered_df = filtered_df[filtered_df["cod_current_bh_lead_violations"].fillna(0) == 1]
    if f_cdc_comp:
        filtered_df = filtered_df[filtered_df["cdc_comp"].fillna(0) == 1]
    if f_council_comp:
        filtered_df = filtered_df[filtered_df["council_comp"].fillna(0) == 1]
    if f_vtype != "All":
        filtered_df = filtered_df[filtered_df["violation_vtype"].astype(str) == f_vtype]
    if f_vtask != "All":
        filtered_df = filtered_df[filtered_df["violation_task_status"].astype(str) == f_vtask]

    if f_evict_status != "All":
        filtered_df = filtered_df[filtered_df["evict_case_status"].astype(str) == f_evict_status]
    if f_evict_disp != "All":
        filtered_df = filtered_df[filtered_df["evict_disp_status"].astype(str) == f_evict_disp]
    if f_evict_yr != "All":
        filtered_df = filtered_df[filtered_df["evict_yr"].astype(str) == f_evict_yr]
    if f_evict_multi:
        filtered_df = filtered_df[filtered_df["evict_case_number"].fillna("").astype(str).str.contains(",", regex=False)]

    if f_lsc != "All":
        filtered_df = filtered_df[filtered_df["lsc_stat"].astype(str) == f_lsc]
    if f_lead_rollout != "All":
        filtered_df = filtered_df[filtered_df["lead_rollout"].astype(str) == f_lead_rollout]

    if f_fo_status != "All":
        filtered_df = filtered_df[filtered_df["lstatus"].astype(str) == f_fo_status]
    if f_cdesig != "All":
        filtered_df = filtered_df[filtered_df["cdesig"].astype(str) == f_cdesig]
    if f_has_fo_deed:
        filtered_df = filtered_df[filtered_df["fo_deed_count"].fillna(0) > 0]

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

    if f_ward != "All":
        filtered_df = filtered_df[filtered_df["ward2025"].astype(str) == f_ward]
    if f_zip != "All":
        filtered_df = filtered_df[filtered_df["zip"].astype(str) == f_zip]
    if f_region != "All":
        filtered_df = filtered_df[filtered_df["cuyregion"].astype(str) == f_region]
    if f_cia != "All":
        filtered_df = filtered_df[filtered_df["cia14_name"].astype(str) == f_cia]

    if f_rental:
        filtered_df = filtered_df[filtered_df["rentalreg"].fillna(0) == 1]
    if f_sect8:
        filtered_df = filtered_df[filtered_df["sect8"].fillna(0) == 1]
    if f_hud:
        filtered_df = filtered_df[filtered_df["hud"].fillna(0) == 1]
    if f_out_of_state:
        filtered_df = filtered_df[~filtered_df["MAIL_STATE"].fillna("").isin(["OH", "/", ""])]

    # Sort improved residential properties first by scoring data completeness.
    _addr_s = filtered_df["address"].fillna("")
    filtered_df = filtered_df.assign(
        _sort_score=(
            # Starts with a digit AND is not all zeros (excludes "00000" placeholders)
            (_addr_s.str.match(r"^\d") & ~_addr_s.str.match(r"^0+$")).astype(int)
            + filtered_df["condition"].notna().astype(int)
            + filtered_df["yrbuilt"].fillna(0).gt(0).astype(int)
        )
    ).sort_values(
        by=["_sort_score", "address"],
        ascending=[False, True],
        na_position="last",
    ).drop(columns=["_sort_score"]).reset_index(drop=True)

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

    with st.expander("Customize Columns"):
        preset_sel = st.radio(
            "Column preset",
            list(PRESET_COLUMNS.keys()) + ["Custom"],
            horizontal=True,
            key="col_preset",
        )
        if preset_sel != "Custom":
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

    tab_table, tab_map, tab_charts, tab_summary = st.tabs(["Table View", "Map View", "Charts", "Summary"])

    with tab_table:
        if total > 0:
            valid_display = [c for c in display_columns if c in filtered_df.columns]
            _CURRENCY_COLS = {
                "TAX_MARKET_TOTAL", "TAX_MARKET_LAND", "TAX_MARKET_IMPROVEMENT",
                "currentvalue2023", "proposedvalue2024", "NET_TAX_DELQ_DUE",
                "lsaleamt", "assessment",
            }
            _FLAG_DISPLAY_COLS = {
                'FORECLOSURE_FLAG', 'HOMESTEAD_FLAG', 'PAYMENT_PLAN_FLAG',
                'CERT_PEND_FLAG', 'CERT_SOLD_FLAG', 'city_lb_flag',
                'violation', 'active_condemn', 'combovac', 'vl', 'lbvl', 'unoccupied',
                'cdc_comp', 'council_comp', 'mayor_comp', 'mac_comp',
                'public_comp', 'other_comp', 'anycomplaint',
                'cod_current_bh_lead_violations', 'rentalreg', 'sect8', 'sect8_cnty', 'hud',
            }
            display_df = filtered_df[valid_display].copy()
            for c in valid_display:
                if c in _CURRENCY_COLS:
                    display_df[c] = display_df[c].apply(
                        lambda x: f"${x:,.0f}" if pd.notna(x) and isinstance(x, (int, float)) else ""
                    )
                elif c in _FLAG_DISPLAY_COLS:
                    display_df[c] = display_df[c].map(
                        lambda x: "Yes" if x == 1 else ("No" if x == 0 else "")
                    )
            st.dataframe(
                display_df.rename(columns=COLUMN_LABELS).reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
                height=520,
            )
        else:
            st.info("No properties match your filters.")

    with tab_map:
        _CHOROPLETH_THRESHOLD = 3000
        if total == 0:
            st.info("No properties to display. Adjust your filters.")
        else:
            import folium
            from streamlit_folium import st_folium
            import geopandas as gpd

            @st.cache_data
            def _load_hoods():
                gdf = gpd.read_file("data/cuy_nei20_NAD83.shp").to_crs(epsg=4326)
                _NAME_FIX = {
                    "KAMM'S": "KAMMS",
                    "CHAGRIN FALLS": "CHAGRIN FALLS TOWNSHIP",
                    "MAYFIELD": "MAYFIELD VILLAGE",
                    "OLMSTED": "OLMSTED TOWNSHIP",
                }
                gdf["name_key"] = (
                    gdf["NEIGHBOR20"].str.upper().str.strip()
                    .map(lambda x: _NAME_FIX.get(x, x))
                )
                return gdf

            gdf_hoods = _load_hoods()

            if total > _CHOROPLETH_THRESHOLD:
                metric_label = st.selectbox(
                    "Color neighborhoods by",
                    ["Property Count", "Vacancy Rate %", "Violation Rate %", "Avg Market Value"],
                    key="map_metric",
                )
                agg = filtered_df.groupby("NEIGHBOR10").agg(
                    count=("PARCEL", "count"),
                    vacant=("combovac", lambda x: (x.fillna(0) == 1).sum()),
                    violation=("violation", lambda x: (x.fillna(0) == 1).sum()),
                    avg_value=("TAX_MARKET_TOTAL", "mean"),
                ).reset_index()
                agg["vacancy_pct"] = (agg["vacant"] / agg["count"] * 100).round(1)
                agg["violation_pct"] = (agg["violation"] / agg["count"] * 100).round(1)
                agg["avg_value"] = agg["avg_value"].fillna(0).round(0)

                _METRIC_MAP = {
                    "Property Count":   ("count",         "YlOrRd"),
                    "Vacancy Rate %":   ("vacancy_pct",   "YlOrRd"),
                    "Violation Rate %": ("violation_pct", "YlOrRd"),
                    "Avg Market Value": ("avg_value",     "YlGn"),
                }
                col_key, color_scale = _METRIC_MAP[metric_label]

                gdf_plot = gdf_hoods.merge(
                    agg[["NEIGHBOR10", "count", "vacancy_pct", "violation_pct", "avg_value"]],
                    left_on="name_key", right_on="NEIGHBOR10", how="left",
                )
                gdf_plot["count"]         = gdf_plot["count"].fillna(0).astype(int)
                gdf_plot["vacancy_pct"]   = gdf_plot["vacancy_pct"].fillna(0.0)
                gdf_plot["violation_pct"] = gdf_plot["violation_pct"].fillna(0.0)
                gdf_plot["avg_value"]     = gdf_plot["avg_value"].fillna(0.0)
                gdf_plot["_count_fmt"] = gdf_plot["count"].apply(lambda x: f"{x:,}")
                gdf_plot["_val_fmt"]   = gdf_plot["avg_value"].apply(
                    lambda x: f"${int(x):,}" if x > 0 else "N/A"
                )
                gdf_plot["_vac_fmt"]  = gdf_plot["vacancy_pct"].apply(lambda x: f"{x:.1f}%")
                gdf_plot["_viol_fmt"] = gdf_plot["violation_pct"].apply(lambda x: f"{x:.1f}%")

                m = folium.Map(location=[41.48, -81.68], zoom_start=11, tiles="OpenStreetMap")

                choro = folium.Choropleth(
                    geo_data=gdf_plot.__geo_interface__,
                    data=gdf_plot[["name_key", col_key]],
                    columns=["name_key", col_key],
                    key_on="feature.properties.name_key",
                    fill_color=color_scale,
                    fill_opacity=0.65,
                    line_opacity=0.4,
                    line_color="#666",
                    legend_name=metric_label,
                    nan_fill_color="#f0f0f0",
                )
                choro.add_to(m)
                choro.geojson.add_child(
                    folium.features.GeoJsonTooltip(
                        fields=["name_key", "_count_fmt", "_vac_fmt", "_viol_fmt", "_val_fmt"],
                        aliases=["Area", "Properties", "Vacancy Rate", "Violation Rate", "Avg Market Value"],
                        style="font-family:Arial,sans-serif;font-size:12px;",
                    )
                )

                st.caption(
                    f"Choropleth: {total:,} filtered properties  ·  "
                    f"Narrow to ≤ {_CHOROPLETH_THRESHOLD:,} to see individual property dots"
                )
                st_folium(m, width=None, height=520, use_container_width=True, returned_objects=[])

            else:
                from folium.plugins import MarkerCluster

                color_by = st.selectbox(
                    "Color dots by",
                    ["Vacant (structure or land)", "In Foreclosure", "Has Violation"],
                    key="map_color",
                )
                # Vacant composite: combovac==1 OR classification starts with Vacant Land.
                _COLOR_COL = {
                    "In Foreclosure": "FORECLOSURE_FLAG",
                    "Has Violation":  "violation",
                }
                color_col = _COLOR_COL.get(color_by, "combovac")

                _map_cols = list(dict.fromkeys([
                    "LATITUDE", "LONGITUDE", "PARCEL", "address", "NEIGHBOR10",
                    "CLASSIFICATION_DESCR", "yrbuilt", "condition", "PRIMARY_OWNER_NAME",
                    "TAX_MARKET_TOTAL", "NET_TAX_DELQ_DUE",
                    "combovac", "FORECLOSURE_FLAG", "violation",
                    color_col,
                ]))
                map_df = (
                    filtered_df[[c for c in _map_cols if c in filtered_df.columns]]
                    .dropna(subset=["LATITUDE", "LONGITUDE"])
                    .copy()
                )

                if map_df.empty:
                    st.info("No properties with coordinates to display.")
                else:
                    center_lat = map_df["LATITUDE"].mean()
                    center_lng = map_df["LONGITUDE"].mean()
                    zoom = 14 if total < 300 else 13

                    m = folium.Map(
                        location=[center_lat, center_lng],
                        zoom_start=zoom,
                        tiles="OpenStreetMap",
                    )

                    folium.GeoJson(
                        gdf_hoods.__geo_interface__,
                        style_function=lambda x: {
                            "fillColor": "transparent",
                            "color": "#aaaaaa",
                            "weight": 1,
                            "fillOpacity": 0,
                        },
                    ).add_to(m)

                    mc = MarkerCluster(
                        options={"maxClusterRadius": 40, "disableClusteringAtZoom": 17}
                    ).add_to(m)

                    def _flag_yn(v):
                        try:
                            return "Yes" if int(float(v)) == 1 else "No"
                        except (TypeError, ValueError):
                            return "No"

                    def _fmt_money(v):
                        try:
                            return f"${int(float(v)):,}" if pd.notna(v) and float(v) > 0 else "N/A"
                        except (TypeError, ValueError):
                            return "N/A"

                    def _fmt_text(v, default="-"):
                        if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() in ("", "nan"):
                            return default
                        return str(v).strip()

                    def _fmt_year(v):
                        try:
                            y = int(float(v))
                            return str(y) if 1700 < y < 9999 else "-"
                        except (TypeError, ValueError):
                            return "-"

                    _is_vacant_mode = color_by.startswith("Vacant")
                    for _, row in map_df.iterrows():
                        if _is_vacant_mode:
                            _cv = row.get("combovac")
                            _vs = int(float(_cv)) == 1 if pd.notna(_cv) else False
                            _cd = str(row.get("CLASSIFICATION_DESCR") or "")
                            _vl = _cd.startswith("Vacant Land")
                            is_flagged = _vs or _vl
                        else:
                            is_flagged = int(row.get(color_col, 0) or 0) == 1
                        color = "#e03127" if is_flagged else "#003071"
                        parcel_id = _fmt_text(row.get("PARCEL"), "")
                        address   = _fmt_text(row.get("address"), "Unknown Address")
                        hood      = _fmt_text(row.get("NEIGHBOR10"), "")
                        val_str   = _fmt_money(row.get("TAX_MARKET_TOTAL"))
                        delq      = row.get("NET_TAX_DELQ_DUE")
                        delq_str  = _fmt_money(delq) if pd.notna(delq) and (delq or 0) > 0 else "None"
                        flag_tip  = (
                            f'<span style="color:#e03127">&#9888; {color_by}</span>'
                            if is_flagged else f"Not {color_by}"
                        )

                        tip = (
                            f"<b>{address}</b><br>"
                            f"{hood}<br>"
                            f"Market Value: {val_str}<br>"
                            f"{flag_tip}"
                        )

                        # window.open bypasses st_folium's rerun loop which reverts same-tab nav.
                        _parcel_js = parcel_id.replace("'", "\\'")
                        profile_js = (
                            "var t=window.top;"
                            f"window.open(t.location.origin+t.location.pathname+"
                            f"'?auth=1&page=property-search&parcel={_parcel_js}','_blank');"
                            "return false;"
                        )
                        popup_html = f"""
                            <div style="font-family:Arial,sans-serif;font-size:12px;min-width:240px;max-width:280px;">
                                <div style="font-size:13px;font-weight:700;color:#003071;margin-bottom:2px;">{address}</div>
                                <div style="color:#666;margin-bottom:8px;">{hood} &nbsp;·&nbsp; {parcel_id}</div>
                                <table style="width:100%;border-collapse:collapse;">
                                    <tr><td style="color:#666;padding:2px 0;">Property Type</td><td style="text-align:right;font-weight:600;">{_fmt_text(row.get('CLASSIFICATION_DESCR'))}</td></tr>
                                    <tr><td style="color:#666;padding:2px 0;">Year Built</td><td style="text-align:right;font-weight:600;">{_fmt_year(row.get('yrbuilt'))}</td></tr>
                                    <tr><td style="color:#666;padding:2px 0;">Condition</td><td style="text-align:right;font-weight:600;">{_fmt_text(row.get('condition'))}</td></tr>
                                    <tr><td style="color:#666;padding:2px 0;">Owner</td><td style="text-align:right;font-weight:600;">{_fmt_text(row.get('PRIMARY_OWNER_NAME'))}</td></tr>
                                    <tr><td style="color:#666;padding:2px 0;">Market Value</td><td style="text-align:right;font-weight:600;">{val_str}</td></tr>
                                    <tr><td style="color:#666;padding:2px 0;">Tax Delinquent</td><td style="text-align:right;font-weight:600;color:{'#c0392b' if delq_str != 'None' else '#27ae60'};">{delq_str}</td></tr>
                                    <tr><td style="color:#666;padding:2px 0;">Vacant</td><td style="text-align:right;font-weight:600;">{_flag_yn(row.get('combovac'))}</td></tr>
                                    <tr><td style="color:#666;padding:2px 0;">In Foreclosure</td><td style="text-align:right;font-weight:600;">{_flag_yn(row.get('FORECLOSURE_FLAG'))}</td></tr>
                                    <tr><td style="color:#666;padding:2px 0;">Has Violation</td><td style="text-align:right;font-weight:600;">{_flag_yn(row.get('violation'))}</td></tr>
                                </table>
                                <div style="margin-top:10px;text-align:center;">
                                    <a href="#" onclick="{profile_js}"
                                       style="display:inline-block;background:#003071;color:white;padding:6px 14px;
                                              border-radius:4px;text-decoration:none;font-weight:600;font-size:12px;cursor:pointer;">
                                        View Full Profile &nbsp;&#8599;
                                    </a>
                                </div>
                            </div>
                        """

                        folium.CircleMarker(
                            location=[row["LATITUDE"], row["LONGITUDE"]],
                            radius=5, color=None, fill=True,
                            fill_color=color, fill_opacity=0.75,
                            tooltip=folium.Tooltip(tip),
                            popup=folium.Popup(popup_html, max_width=320),
                        ).add_to(mc)

                    legend_html = f"""
                    <div style="position:fixed;bottom:30px;right:30px;z-index:9999;background:white;
                         padding:10px 14px;border-radius:8px;border:1px solid #ddd;font-size:12px;
                         font-family:Arial,sans-serif;box-shadow:0 2px 8px rgba(0,0,0,0.12);">
                        <div style="font-weight:700;margin-bottom:6px;color:#003071;">{color_by}</div>
                        <div><span style="display:inline-block;width:11px;height:11px;border-radius:50%;
                             background:#e03127;margin-right:7px;vertical-align:middle;"></span>Yes</div>
                        <div style="margin-top:4px"><span style="display:inline-block;width:11px;height:11px;
                             border-radius:50%;background:#003071;margin-right:7px;vertical-align:middle;"></span>No</div>
                    </div>
                    """
                    m.get_root().html.add_child(folium.Element(legend_html))

                    st.caption(
                        f"Showing {len(map_df):,} properties  ·  "
                        f"Red = {color_by}  ·  Navy = Not {color_by}  ·  "
                        f"Zoom in to expand clusters"
                    )
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
        else:
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

    st.markdown("---")
    st.markdown('<div style="text-align: center; color: #666; padding: 2rem 0;"><p>Powered by CWRU Poverty Center | Last Updated: March 2026</p></div>', unsafe_allow_html=True)
