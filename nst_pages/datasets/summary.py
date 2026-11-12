"""Active-filter summary line and the 4-column stat boxes."""

import streamlit as st


def render_summary_line(state):
    """One-line recap of every active filter so the user can see them when scrolled down."""
    parts = []
    parts.append(f"Area: {state['neighborhood']}")
    yr_note = '' if state['yr_include_unknown'] else ' (known years only)'
    parts.append(f"Year Built: {state['year_range'][0]}–{state['year_range'][1]}{yr_note}")
    parts.append(f"Property Value: {state['val_label']}")
    parts.append(f"Property Type: {state['prop_type']}")
    parts.append(f"Condition: {state['condition']}")

    active = st.session_state.get("ds_presets", set())
    if active:
        parts.append(f"Presets: {', '.join(sorted(active))}")

    # Dropdown filters set to "All" are hidden; only show user-chosen values.
    dropdown_map = [
        ("ward", "Ward"), ("zip", "ZIP"), ("region", "Region"), ("cia", "CIA Area"),
        ("style", "Style"), ("stories", "Stories"), ("zone", "Zoning"),
        ("pclass", "Property Class"), ("bed", "Bedrooms"), ("bath", "Bathrooms"),
        ("taxabate", "Tax Abatement"), ("vtype", "Violation Type"),
        ("vtask", "Violation Status"), ("lsc", "LSC Status"),
        ("lead_rollout", "Lead Rollout"), ("fo_status", "Foreclosure Status"),
        ("cdesig", "Case Designation"), ("demo_status", "Demo Status"),
        ("rehab_status", "Rehab Status"), ("disp_status", "Disposition"),
    ]
    for key, label in dropdown_map:
        if state.get(key, "All") != "All":
            parts.append(f"{label}: {state[key]}")

    if state["sqft"] != (0, state["sqft_max"]):
        parts.append(f"Sq Ft: {state['sqft'][0]:,}–{state['sqft'][1]:,}")

    bool_filters = []
    bool_map = [
        ("homestead", "Homestead exemption"), ("payment_plan", "On payment plan"),
        ("cert_pend", "Tax cert. pending"), ("cert_sold", "Tax cert. sold"),
        ("active_condemn", "Active condemnation"), ("bh_lead", "B&H lead violation"),
        ("cdc_comp", "CDC complaint"), ("council_comp", "Council complaint"),
        ("has_fo_deed", "Has fiscal officer deed"), ("city_lb", "City Land Bank"),
        ("cclrc", "CCLRC"), ("rental", "Rental registered"),
        ("sect8", "Section 8"), ("hud", "HUD"), ("out_of_state", "Out-of-state owner"),
    ]
    for key, label in bool_map:
        if state.get(key):
            bool_filters.append(label)
    if state.get("evict_status", "All") != "All":
        bool_filters.append(f"Eviction status: {state['evict_status']}")
    if state.get("evict_disp", "All") != "All":
        bool_filters.append(f"Eviction disposition: {state['evict_disp']}")
    if state.get("evict_yr", "All") != "All":
        bool_filters.append(f"Eviction year: {state['evict_yr']}")
    if state.get("evict_multi"):
        bool_filters.append("Multiple evictions")
    if bool_filters:
        parts.append(f"Other: {', '.join(bool_filters)}")

    html = "  |  ".join(parts)
    st.markdown(
        f'<div style="font-size:0.85rem;color:#555;margin-bottom:0.75rem;line-height:1.8;">'
        f'<strong style="color:#003071;">Active Filters:</strong>  {html}</div>',
        unsafe_allow_html=True,
    )


def render_stat_boxes(filtered_df):
    """Four big KPI tiles at the top of the results area."""
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
