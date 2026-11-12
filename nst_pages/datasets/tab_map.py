"""Map tab. Choropleth above CHOROPLETH_THRESHOLD properties, marker clusters below."""

import pandas as pd
import streamlit as st

from utils.formatting import fmt_money, fmt_text, fmt_year, flag_yn


CHOROPLETH_THRESHOLD = 3000


_METRIC_MAP = {
    "Property Count":   ("count",         "YlOrRd"),
    "Vacancy Rate %":   ("vacancy_pct",   "YlOrRd"),
    "Violation Rate %": ("violation_pct", "YlOrRd"),
    "Avg Market Value": ("avg_value",     "YlGn"),
}

_COLOR_COL = {
    "In Foreclosure": "FORECLOSURE_FLAG",
    "Has Violation":  "violation",
}


@st.cache_data
def _load_hoods():
    import geopandas as gpd
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


def render(filtered_df):
    total = len(filtered_df)
    if total == 0:
        st.info("No properties to display. Adjust your filters.")
        return

    import folium
    from streamlit_folium import st_folium

    gdf_hoods = _load_hoods()

    if total > CHOROPLETH_THRESHOLD:
        _render_choropleth(filtered_df, gdf_hoods, folium, st_folium, total)
    else:
        _render_marker_cluster(filtered_df, gdf_hoods, folium, st_folium, total)


def _render_choropleth(filtered_df, gdf_hoods, folium, st_folium, total):
    metric_label = st.selectbox(
        "Color neighborhoods by",
        list(_METRIC_MAP.keys()),
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
        f"Narrow to ≤ {CHOROPLETH_THRESHOLD:,} to see individual property dots"
    )
    st_folium(m, width=None, height=520, use_container_width=True, returned_objects=[])


def _render_marker_cluster(filtered_df, gdf_hoods, folium, st_folium, total):
    from folium.plugins import MarkerCluster

    color_by = st.selectbox(
        "Color dots by",
        ["Vacant (structure or land)", "In Foreclosure", "Has Violation"],
        key="map_color",
    )
    # Vacant composite: combovac==1 OR classification starts with Vacant Land.
    color_col = _COLOR_COL.get(color_by, "combovac")

    map_cols = list(dict.fromkeys([
        "LATITUDE", "LONGITUDE", "PARCEL", "address", "NEIGHBOR10",
        "CLASSIFICATION_DESCR", "yrbuilt", "condition", "PRIMARY_OWNER_NAME",
        "TAX_MARKET_TOTAL", "NET_TAX_DELQ_DUE",
        "combovac", "FORECLOSURE_FLAG", "violation",
        color_col,
    ]))
    map_df = (
        filtered_df[[c for c in map_cols if c in filtered_df.columns]]
        .dropna(subset=["LATITUDE", "LONGITUDE"])
        .copy()
    )

    if map_df.empty:
        st.info("No properties with coordinates to display.")
        return

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

    is_vacant_mode = color_by.startswith("Vacant")
    for _, row in map_df.iterrows():
        if is_vacant_mode:
            cv = row.get("combovac")
            vs = int(float(cv)) == 1 if pd.notna(cv) else False
            cd = str(row.get("CLASSIFICATION_DESCR") or "")
            vl = cd.startswith("Vacant Land")
            is_flagged = vs or vl
        else:
            is_flagged = int(row.get(color_col, 0) or 0) == 1
        color = "#e03127" if is_flagged else "#003071"
        parcel_id = fmt_text(row.get("PARCEL"), "")
        address   = fmt_text(row.get("address"), "Unknown Address")
        hood      = fmt_text(row.get("NEIGHBOR10"), "")
        val_str   = fmt_money(row.get("TAX_MARKET_TOTAL"))
        delq      = row.get("NET_TAX_DELQ_DUE")
        delq_str  = fmt_money(delq) if pd.notna(delq) and (delq or 0) > 0 else "None"
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
        parcel_js = parcel_id.replace("'", "\\'")
        profile_js = (
            "var t=window.top;"
            f"window.open(t.location.origin+t.location.pathname+"
            f"'?auth=1&page=property-search&parcel={parcel_js}','_blank');"
            "return false;"
        )
        popup_html = f"""
            <div style="font-family:Arial,sans-serif;font-size:12px;min-width:240px;max-width:280px;">
                <div style="font-size:13px;font-weight:700;color:#003071;margin-bottom:2px;">{address}</div>
                <div style="color:#666;margin-bottom:8px;">{hood} &nbsp;·&nbsp; {parcel_id}</div>
                <table style="width:100%;border-collapse:collapse;">
                    <tr><td style="color:#666;padding:2px 0;">Property Type</td><td style="text-align:right;font-weight:600;">{fmt_text(row.get('CLASSIFICATION_DESCR'))}</td></tr>
                    <tr><td style="color:#666;padding:2px 0;">Year Built</td><td style="text-align:right;font-weight:600;">{fmt_year(row.get('yrbuilt'))}</td></tr>
                    <tr><td style="color:#666;padding:2px 0;">Condition</td><td style="text-align:right;font-weight:600;">{fmt_text(row.get('condition'))}</td></tr>
                    <tr><td style="color:#666;padding:2px 0;">Owner</td><td style="text-align:right;font-weight:600;">{fmt_text(row.get('PRIMARY_OWNER_NAME'))}</td></tr>
                    <tr><td style="color:#666;padding:2px 0;">Market Value</td><td style="text-align:right;font-weight:600;">{val_str}</td></tr>
                    <tr><td style="color:#666;padding:2px 0;">Tax Delinquent</td><td style="text-align:right;font-weight:600;color:{'#c0392b' if delq_str != 'None' else '#1e8449'};">{delq_str}</td></tr>
                    <tr><td style="color:#666;padding:2px 0;">Vacant</td><td style="text-align:right;font-weight:600;">{flag_yn(row.get('combovac'))}</td></tr>
                    <tr><td style="color:#666;padding:2px 0;">In Foreclosure</td><td style="text-align:right;font-weight:600;">{flag_yn(row.get('FORECLOSURE_FLAG'))}</td></tr>
                    <tr><td style="color:#666;padding:2px 0;">Has Violation</td><td style="text-align:right;font-weight:600;">{flag_yn(row.get('violation'))}</td></tr>
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
