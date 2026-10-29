"""Distressed Rentals project page."""

import pandas as pd
import streamlit as st

from config import DR_START, DR_END
from loaders import load_distressed_rentals


def render():
    st.markdown(
        '<div style="font-size:0.95rem;color:#666;margin-bottom:1.5rem;">'
        '<a href="?auth=1&page=home" target="_self" style="color:#003071;text-decoration:none;">Home</a>'
        ' &nbsp;/&nbsp; <strong>Distressed Rentals</strong></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div style="font-size:2.5rem;font-weight:700;color:#003071;margin-bottom:0.3rem;">Distressed Rentals</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:1.1rem;color:#666;margin-bottom:1.5rem;">'
        'Rental properties flagged with signs of distress or extractive ownership. '
        'Based on the <a href="?auth=1&page=home" style="color:#003071;">Center on Poverty &amp; Community Development</a> methodology: '
        'rental universe, five distress indicators (tax delinquency, violations, complaints, grade decline, evictions), '
        'and owner classification.'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.spinner("Loading rental universe and computing distress indicators…"):
        dr = load_distressed_rentals()

    if dr.empty:
        st.error("No rental properties found. Check that the parquet data is present.")
        st.stop()

    with st.expander("Filters", expanded=True):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            hoods = ["All"] + sorted(dr["NEIGHBOR10"].dropna().unique().tolist())
            f_hood = st.selectbox("Neighborhood", hoods, key="dr_hood")
        with fc2:
            owner_types = ["All"] + sorted(dr["owner_type"].dropna().unique().tolist())
            f_owner = st.selectbox("Owner type", owner_types, key="dr_owner")
        with fc3:
            f_min_distress = st.selectbox(
                "Minimum distress indicators",
                [0, 1, 2, 3, 4, 5],
                index=0, key="dr_min_distress",
            )
        fc4, fc5 = st.columns(2)
        with fc4:
            f_investor = st.checkbox("Investor-owned only (Corporate / Trust)", key="dr_inv")
        with fc5:
            f_vacant = st.checkbox("Vacant structures only", key="dr_vac")

    with st.expander("Advanced Filters: specific distress indicators", expanded=False):
        st.caption(
            "Narrow the results to properties that match specific distress indicators. "
            "Match mode controls whether all checked indicators are required, or any one is enough."
        )
        f_match_mode = st.radio(
            "Match mode",
            ["ANY of the checked indicators", "ALL of the checked indicators"],
            key="dr_match_mode", horizontal=True,
        )
        ac1, ac2, ac3, ac4, ac5 = st.columns(5)
        with ac1:
            f_ind_delq = st.checkbox("Tax delinquent ≥ $500", key="dr_ind_delq")
        with ac2:
            f_ind_viol = st.checkbox("Violation (last 5 yrs)", key="dr_ind_viol")
        with ac3:
            f_ind_comp = st.checkbox("Complaint (last 5 yrs)", key="dr_ind_comp")
        with ac4:
            f_ind_decl = st.checkbox("Grade declined 2015 → 2023", key="dr_ind_decl")
        with ac5:
            f_ind_evic = st.checkbox("Has evictions 2021-2025", key="dr_ind_evic")

    with st.expander("Portfolio Filters: group parcels by tax mailing address", expanded=False):
        st.caption(
            "Portfolios are inferred by grouping parcels that share the same tax mailing address. "
            "This exposes landlords who hide portfolio size by using multiple LLCs: all mailed to one P.O. box. "
            "Mail-drop addresses (where many unrelated owners share a commercial mail service) are filtered out by default."
        )
        pfc1, pfc2 = st.columns([2, 1])
        with pfc1:
            f_min_portfolio = st.slider(
                "Minimum portfolio size (parcels at the same mailing address)",
                min_value=1, max_value=100, value=1, step=1, key="dr_min_portfolio",
                help="Set to 10+ to focus on real multi-parcel landlords.",
            )
        with pfc2:
            f_include_maildrops = st.checkbox(
                "Include likely mail drops & high-share addresses",
                value=False, key="dr_incl_maildrops",
                help="Off by default. Mail drops are detected when 50%+ of parcels at an address have different owner names.",
            )

    f = dr.copy()
    if f_hood != "All":
        f = f[f["NEIGHBOR10"] == f_hood]
    if f_owner != "All":
        f = f[f["owner_type"] == f_owner]
    if f_min_distress > 0:
        f = f[f["distress_score"] >= f_min_distress]
    if f_investor:
        f = f[f["investor_flag"] == 1]
    if f_vacant:
        f = f[f["combovac"] == 1]

    _ind_checks = [
        (f_ind_delq, "delinquent_flag"),
        (f_ind_viol, "violation_flag"),
        (f_ind_comp, "complaint_flag"),
        (f_ind_decl, "grade_declined_flag"),
        (f_ind_evic, "eviction_flag"),
    ]
    _selected_cols = [col for checked, col in _ind_checks if checked]
    if _selected_cols:
        _mask_each = [(f[c].fillna(0) == 1) for c in _selected_cols]
        if f_match_mode.startswith("ALL"):
            combined = _mask_each[0]
            for m in _mask_each[1:]:
                combined = combined & m
        else:
            combined = _mask_each[0]
            for m in _mask_each[1:]:
                combined = combined | m
        f = f[combined]

    if not f_include_maildrops:
        f = f[f["is_likely_mail_drop"].fillna(0) == 0]
    if f_min_portfolio > 1:
        f = f[f["true_portfolio_size"].fillna(1) >= f_min_portfolio]

    tab_overview, tab_rentals, tab_portfolios = st.tabs(
        ["Overview", "Rentals", "Portfolios & Owners"]
    )

    with tab_overview:
        k1, k2, k3, k4 = st.columns(4)
        _kpi_css = 'background:#f8f9fc;border-left:4px solid #003071;padding:1rem 1.2rem;border-radius:4px;'
        with k1:
            st.markdown(f'<div style="{_kpi_css}"><div style="font-size:1.6rem;font-weight:700;color:#003071;">{len(f):,}</div><div style="font-size:0.85rem;color:#666;">Rental Properties</div></div>', unsafe_allow_html=True)
        with k2:
            pct_inv = (f["investor_flag"].mean() * 100) if len(f) > 0 else 0
            st.markdown(f'<div style="{_kpi_css}"><div style="font-size:1.6rem;font-weight:700;color:#003071;">{pct_inv:.1f}%</div><div style="font-size:0.85rem;color:#666;">Investor-Owned</div></div>', unsafe_allow_html=True)
        with k3:
            high_distress = int((f["distress_score"] >= 2).sum())
            st.markdown(f'<div style="{_kpi_css}"><div style="font-size:1.6rem;font-weight:700;color:#003071;">{high_distress:,}</div><div style="font-size:0.85rem;color:#666;">≥ 2 Distress Indicators</div></div>', unsafe_allow_html=True)
        with k4:
            declined = int((f["grade_declined_flag"] == 1).sum())
            st.markdown(f'<div style="{_kpi_css}"><div style="font-size:1.6rem;font-weight:700;color:#003071;">{declined:,}</div><div style="font-size:0.85rem;color:#666;">Grade Declined 2015 → 2023</div></div>', unsafe_allow_html=True)

        st.markdown("")

        bc1, bc2 = st.columns(2)
        with bc1:
            st.markdown('<div style="font-size:1.1rem;font-weight:600;color:#003071;margin-bottom:0.5rem;">Owner Type Breakdown</div>', unsafe_allow_html=True)
            ot = f["owner_type"].value_counts().rename("Rentals")
            st.dataframe(ot, use_container_width=True)
        with bc2:
            st.markdown('<div style="font-size:1.1rem;font-weight:600;color:#003071;margin-bottom:0.5rem;">Distress Score Distribution</div>', unsafe_allow_html=True)
            ds = f["distress_score"].value_counts().sort_index().rename("Rentals")
            ds.index = ds.index.astype(str) + " indicator(s)"
            st.dataframe(ds, use_container_width=True)

    with tab_rentals:
        st.markdown(f'<div style="font-size:1.15rem;font-weight:600;color:#003071;margin:0.5rem 0 0.5rem;">Rental Properties ({len(f):,})</div>', unsafe_allow_html=True)
        st.caption("Sort any column by clicking its header. Download the full filtered set as CSV below the table.")

        def _yn(v):
            return "Yes" if v == 1 else "No"
        display = f.copy()
        display["Delinquent"]  = display["delinquent_flag"].map(_yn)
        display["Violation"]   = display["violation_flag"].map(_yn)
        display["Complaint"]   = display["complaint_flag"].map(_yn)
        display["Grade↓"]      = display["grade_declined_flag"].map(lambda v: "-" if pd.isna(v) else ("Yes" if v == 1 else "No"))
        display["Evictions"]   = display["eviction_cases_total"].fillna(0).astype(int)
        display["Investor"]    = display["investor_flag"].map(_yn)
        display["Market Value"] = display["TAX_MARKET_TOTAL"].apply(
            lambda v: f"${int(v):,}" if pd.notna(v) and v > 0 else ""
        )
        display["Delinquent $"] = display["NET_TAX_DELQ_DUE"].apply(
            lambda v: f"${int(v):,}" if pd.notna(v) and v > 0 else ""
        )
        display["Portfolio Size"] = display["true_portfolio_size"].fillna(1).astype(int)

        cols = ["PARCEL", "address", "NEIGHBOR10", "PRIMARY_OWNER_NAME", "owner_type",
                "distress_score", "Delinquent", "Violation", "Complaint", "Grade↓", "Evictions",
                "Investor", "Portfolio Size", "grade_change", "Market Value", "Delinquent $"]
        show = display[cols].rename(columns={
            "PARCEL": "Parcel",
            "address": "Address",
            "NEIGHBOR10": "Neighborhood",
            "PRIMARY_OWNER_NAME": "Owner",
            "owner_type": "Owner Type",
            "distress_score": "Score",
            "grade_change": "Grade Trend",
        })
        show = show.sort_values(["Score", "Portfolio Size", "Evictions"], ascending=[False, False, False])

        st.dataframe(show, use_container_width=True, hide_index=True, height=560)

        csv = f.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"Download CSV ({len(f):,} rows)",
            data=csv,
            file_name=f"distressed_rentals_{f_hood.replace(' ', '_') if f_hood != 'All' else 'all'}.csv",
            mime="text/csv",
        )

    with tab_portfolios:
        st.markdown('<div style="font-size:1.15rem;font-weight:600;color:#003071;margin:0.5rem 0 0.5rem;">Shared Mailing Addresses: Possible Hidden Portfolios</div>', unsafe_allow_html=True)
        st.caption(
            "Addresses where multiple different LLC or entity names receive mail at the same spot. "
            "This pattern often signals a single owner using shell entities to obscure portfolio size: "
            "a 'landlord' listed as four different LLCs may really be one person operating from one P.O. box. "
            "Sorted by number of distinct entity names at the address."
        )

        def _truncate_entities(name_str, n=3):
            if not name_str or pd.isna(name_str):
                return ""
            names = [x.strip() for x in str(name_str).split(" | ") if x.strip()]
            if len(names) <= n:
                return ", ".join(names)
            return ", ".join(names[:n]) + f"  + {len(names) - n} more"

        shared_source = f[
            f["mailing_id"].notna()
            & (f["unique_entity_count"].fillna(1) >= 2)
        ].copy()

        if shared_source.empty:
            st.info("No shared mailing addresses in the current filter. Try broadening filters or enabling 'Include likely mail drops'.")
        else:
            shared = (
                shared_source.groupby("mailing_id", as_index=False)
                .agg(
                    MailingAddress=("mailing_display", "first"),
                    EntityCount=("unique_entity_count", "first"),
                    TotalParcels=("true_portfolio_size", "first"),
                    EntityNames=("all_entity_names", "first"),
                    RentalsInFilter=("PARCEL", "count"),
                    AvgDistress=("distress_score", "mean"),
                )
                .sort_values(["EntityCount", "TotalParcels"], ascending=[False, False])
                .head(50)
            )
            shared["EntityNames"] = shared["EntityNames"].apply(_truncate_entities)
            shared["AvgDistress"] = shared["AvgDistress"].round(2)
            shared = shared.rename(columns={
                "MailingAddress": "Mailing Address",
                "EntityCount": "# Entities",
                "TotalParcels": "Total Parcels",
                "EntityNames": "Entity Names",
                "RentalsInFilter": "Rentals in Filter",
                "AvgDistress": "Avg Distress",
            })
            st.dataframe(shared.drop(columns=["mailing_id"]), use_container_width=True, hide_index=True, height=380)

        st.markdown('<div style="font-size:1.15rem;font-weight:600;color:#003071;margin:1.5rem 0 0.5rem;">Top Portfolios by True Size</div>', unsafe_allow_html=True)
        st.caption(
            "Mailing addresses with the most parcels (across the full county, not just the filtered rentals). "
            "The 'Rentals in Filter' column shows how many of those parcels are rentals from the current filtered set: "
            "use the Portfolio Filters above to focus on larger landlords."
        )
        _port_floor = max(10, f_min_portfolio)
        port_source = f[f["true_portfolio_size"].fillna(0) >= _port_floor].copy()
        if port_source.empty or port_source["mailing_id"].notna().sum() == 0:
            st.info(f"No portfolios with ≥ {_port_floor} parcels in the current filter. Try lowering the Minimum portfolio size filter.")
        else:
            top_port = (
                port_source.dropna(subset=["mailing_id"])
                .groupby("mailing_id", as_index=False)
                .agg(
                    Address=("mailing_display", "first"),
                    PrimaryOwner=("primary_owner_at_mailing", "first"),
                    PortfolioSize=("true_portfolio_size", "first"),
                    UniqueEntities=("unique_entity_count", "first"),
                    RentalsInPortfolio=("PARCEL", "count"),
                    AvgDistress=("distress_score", "mean"),
                    HighDistress=("distress_score", lambda s: int((s >= 2).sum())),
                )
                .sort_values("PortfolioSize", ascending=False)
                .head(50)
            )
            top_port["AvgDistress"] = top_port["AvgDistress"].round(2)
            top_port = top_port.rename(columns={
                "Address": "Mailing Address",
                "PrimaryOwner": "Primary Owner (most common)",
                "PortfolioSize": "Portfolio Size (all parcels)",
                "UniqueEntities": "Unique Entities",
                "RentalsInPortfolio": "Rentals in Filter",
                "AvgDistress": "Avg Distress",
                "HighDistress": "≥2 Distress",
            })
            st.dataframe(top_port.drop(columns=["mailing_id"]), use_container_width=True, hide_index=True, height=360)

    st.markdown("---")
    st.caption(
        "Methodology: adapted from Austin Cummings' R code for identifying extractive rental ownership "
        "(see Center on Poverty &amp; Community Development docs). "
        f"Distress window: {DR_START} to {DR_END}. "
        "Grade trend compares TCI 2015 survey to WRLC 2023 survey where both exist."
    )
