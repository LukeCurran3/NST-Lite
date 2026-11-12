"""Property Search page: lookup by address, parcel, or owner."""

import pandas as pd
import streamlit as st
import plotly.express as px

from loaders import (
    ps_search, ps_value_history, ps_sales_history,
    ps_tax_history, ps_hood_counts,
)
from utils.formatting import fmt_val, fmt_int as _fmt_int, flag_yn_colored
from utils.html import cell, grid, section
import styles


def render():
    query_params = st.query_params

    def fmt(val, prefix="", suffix="", fmt_int=False, na="N/A"):
        """Legacy signature; delegates to shared formatters in utils.formatting."""
        if fmt_int:
            return _fmt_int(val, prefix=prefix, suffix=suffix, na=na)
        return fmt_val(val, prefix=prefix, suffix=suffix, na=na)

    flag = flag_yn_colored

    styles.inject_property_search()

    st.markdown(
        '<div class="breadcrumb">'
        '<a href="?auth=1&page=home" target="_self">Home</a> &nbsp;/&nbsp; '
        '<a href="?auth=1&page=datasets" target="_self">Data</a> &nbsp;/&nbsp; '
        '<strong>Property Search</strong></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div style="font-size:2.5rem;font-weight:700;color:#003071;margin-bottom:0.3rem;">Property Search</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:1.1rem;color:#666;margin-bottom:1rem;">Look up detailed information for a specific address, parcel ID, or owner name.</div>', unsafe_allow_html=True)

    # Deep link from Datasets map popup: ?parcel=... pre-fills the search box.
    _url_parcel = query_params.get("parcel")
    if _url_parcel and "ps_search" not in st.session_state:
        st.session_state["ps_search"] = _url_parcel

    ps_query = st.text_input(
        "Search by address, parcel ID, or owner name",
        placeholder="e.g. 1234 W 25th St  |  123-45-678  |  SMITH JOHN",
        key="ps_search",
    )

    if ps_query:
        results = ps_search(ps_query)
        for c in results.select_dtypes(include='object').columns:
            results[c] = results[c].replace('NONE', pd.NA)

        if len(results) == 0:
            st.warning("No properties found. Try a different address, parcel ID, or owner name.")
        elif len(results) > 20:
            st.warning(f"{len(results):,} results: please be more specific (city, zip, or full address).")
        else:
            if len(results) > 1:
                st.markdown(f"**{len(results)} properties found.** Select one to view its full profile:")
                options = [
                    f"{r.get('address','Unknown')}  ·  {r.get('NEIGHBOR10','')}  ({r['PARCEL']})"
                    for _, r in results.iterrows()
                ]
                sel = st.selectbox("Select a property", options, label_visibility="collapsed")
                prop = results.iloc[options.index(sel)].to_dict()
            else:
                prop = results.iloc[0].to_dict()

            parcel_id = str(prop.get("PARCEL", ""))

            ward_str = fmt(prop.get("ward2025"), fmt_int=True)
            zip_str  = fmt(prop.get("zip"), fmt_int=True)
            addr     = prop.get("address") or f"{prop.get('number','')} {prop.get('street','')}".strip() or "Unknown Address"
            mkt_val  = prop.get("TAX_MARKET_TOTAL")
            mkt_str  = f"${int(mkt_val):,}" if pd.notna(mkt_val) and mkt_val else "N/A"
            yr       = prop.get("yrbuilt")
            yr_str   = str(int(yr)) if pd.notna(yr) and yr and int(yr) not in (0, 9999) else "N/A"

            st.markdown(f"""
                <div style="background:white;border:1px solid #dde;border-radius:8px;
                            padding:1.5rem 1.75rem;margin-bottom:1rem;">
                    <div class="ps-header">{addr}</div>
                    <div class="ps-meta">
                        Parcel <strong>{parcel_id}</strong>
                        &nbsp;·&nbsp; {fmt(prop.get('NEIGHBOR10'))}
                        &nbsp;·&nbsp; Ward {ward_str}
                        &nbsp;·&nbsp; ZIP {zip_str}
                        &nbsp;·&nbsp; {fmt(prop.get('cuyregion'))}
                    </div>
                    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;">
                        <div><div class="kpi-val">{mkt_str}</div><div class="kpi-lbl">Market Value</div></div>
                        <div><div class="kpi-val">{yr_str}</div><div class="kpi-lbl">Year Built</div></div>
                        <div><div class="kpi-val">{fmt(prop.get('condition'))}</div><div class="kpi-lbl">Condition</div></div>
                        <div><div class="kpi-val" style="font-size:1.1rem;">{fmt(prop.get('PRIMARY_OWNER_NAME'))}</div><div class="kpi-lbl">Owner</div></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            t_overview, t_history, t_violations, t_evictions, t_location = st.tabs([
                "Overview", "Values & History", "Violations & Lead", "Evictions", "Location"
            ])

            with t_overview:
                section("Property Details")
                yr_disp = yr_str
                st.markdown(grid(
                    cell("Property Type",  fmt(prop.get("CLASSIFICATION_DESCR"))),
                    cell("Year Built",     yr_disp),
                    cell("Condition",      fmt(prop.get("condition"))),
                    cell("Style",          fmt(prop.get("style"))),
                    cell("Stories",        fmt(prop.get("numstory"))),
                    cell("Exterior Wall",  fmt(prop.get("rextwall"))),
                    cell("Building Sqft",  fmt(prop.get("basesqft"), fmt_int=True)),
                    cell("Bedrooms",       fmt(prop.get("bedrooms"), fmt_int=True)),
                    cell("Bathrooms",      fmt(prop.get("baths"))),
                    cell("Units",          fmt(prop.get("units"), fmt_int=True)),
                    cell("Lot Size (sqft)",fmt(prop.get("propsize"), fmt_int=True)),
                    cell("Zoning",         fmt(prop.get("zone_desc"))),
                ), unsafe_allow_html=True)

                section("Ownership & Occupancy")
                st.markdown(grid(
                    cell("Owner",              fmt(prop.get("PRIMARY_OWNER_NAME"))),
                    cell("Owner Mail State",   fmt(prop.get("MAIL_STATE"))),
                    cell("Parcel Status",      fmt(prop.get("parcel_status"))),
                    cell("Vacant",             flag(prop.get("combovac"))),
                    cell("Vacant Lot",         flag(prop.get("vl"))),
                    cell("Unoccupied",         flag(prop.get("unoccupied"))),
                    cell("In Foreclosure",     flag(prop.get("FORECLOSURE_FLAG"))),
                    cell("Foreclosure Status", fmt(prop.get("lstatus"))),
                    cell("Active Condemnation",flag(prop.get("active_condemn"))),
                    cell("City Land Bank",     flag(prop.get("city_lb_flag"))),
                    cell("CCLRC",              flag(prop.get("cclrc"))),
                    cell("Disposition Status", fmt(prop.get("disp_status"))),
                ), unsafe_allow_html=True)

                section("Value & Tax")
                delq = prop.get("NET_TAX_DELQ_DUE")
                delq_disp = (f'<span style="color:#c0392b;font-weight:600;">${int(float(delq)):,}</span>'
                             if pd.notna(delq) and delq and float(delq) > 0
                             else '<span style="color:#1e8449;font-weight:600;">None</span>')
                st.markdown(grid(
                    cell("Market Value",      fmt(prop.get("TAX_MARKET_TOTAL"), prefix="$", fmt_int=True)),
                    cell("Land Value",        fmt(prop.get("TAX_MARKET_LAND"), prefix="$", fmt_int=True)),
                    cell("Improvement Value", fmt(prop.get("TAX_MARKET_IMPROVEMENT"), prefix="$", fmt_int=True)),
                    cell("2023 Value",        fmt(prop.get("currentvalue2023"), prefix="$", fmt_int=True)),
                    cell("Proposed 2024",     fmt(prop.get("proposedvalue2024"), prefix="$", fmt_int=True)),
                    cell("Tax Delinquent",    delq_disp),
                    cell("Homestead",         flag(prop.get("HOMESTEAD_FLAG"))),
                    cell("Payment Plan",      flag(prop.get("PAYMENT_PLAN_FLAG"))),
                    cell("Tax Abatement",     fmt(prop.get("taxabate"))),
                    cell("Cert Pending",      flag(prop.get("CERT_PEND_FLAG"))),
                    cell("Cert Sold",         flag(prop.get("CERT_SOLD_FLAG"))),
                    cell("FO Deed Count",     fmt(prop.get("fo_deed_count"), fmt_int=True)),
                ), unsafe_allow_html=True)

                section("Programs & Registration")
                st.markdown(grid(
                    cell("Rental Registered", flag(prop.get("rentalreg"))),
                    cell("Section 8",         flag(prop.get("sect8"))),
                    cell("Section 8 (County)",flag(prop.get("sect8_cnty"))),
                    cell("HUD",               flag(prop.get("hud"))),
                    cell("Demo Status",       fmt(prop.get("demo_status"))),
                    cell("Rehab Status",      fmt(prop.get("rehab_status"))),
                    cell("Last Permit Type",  fmt(prop.get("last_permit_category"))),
                    cell("Last Permit Date",  fmt(prop.get("last_permit_file_date"))),
                    cell("CIA Area",          fmt(prop.get("cia14_name"))),
                ), unsafe_allow_html=True)
                st.markdown("""
                    <div style="background:#f0f4ff;border-left:4px solid #003071;padding:0.75rem 1rem;
                                border-radius:4px;font-size:0.88rem;color:#444;margin-top:0.5rem;">
                        <strong>Contacts:</strong>&nbsp;
                        Rental Registration: City of Cleveland Division of Building &amp; Housing
                        <a href="https://www.clevelandohio.gov/city-hall/departments/building-housing/divisions/records-administration/rental-registration" target="_blank" style="color:#003071;">clevelandohio.gov</a>
                        · (216) 664-2827 · bhrental@clevelandohio.gov&nbsp;&nbsp;|&nbsp;&nbsp;
                        Section 8 / HCV: CMHA
                        <a href="https://www.cmha.net" target="_blank" style="color:#003071;">cmha.net</a>
                        · (216) 431-1471
                    </div>
                """, unsafe_allow_html=True)

            with t_history:
                val_hist = ps_value_history(parcel_id)
                if not val_hist.empty:
                    section("Market Value Over Time")
                    st.caption("County-assessed market value by year. The dashed line shows what the value would be if it had only kept pace with inflation (CPI).")
                    fig = px.line(
                        val_hist, x="taxyr", y=["mktval", "mktland", "mktbldg"],
                        labels={"taxyr": "Tax Year", "value": "Value ($)"},
                        color_discrete_map={
                            "mktval": "#003071",
                            "mktland": "#e67e22",
                            "mktbldg": "#16a34a",
                        },
                    )
                    _name_map = {"mktval": "Total Market Value", "mktland": "Land Value", "mktbldg": "Building Value"}
                    fig.for_each_trace(lambda t: t.update(
                        name=_name_map.get(t.name, t.name),
                        hovertemplate="%{y:$,.0f}<extra>" + _name_map.get(t.name, t.name) + "</extra>",
                        line=dict(width=3),
                    ))

                    # BLS CPI-U annual averages.
                    _CPI = {
                        2010: 218.1, 2011: 224.9, 2012: 229.6, 2013: 233.0, 2014: 236.7,
                        2015: 237.0, 2016: 240.0, 2017: 245.1, 2018: 251.1, 2019: 255.7,
                        2020: 258.8, 2021: 271.0, 2022: 292.7, 2023: 304.7, 2024: 314.5,
                        2025: 320.0,
                    }
                    _base = val_hist.dropna(subset=["mktval"]).sort_values("taxyr").iloc[0]
                    _base_yr, _base_val = int(_base["taxyr"]), _base["mktval"]
                    if _base_yr in _CPI and _base_val and _base_val > 0:
                        _infl_years = [int(y) for y in val_hist["taxyr"].dropna() if int(y) in _CPI]
                        _infl_vals  = [_base_val * (_CPI[y] / _CPI[_base_yr]) for y in _infl_years]
                        import plotly.graph_objects as go
                        fig.add_trace(go.Scatter(
                            x=_infl_years, y=_infl_vals,
                            mode="lines", name="Inflation Baseline",
                            line=dict(color="#aaa", width=1.5, dash="dash"),
                            hovertemplate="%{y:$,.0f}<extra>Inflation Baseline</extra>",
                        ))

                    fig.update_layout(
                        yaxis_tickprefix="$", yaxis_tickformat=",",
                        hovermode="x unified", height=340,
                        legend=dict(orientation="h", y=1.1),
                        margin=dict(t=20, b=20),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    _COND_RANK = {"EX": 8, "VG": 7, "G": 6, "AVG": 5, "F": 4, "PR": 3, "VP": 2, "US": 1, "SV": 0}
                    _COND_LABEL = {"EX": "Excellent", "VG": "Very Good", "G": "Good", "AVG": "Average",
                                   "F": "Fair", "PR": "Poor", "VP": "Very Poor", "US": "Unsound", "SV": "Salvage"}
                    _COND_COLOR = {"EX": "#16a34a", "VG": "#4ade80", "G": "#86efac",
                                   "AVG": "#f59e0b", "F": "#fb923c", "PR": "#ef4444",
                                   "VP": "#b91c1c", "US": "#7f1d1d", "SV": "#3f0000"}
                    cond_df = val_hist[["taxyr", "condition"]].dropna(subset=["condition"])
                    cond_df = cond_df[cond_df["condition"].str.strip().ne("")]
                    if not cond_df.empty:
                        section("Condition Over Time")
                        st.caption("Condition grade assigned by the County Auditor appraiser at each assessment year.")
                        cond_df = cond_df.copy()
                        cond_df["rank"]  = cond_df["condition"].map(_COND_RANK)
                        cond_df["label"] = cond_df["condition"].map(_COND_LABEL).fillna(cond_df["condition"])
                        cond_df["color"] = cond_df["condition"].map(_COND_COLOR).fillna("#aaa")
                        cond_df["taxyr"] = cond_df["taxyr"].astype(int)
                        import plotly.graph_objects as go
                        fig_cond = go.Figure(go.Bar(
                            x=cond_df["taxyr"],
                            y=cond_df["rank"],
                            marker_color=cond_df["color"],
                            text=cond_df["label"],
                            textposition="inside",
                            hovertemplate="<b>%{text}</b><extra>Tax Year %{x}</extra>",
                        ))
                        fig_cond.update_layout(
                            xaxis=dict(title="Tax Year", dtick=1, tickformat="d"),
                            yaxis=dict(
                                title="", tickmode="array",
                                tickvals=list(_COND_RANK.values()),
                                ticktext=list(_COND_LABEL.values()),
                                range=[-0.5, 8.5],
                            ),
                            height=260, margin=dict(t=10, b=20),
                            showlegend=False,
                        )
                        st.plotly_chart(fig_cond, use_container_width=True)

                    section("Owner History")
                    owner_hist = val_hist[["taxyr", "owner", "condition", "ownerocc"]].dropna(subset=["owner"])
                    owner_hist = owner_hist.rename(columns={
                        "taxyr": "Tax Year", "owner": "Owner",
                        "condition": "Condition", "ownerocc": "Owner Occupied",
                    })
                    owner_hist["Tax Year"] = owner_hist["Tax Year"].astype(int)
                    owner_hist["Owner Occupied"] = owner_hist["Owner Occupied"].map(
                        lambda x: "Yes" if x == 1 else ("No" if x == 0 else "")
                    )
                    st.dataframe(owner_hist.sort_values("Tax Year", ascending=False), use_container_width=True, hide_index=True)
                else:
                    st.info("No historical value data found for this parcel.")

                sales_hist = ps_sales_history(parcel_id)
                if not sales_hist.empty:
                    section("Sales History")
                    sales_hist["Sale Date"] = sales_hist.apply(
                        lambda r: f"{int(r['YEAR_OF_SALE'])}-{int(r['MONTH_OF_SALE']):02d}"
                        if pd.notna(r["YEAR_OF_SALE"]) and pd.notna(r["MONTH_OF_SALE"]) else "Unknown",
                        axis=1,
                    )
                    sales_hist["Sale Amount"] = sales_hist["SALES_AMOUNT"].apply(
                        lambda x: f"${int(x):,}" if pd.notna(x) else "N/A"
                    )
                    _sale_valid_map = {1.0: "Valid", 2.0: "Not Valid", 0.0: "Unknown", 3.0: "Forced Sale", -1.0: "N/A"}
                    sales_hist["Valid Sale"] = sales_hist["SALE_VALID"].map(
                        lambda x: _sale_valid_map.get(float(x), str(x)) if pd.notna(x) else ""
                    )
                    show_sales = sales_hist[["Sale Date", "Sale Amount", "GRANTEE1", "GRANTOR1", "DEED_TYPE", "TRANSFER_TYPE_DESCR", "Valid Sale"]].rename(columns={
                        "GRANTEE1": "Buyer", "GRANTOR1": "Seller",
                        "DEED_TYPE": "Deed Type", "TRANSFER_TYPE_DESCR": "Transfer Type",
                    })
                    st.dataframe(show_sales, use_container_width=True, hide_index=True)
                else:
                    st.info("No sales history found for this parcel.")

                tax_hist = ps_tax_history(parcel_id)
                if not tax_hist.empty:
                    section("Tax Bill History")
                    for col in ["TAX_MARKET_TOTAL", "TAX_MARKET_LAND", "TAX_MARKET_IMPROVEMENT",
                                "NET_TAX_DELQ_DUE", "GRAND_TOTAL_OWED", "GRAND_TOTAL_PAID", "GRAND_TOTAL_BALANCE"]:
                        if col in tax_hist.columns:
                            tax_hist[col] = tax_hist[col].apply(
                                lambda x: f"${int(x):,}" if pd.notna(x) and isinstance(x, (int, float)) else ""
                            )
                    tax_hist["TAX_YEAR"] = tax_hist["TAX_YEAR"].apply(
                        lambda x: int(x) if pd.notna(x) else x
                    )
                    st.dataframe(
                        tax_hist.rename(columns={
                            "TAX_YEAR": "Year", "TAX_MARKET_TOTAL": "Market Value",
                            "TAX_MARKET_LAND": "Land", "TAX_MARKET_IMPROVEMENT": "Improvement",
                            "NET_TAX_DELQ_DUE": "Delinquent", "GRAND_TOTAL_OWED": "Total Owed",
                            "GRAND_TOTAL_PAID": "Total Paid", "GRAND_TOTAL_BALANCE": "Balance",
                        }),
                        use_container_width=True, hide_index=True,
                    )

            with t_violations:
                section("Violations")
                st.markdown(grid(
                    cell("Has Violation",       flag(prop.get("violation"))),
                    cell("Violation Type",      fmt(prop.get("violation_vtype"))),
                    cell("Violation Status",    fmt(prop.get("violation_task_status"))),
                    cell("Violation Date",      fmt(prop.get("violation_file_date"))),
                    cell("Violation #",         fmt(prop.get("violation_vin"))),
                    cell("Active Condemnation", flag(prop.get("active_condemn"))),
                    cell("COD Condemned",       fmt(prop.get("cod_condemed_status"))),
                    cell("COD Violations",      fmt(prop.get("cod_current_violations"))),
                    cell("B&H Lead Violation",  flag(prop.get("cod_current_bh_lead_violations"))),
                ), unsafe_allow_html=True)

                section("Lead Safe Certification")
                st.markdown(grid(
                    cell("Lead Safe Status",   fmt(prop.get("lsc_stat"))),
                    cell("Issue Date",         fmt(prop.get("lsc_issue_dt"))),
                    cell("Lead Rollout Phase", fmt(prop.get("lead_rollout"))),
                    cell("Compliance Accepted",fmt(prop.get("compliance_acc"))),
                    cell("Compliance Date",    fmt(prop.get("compliance_acc_dt"))),
                ), unsafe_allow_html=True)

                section("Complaints")
                st.markdown(grid(
                    cell("Any Complaint",   flag(prop.get("anycomplaint"))),
                    cell("CDC",            flag(prop.get("cdc_comp"))),
                    cell("Council",        flag(prop.get("council_comp"))),
                    cell("Mayor",          flag(prop.get("mayor_comp"))),
                    cell("MAC",            flag(prop.get("mac_comp"))),
                    cell("Public",         flag(prop.get("public_comp"))),
                    cell("Other",          flag(prop.get("other_comp"))),
                ), unsafe_allow_html=True)

            with t_evictions:
                evict_years = list(range(2016, 2026))
                evict_cols  = [f"cases_filed_{y}" for y in evict_years]
                evict_vals  = [int(x) if pd.notna(x := prop.get(c)) else 0 for c in evict_cols]

                if any(v > 0 for v in evict_vals):
                    section("Eviction Cases Filed by Year")
                    evict_df = pd.DataFrame({"Year": evict_years, "Cases Filed": evict_vals})
                    fig2 = px.bar(
                        evict_df, x="Year", y="Cases Filed",
                        color_discrete_sequence=["#003071"],
                        text="Cases Filed",
                    )
                    fig2.update_traces(textposition="outside")
                    fig2.update_layout(
                        xaxis=dict(dtick=1, tickformat="d"),
                        yaxis_title="Cases Filed",
                        height=320,
                        margin=dict(t=10, b=10),
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("No eviction cases on record for this property (2016-2025).")

                section("Current Eviction Case")
                st.markdown(grid(
                    cell("Case Number",      fmt(prop.get("evict_case_number"))),
                    cell("Case Status",      fmt(prop.get("evict_case_status"))),
                    cell("Disposition",      fmt(prop.get("evict_disp_status"))),
                    cell("Year",             fmt(prop.get("evict_yr"), fmt_int=True)),
                ), unsafe_allow_html=True)

            with t_location:
                import folium
                from streamlit_folium import st_folium
                lat = prop.get("LATITUDE")
                lon = prop.get("LONGITUDE")
                if pd.notna(lat) and pd.notna(lon):
                    m = folium.Map(location=[lat, lon], zoom_start=16, tiles="OpenStreetMap")
                    folium.Marker(
                        location=[lat, lon],
                        tooltip=f"<b>{addr}</b><br>{parcel_id}",
                        icon=folium.Icon(color="darkblue", icon="home"),
                    ).add_to(m)
                    st_folium(m, width=None, height=480, use_container_width=True, returned_objects=[])
                else:
                    st.info("No coordinates available for this property.")

    else:
        st.markdown("")
        st.markdown("**Quick links: browse by neighborhood:**")
        hc = ps_hood_counts()
        cols = st.columns(5)
        for i, row in hc.iterrows():
            with cols[i % 5]:
                st.markdown(
                    f'<a href="?auth=1&page=datasets" target="_self" '
                    f'style="color:#003071;text-decoration:none;font-weight:500;">{row["NEIGHBOR10"]}</a>'
                    f' <span style="color:#999;font-size:0.85rem;">({int(row["cnt"]):,})</span>',
                    unsafe_allow_html=True,
                )

    st.markdown("---")
    st.caption("CWRU Poverty Center · Cuyahoga County property data")
