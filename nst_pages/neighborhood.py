"""Neighborhood profile page."""

import json
import math

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from loaders import load_neighborhood_data


def render(hood_name):
    selected_hood = hood_name

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

    if not selected_hood:
        st.warning("No neighborhood selected. Please choose one from the Map Explorer.")
        st.markdown('<a href="?auth=1&page=maps" target="_self">← Back to Map Explorer</a>', unsafe_allow_html=True)
        return

    hood_df = load_neighborhood_data(selected_hood)
    if hood_df.empty:
        st.warning(f'No data found for "{selected_hood}". Please choose a neighborhood from the Map Explorer.')
        st.markdown('<a href="?auth=1&page=maps" target="_self">← Back to Map Explorer</a>', unsafe_allow_html=True)
        st.stop()

    st.markdown(f"""
        <div class="breadcrumb">
            <a href="?auth=1&page=home">Home</a> &rsaquo;
            <a href="?auth=1&page=maps">Map Explorer</a> &rsaquo;
            <strong>{selected_hood}</strong>
        </div>
    """, unsafe_allow_html=True)
    st.markdown('<a href="?auth=1&page=maps" class="hood-back-link" target="_self">&larr; Back to Map</a>', unsafe_allow_html=True)

    wards_in_hood = sorted(pd.to_numeric(hood_df["ward2025"], errors="coerce").dropna().unique().astype(int).tolist())
    zips_in_hood = sorted(pd.to_numeric(hood_df["zip"], errors="coerce").dropna().unique().astype(int).astype(str).tolist())
    st.markdown(f'<div class="hood-profile-header">{selected_hood}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hood-profile-sub">Ward{"s" if len(wards_in_hood) > 1 else ""} {", ".join(str(w) for w in wards_in_hood)} &nbsp;|&nbsp; ZIP{"s" if len(zips_in_hood) > 1 else ""} {", ".join(str(z) for z in zips_in_hood)}</div>', unsafe_allow_html=True)

    n_total = len(hood_df)

    def _safe_int(val, default=0):
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
            m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles="OpenStreetMap")
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
