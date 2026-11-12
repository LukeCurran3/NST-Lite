"""Datasets page orchestrator. Wires filters, summary, tabs, and export together."""

import streamlit as st

from loaders import load_data
import styles

from . import presets, filters, summary, tab_table, tab_map, tab_charts, tab_summary, export


def render():
    df = load_data()

    styles.inject_datasets()

    # Header and breadcrumb
    st.markdown(
        '<div class="breadcrumb"><a href="?auth=1&page=home" target="_self">Home</a> '
        '&nbsp;/&nbsp; <strong>Datasets</strong></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="page-header">Datasets</div>'
        '<div class="page-subtitle">Browse and download comprehensive property data for Cleveland and Cuyahoga County.</div>',
        unsafe_allow_html=True,
    )

    # Preset toggle buttons
    presets.render()

    st.markdown("---")

    # Filter widgets + search input
    search_query, state = filters.render_filters(df)

    # Apply filters, then sort by data completeness
    filtered_df = filters.apply_filters(df, search_query, state)
    filtered_df = filters.sort_by_completeness(filtered_df)

    if state["neighborhood"] != "Cleveland (City)":
        st.warning(
            "Violation data is only available for City of Cleveland properties. "
            "Results outside Cleveland may be incomplete."
        )

    st.markdown("---")

    # Active filter recap, then the big KPI tiles
    summary.render_summary_line(state)
    summary.render_stat_boxes(filtered_df)

    st.markdown("")

    # Column selector feeds both the table tab and the export buttons
    display_columns = tab_table.render_column_customizer(df)

    t_table, t_map, t_charts, t_summary = st.tabs(["Table View", "Map View", "Charts", "Summary"])
    with t_table:
        tab_table.render(filtered_df, display_columns)
    with t_map:
        tab_map.render(filtered_df)
    with t_charts:
        tab_charts.render(filtered_df)
    with t_summary:
        tab_summary.render(filtered_df)

    st.markdown("---")
    export.render(filtered_df, display_columns)

    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: #666; padding: 2rem 0;">'
        '<p>Powered by CWRU Poverty Center | Last Updated: November 2026</p>'
        '</div>',
        unsafe_allow_html=True,
    )
