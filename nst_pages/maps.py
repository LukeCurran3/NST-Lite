"""Map Explorer page: Cuyahoga County neighborhood overview."""

import folium
from streamlit_folium import st_folium
import streamlit as st

from loaders import load_neighborhoods, load_map_agg
import styles


def render():
    df_map = load_map_agg()
    gdf_hoods = load_neighborhoods()
    _agg_by_name  = {r["NEIGHBOR10"]: r for _, r in df_map.iterrows()}
    _hoods_w_data = set(df_map["NEIGHBOR10"].dropna())
    _max_count    = int(df_map["count"].max()) if len(df_map) > 0 else 1

    styles.inject_maps()

    st.markdown("""
        <div class="breadcrumb">
            <a href="?auth=1&page=home" target="_self">Home</a> &nbsp;/&nbsp; <strong>Map Explorer</strong>
        </div>
    """, unsafe_allow_html=True)

    panel_col, map_col = st.columns([1, 2.5])

    with panel_col:
        st.markdown('<div class="map-page-header" style="font-size:1.6rem;">Map Explorer</div>', unsafe_allow_html=True)
        st.markdown('<div class="map-page-subtitle" style="font-size:0.95rem;">Cuyahoga County: click any neighborhood to view its profile.</div>', unsafe_allow_html=True)

        neighborhoods = df_map["NEIGHBOR10"].tolist()
        selected_from_dropdown = st.selectbox(
            "Jump to neighborhood",
            [""] + neighborhoods,
            key="map_hood_select",
            format_func=lambda x: "Choose a neighborhood..." if x == "" else x,
        )
        if selected_from_dropdown:
            st.query_params["page"] = "neighborhood"
            st.query_params["hood"] = selected_from_dropdown
            st.rerun()

        st.markdown("---")

        st.markdown("**All Neighborhoods**")
        hood_list_html = ""
        for _, row in df_map.iterrows():
            hood_name = row["NEIGHBOR10"]
            count = int(row["count"])
            vac = row["vacancy_pct"]
            hood_list_html += (
                f'<a href="?auth=1&page=neighborhood&hood={hood_name}" target="_self" class="hood-list-item">'
                f'{hood_name}'
                f'<span class="hood-list-item-count">{count:,} &nbsp;·&nbsp; {vac:.0f}% vac</span>'
                f'</a>'
            )
        st.markdown(
            f'<div style="max-height:450px;overflow-y:auto;border:1px solid #e0e0e0;border-radius:6px;">'
            f'{hood_list_html}</div>',
            unsafe_allow_html=True,
        )

    with map_col:
        def _count_color(count):
            ratio = min(count / _max_count, 1.0) if _max_count > 0 else 0
            r = int(222 + (0   - 222) * ratio)
            g = int(234 + (48  - 234) * ratio)
            b = int(255 + (113 - 255) * ratio)
            return f"#{r:02x}{g:02x}{b:02x}"

        m = folium.Map(location=[41.4993, -81.6944], zoom_start=11, tiles="OpenStreetMap")

        for _, row in gdf_hoods.iterrows():
            raw_name  = row["NEIGHBOR20"]
            name_key  = row["name_key"]
            hood_data = _agg_by_name.get(name_key)
            has_data  = hood_data is not None

            if has_data:
                count      = int(hood_data["count"])
                vac        = hood_data["vacancy_pct"]
                avg_val    = hood_data["avg_value"]
                fill_color = _count_color(count)
                fill_opacity  = 0.6
                border_color  = "#003071"
                border_weight = 1.5
                val_str = f"${int(avg_val):,}" if avg_val and avg_val > 0 else "N/A"
                tooltip_text = (
                    f"{raw_name}: {count:,} properties · "
                    f"{vac:.1f}% vacant · avg {val_str}"
                )
            else:
                fill_color    = "#e0e0e0"
                fill_opacity  = 0.3
                border_color  = "#aaaaaa"
                border_weight = 1
                tooltip_text  = raw_name

            folium.GeoJson(
                data=row.geometry.__geo_interface__,
                style_function=lambda x, fc=fill_color, fo=fill_opacity, bc=border_color, bw=border_weight: {
                    "fillColor": fc, "color": bc, "weight": bw, "fillOpacity": fo,
                },
                highlight_function=lambda x: {
                    "weight": 3, "color": "#FFD700", "fillOpacity": 0.8,
                },
                tooltip=tooltip_text,
                name=raw_name,
            ).add_to(m)

        map_data = st_folium(m, width=None, height=650, use_container_width=True)

        # Point-in-polygon on last_clicked; st_folium's tooltip return is unreliable.
        if "last_map_click" not in st.session_state:
            st.session_state["last_map_click"] = None

        if map_data:
            click = map_data.get("last_clicked")
            if click and isinstance(click, dict):
                lat = click.get("lat")
                lng = click.get("lng")
                if lat is not None and lng is not None:
                    click_key = f"{lat:.6f},{lng:.6f}"
                    if click_key != st.session_state.get("last_map_click"):
                        st.session_state["last_map_click"] = click_key
                        from shapely.geometry import Point
                        pt = Point(lng, lat)
                        match = gdf_hoods[gdf_hoods.geometry.contains(pt)]
                        if not match.empty:
                            clicked_key = match.iloc[0]["name_key"]
                            if clicked_key in _hoods_w_data:
                                st.query_params.update({"auth": "1", "page": "neighborhood", "hood": clicked_key})
                                st.rerun()

    st.markdown("---")
    st.caption(
        f"Data from Cuyahoga County: "
        f"{int(df_map['count'].sum()):,} parcels across {len(df_map):,} neighborhoods · CWRU Poverty Center"
    )
