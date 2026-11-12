"""Summary tab: value statistics, top neighborhoods, distress counts, foreclosure cases."""

import pandas as pd
import streamlit as st


def render(filtered_df):
    if len(filtered_df) == 0:
        st.info("No data to summarize. Adjust your filters.")
        return

    su1, su2 = st.columns(2)
    with su1:
        st.markdown("**Value Statistics**")
        val_cols = [c for c in ["TAX_MARKET_TOTAL", "TAX_MARKET_LAND", "TAX_MARKET_IMPROVEMENT",
                                "currentvalue2023", "lsaleamt"]
                    if c in filtered_df.columns]
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
