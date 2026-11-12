"""Out-of-State Owner Finder project page."""

import pandas as pd
import streamlit as st

from loaders import load_oos_data
import styles


def render():
    df_raw = load_oos_data()

    df_oos = df_raw[
        ~df_raw["MAIL_STATE"].fillna("").str.strip().isin(["OH", "/", ""])
    ].copy()

    CORP_PAT = r"LLC|INC|CORP|TRUST|INVEST|PROP|HOLD|GROUP|FUND|REAL"
    df_oos["_is_corp"]       = df_oos["PRIMARY_OWNER_NAME"].fillna("").str.contains(CORP_PAT, case=False, regex=True)
    df_oos["_delq_amt"]      = pd.to_numeric(df_oos["NET_TAX_DELQ_DUE"], errors="coerce").fillna(0)
    df_oos["_is_delinquent"] = df_oos["_delq_amt"] > 0
    df_oos["_is_vacant"]     = df_oos["combovac"].fillna(0).astype(float) == 1
    df_oos["_is_condemned"]  = df_oos["active_condemn"].fillna(0).astype(float) == 1
    df_oos["_is_foreclosure"]= df_oos["FORECLOSURE_FLAG"].fillna(0).astype(float) == 1
    df_oos["_no_homestead"]  = df_oos["HOMESTEAD_FLAG"].fillna(0).astype(float) == 0

    total_oos   = len(df_oos)
    pct_corp    = df_oos["_is_corp"].mean() * 100
    total_delq  = df_oos["_delq_amt"].sum()
    vacant_oos  = int(df_oos["_is_vacant"].sum())
    top_states  = df_oos["MAIL_STATE"].value_counts().head(5)

    ind_counts = {
        "delinquent":  int(df_oos["_is_delinquent"].sum()),
        "no_homestead":int(df_oos["_no_homestead"].sum()),
        "vacant":      int(df_oos["_is_vacant"].sum()),
        "corp":        int(df_oos["_is_corp"].sum()),
        "condemned":   int(df_oos["_is_condemned"].sum()),
        "foreclosure": int(df_oos["_is_foreclosure"].sum()),
    }

    styles.inject_oos_owners()

    st.markdown('<div class="breadcrumb"><a href="?auth=1&page=home" target="_self">Home</a> &nbsp;/&nbsp; <a href="?auth=1&page=projects" target="_self">Popular Projects</a> &nbsp;/&nbsp; <strong>Out-of-State Owner Finder</strong></div>', unsafe_allow_html=True)

    states_html = "".join([
        f'<span class="state-chip">{s}<span>({c:,})</span></span>'
        for s, c in top_states.items()
    ])
    st.markdown(f"""
        <div class="oos-hero">
            <div class="oos-hero-title">Out-of-State Owner Finder</div>
            <div class="oos-hero-sub">
                Parcels where the owner's mailing address is outside Ohio: layered with risk signals
                to build targeted outreach, enforcement, and acquisition lists.
            </div>
            <div style="display:grid; grid-template-columns: repeat(4,1fr); gap: 1.5rem;">
                <div>
                    <div class="oos-stat-num">{total_oos:,}</div>
                    <div class="oos-stat-label">Out-of-State Parcels</div>
                </div>
                <div>
                    <div class="oos-stat-num">{pct_corp:.0f}%</div>
                    <div class="oos-stat-label">Corporate / LLC Owned</div>
                </div>
                <div>
                    <div class="oos-stat-num">${total_delq/1000:.0f}k</div>
                    <div class="oos-stat-label">Total Tax Delinquency</div>
                </div>
                <div>
                    <div class="oos-stat-num">{vacant_oos:,}</div>
                    <div class="oos-stat-label">Vacant Properties</div>
                </div>
            </div>
            <div style="margin-top:1.5rem; font-size:0.75rem; color:rgba(255,255,255,0.5); text-transform:uppercase; letter-spacing:0.06em; margin-bottom:0.4rem;">Top origin states</div>
            <div class="states-row">{states_html}</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="step-wrap">
            <div class="step-num">1</div>
            <div>
                <div class="step-title">Where do you want to investigate?</div>
                <div class="step-sub">Narrow to specific neighborhoods, or leave blank to search all of Cuyahoga County.</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    all_hoods = sorted(df_oos["NEIGHBOR10"].dropna().unique().tolist())
    selected_hoods = st.multiselect(
        "Neighborhoods",
        options=all_hoods,
        key="oos_hoods",
        label_visibility="collapsed",
        placeholder="All neighborhoods: type to search and select",
    )
    if selected_hoods:
        st.caption(f"{len(selected_hoods)} neighborhood(s) selected")

    st.markdown("""
        <div class="step-wrap">
            <div class="step-num">2</div>
            <div>
                <div class="step-title">What risk signals matter to you?</div>
                <div class="step-sub">Each card shows how many out-of-state owners carry that flag. Check any to narrow your results.</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    def ind_card(icon, title, count, pct, desc):
        return f"""
            <div class="ind-title">{title}</div>
            <div class="ind-count">{count:,}</div>
            <div class="ind-pct">{pct:.1f}% of out-of-state owners</div>
            <div class="ind-desc">{desc}</div>
        """

    row1 = st.columns(3)
    with row1[0]:
        with st.container(border=True):
            st.markdown(ind_card("", "Tax Delinquent",
                ind_counts["delinquent"], ind_counts["delinquent"]/total_oos*100,
                "Owner has unpaid tax obligations outstanding on this property."),
                unsafe_allow_html=True)
            f_delinquent = st.checkbox("Filter by this signal", key="f_delq")
    with row1[1]:
        with st.container(border=True):
            st.markdown(ind_card("", "No Homestead Exemption",
                ind_counts["no_homestead"], ind_counts["no_homestead"]/total_oos*100,
                "Owner does not claim homestead: they are not living at this address."),
                unsafe_allow_html=True)
            f_no_homestead = st.checkbox("Filter by this signal", key="f_home")
    with row1[2]:
        with st.container(border=True):
            st.markdown(ind_card("", "Vacant Property",
                ind_counts["vacant"], ind_counts["vacant"]/total_oos*100,
                "Property is recorded as vacant in the combined vacancy field."),
                unsafe_allow_html=True)
            f_vacant = st.checkbox("Filter by this signal", key="f_vac")

    row2 = st.columns(3)
    with row2[0]:
        with st.container(border=True):
            st.markdown(ind_card("", "Corporate / LLC Owner",
                ind_counts["corp"], ind_counts["corp"]/total_oos*100,
                "Owner name contains LLC, INC, CORP, TRUST, or similar entity indicators."),
                unsafe_allow_html=True)
            f_corp = st.checkbox("Filter by this signal", key="f_corp")
    with row2[1]:
        with st.container(border=True):
            st.markdown(ind_card("", "Active Condemnation",
                ind_counts["condemned"], ind_counts["condemned"]/total_oos*100,
                "Property has an active condemnation order on record."),
                unsafe_allow_html=True)
            f_condemned = st.checkbox("Filter by this signal", key="f_cond")
    with row2[2]:
        with st.container(border=True):
            st.markdown(ind_card("", "In Foreclosure",
                ind_counts["foreclosure"], ind_counts["foreclosure"]/total_oos*100,
                "Property is currently flagged as being in the foreclosure process."),
                unsafe_allow_html=True)
            f_foreclosure = st.checkbox("Filter by this signal", key="f_fc")

    df_filtered = df_oos.copy()
    if f_delinquent:   df_filtered = df_filtered[df_filtered["_is_delinquent"]]
    if f_no_homestead: df_filtered = df_filtered[df_filtered["_no_homestead"]]
    if f_vacant:       df_filtered = df_filtered[df_filtered["_is_vacant"]]
    if f_corp:         df_filtered = df_filtered[df_filtered["_is_corp"]]
    if f_condemned:    df_filtered = df_filtered[df_filtered["_is_condemned"]]
    if f_foreclosure:  df_filtered = df_filtered[df_filtered["_is_foreclosure"]]
    if selected_hoods: df_filtered = df_filtered[df_filtered["NEIGHBOR10"].isin(selected_hoods)]

    df_filtered = df_filtered.copy()
    df_filtered["Risk Score"] = (
        df_filtered["_is_delinquent"].astype(int) +
        df_filtered["_no_homestead"].astype(int)  +
        df_filtered["_is_vacant"].astype(int)     +
        df_filtered["_is_corp"].astype(int)       +
        df_filtered["_is_condemned"].astype(int)  +
        df_filtered["_is_foreclosure"].astype(int)
    )

    st.markdown("""
        <div class="step-wrap">
            <div class="step-num">3</div>
            <div>
                <div class="step-title">Your Results</div>
                <div class="step-sub">Properties sorted by risk score: highest first. Export to CSV for outreach or further analysis.</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    active = []
    if selected_hoods:  active.append(f"{len(selected_hoods)} Neighborhood(s)")
    if f_delinquent:    active.append("Tax Delinquent")
    if f_no_homestead:  active.append("No Homestead")
    if f_vacant:        active.append("Vacant")
    if f_corp:          active.append("Corporate / LLC")
    if f_condemned:     active.append("Active Condemnation")
    if f_foreclosure:   active.append("In Foreclosure")

    if active:
        pills = "".join([f'<span class="filter-pill">{a}</span>' for a in active])
        st.markdown(f'<div style="margin-bottom:0.75rem;"><span style="font-size:0.82rem;color:#888;margin-right:0.5rem;">Active filters:</span>{pills}</div>', unsafe_allow_html=True)

    st.markdown(f"""
        <div class="match-banner">
            <div class="match-num">{len(df_filtered):,}</div>
            <div>
                <div class="match-text">properties match your investigation</div>
                <div class="match-label">out of {total_oos:,} total out-of-state owners</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    display_col_map = {
        "address":                    "Address",
        "PARCEL":                     "Parcel ID",
        "PRIMARY_OWNER_NAME":         "Owner Name",
        "MAIL_STATE":                 "Owner State",
        "NEIGHBOR10":                 "Neighborhood",
        "ward2025":                   "Ward",
        "zip":                        "ZIP",
        "CLASSIFICATION_DESCR":       "Classification",
        "TAX_MARKET_TOTAL":           "Market Value ($)",
        "NET_TAX_DELQ_DUE":           "Tax Delinquent ($)",
        "HOMESTEAD_FLAG":             "Homestead",
        "combovac":                   "Vacant",
        "FORECLOSURE_FLAG":           "Foreclosure",
        "active_condemn":             "Condemnation",
        "lsc_stat":                   "Lead Safe Cert",
        "rentalreg":                  "Rental Reg.",
        "Risk Score":                 "Risk Score",
    }

    available_cols = [c for c in display_col_map if c in df_filtered.columns]
    df_display = df_filtered[available_cols].copy()
    df_display = df_display.rename(columns=display_col_map)
    df_display = df_display.sort_values("Risk Score", ascending=False).reset_index(drop=True)

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Risk Score": st.column_config.ProgressColumn(
                "Risk Score",
                help="Number of risk indicators active for this property (max 6)",
                min_value=0,
                max_value=6,
                format="%d",
            ),
            "Market Value ($)":    st.column_config.NumberColumn(format="$%d"),
            "Tax Delinquent ($)":  st.column_config.NumberColumn(format="$%d"),
        },
    )

    csv_export = df_display.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Results as CSV",
        data=csv_export,
        file_name="oos_owners_export.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #666; padding: 2rem 0;">
            <p>Powered by CWRU Poverty Center | Last Updated: January 2026</p>
        </div>
    """, unsafe_allow_html=True)
