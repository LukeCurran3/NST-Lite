"""HTML snippet builders for the property profile grid layouts."""

import streamlit as st


def cell(label, value):
    """Single labeled value cell used inside a grid."""
    return (
        f'<div style="padding:0.75rem;background:#f8f9fc;border-radius:4px;">'
        f'<div style="font-size:0.75rem;color:#888;text-transform:uppercase;letter-spacing:0.04em;margin-bottom:0.2rem;">{label}</div>'
        f'<div style="font-size:1rem;font-weight:600;color:#003071;">{value}</div>'
        f'</div>'
    )


def grid(*cells, cols=3):
    """Wrap any number of cell() strings in a CSS grid."""
    style = f'display:grid;grid-template-columns:repeat({cols},1fr);gap:0.75rem;margin-bottom:1rem;'
    return f'<div style="{style}">{"".join(cells)}</div>'


def section(title):
    """Render a section header with a navy underline."""
    st.markdown(
        f'<div style="font-size:1.15rem;font-weight:600;color:#003071;'
        f'margin:1.5rem 0 0.75rem;padding-bottom:0.35rem;'
        f'border-bottom:2px solid #003071;">{title}</div>',
        unsafe_allow_html=True,
    )
