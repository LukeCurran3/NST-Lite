"""Table tab and the column customizer expander that feeds it."""

import pandas as pd
import streamlit as st

from config import COL_GROUPS, PRESET_COLUMNS, COLUMN_LABELS


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


def render_column_customizer(df):
    """Expander that lets the user pick a column preset or a custom selection."""
    with st.expander("Customize Columns"):
        preset_sel = st.radio(
            "Column preset",
            list(PRESET_COLUMNS.keys()) + ["Custom"],
            horizontal=True,
            key="col_preset",
        )
        if preset_sel != "Custom":
            return [c for c in PRESET_COLUMNS[preset_sel] if c in df.columns]

        custom_selections = []
        for group_name, group_cols in COL_GROUPS.items():
            valid_cols = [c for c in group_cols if c in df.columns]
            if not valid_cols:
                continue
            with st.expander(f"{group_name}"):
                gcol1, gcol2 = st.columns([1, 3])
                with gcol1:
                    st.button("All", key=f"all_{group_name}")
                    st.button("None", key=f"none_{group_name}")
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
        return custom_selections if custom_selections else [c for c in PRESET_COLUMNS["Basic Info"] if c in df.columns]


def render(filtered_df, display_columns):
    """Table tab body. Formats currency and flag columns before display."""
    if len(filtered_df) == 0:
        st.info("No properties match your filters.")
        return

    valid_display = [c for c in display_columns if c in filtered_df.columns]
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
