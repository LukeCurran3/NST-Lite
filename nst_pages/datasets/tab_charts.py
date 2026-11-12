"""Charts tab: four Plotly bar charts (type, neighborhood, condition, region)."""

import streamlit as st

from config import COLOR_NAVY, COLOR_GOLD


def render(filtered_df):
    if len(filtered_df) == 0:
        st.info("No data to chart. Adjust your filters.")
        return

    import plotly.express as px

    ch1, ch2 = st.columns(2)
    with ch1:
        type_counts = filtered_df["CLASSIFICATION_DESCR"].value_counts().head(10)
        df_p = type_counts.reset_index()
        df_p.columns = ["Category", "Count"]
        df_p = df_p.sort_values("Count", ascending=True)
        fig = px.bar(
            df_p, x="Count", y="Category", orientation="h",
            title="Properties by Type (top 10)",
            color_discrete_sequence=[COLOR_NAVY],
        )
        _style_fig(fig, height=320)
        fig.update_traces(hovertemplate="%{y}<br><b>%{x:,}</b><extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": False, "displayModeBar": False})
    with ch2:
        nbh_counts = filtered_df["NEIGHBOR10"].value_counts().head(10).reset_index()
        nbh_counts.columns = ["Neighborhood", "Count"]
        fig2 = px.bar(
            nbh_counts, x="Count", y="Neighborhood", orientation="h",
            title="Properties by Neighborhood (top 10)",
            color_discrete_sequence=[COLOR_GOLD],
        )
        _style_fig(fig2, height=320)
        fig2.update_traces(hovertemplate="%{y}<br><b>%{x:,}</b><extra></extra>")
        st.plotly_chart(fig2, use_container_width=True, config={"scrollZoom": False, "displayModeBar": False})

    ch3, ch4 = st.columns(2)
    with ch3:
        cond_counts = filtered_df["condition"].value_counts().reset_index()
        cond_counts.columns = ["Condition", "Count"]
        fig3 = px.bar(
            cond_counts, x="Condition", y="Count",
            title="Property Condition",
            color_discrete_sequence=[COLOR_NAVY],
        )
        _style_fig(fig3, height=300)
        fig3.update_traces(hovertemplate="%{x}<br><b>%{y:,}</b><extra></extra>")
        st.plotly_chart(fig3, use_container_width=True, config={"scrollZoom": False, "displayModeBar": False})
    with ch4:
        region_counts = filtered_df["cuyregion"].value_counts().reset_index()
        region_counts.columns = ["Region", "Count"]
        fig4 = px.bar(
            region_counts, x="Region", y="Count",
            title="By Cuyahoga Region",
            color_discrete_sequence=[COLOR_GOLD],
        )
        _style_fig(fig4, height=300)
        fig4.update_traces(hovertemplate="%{x}<br><b>%{y:,}</b><extra></extra>")
        st.plotly_chart(fig4, use_container_width=True, config={"scrollZoom": False, "displayModeBar": False})


def _style_fig(fig, height):
    """Shared layout for all four charts: white bg, Inter font, no zoom."""
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white", height=height,
        font=dict(family="Inter, Arial, sans-serif", size=12),
        title_font=dict(size=13, color=COLOR_NAVY),
        margin=dict(l=10, r=20, t=40, b=10),
        xaxis_title="", yaxis_title="",
        xaxis=dict(fixedrange=True),
        yaxis=dict(fixedrange=True),
    )
