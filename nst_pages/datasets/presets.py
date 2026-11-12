"""Preset filter buttons (Vacant, Violations, etc). Toggles live in session state."""

import streamlit as st

import styles


PRESET_LABELS = [
    "Vacant Properties",
    "With Violations",
    "Tax Delinquent",
    "Out-of-State Owners",
    "In Foreclosure",
    "Failed Lead Certification",
]


def _preset_key(label):
    """CSS classes can't contain spaces; sanitize for st.button key."""
    return "preset_" + label.replace(" ", "_").replace("-", "_")


def render():
    """Draw the 6 preset buttons and apply active-state styling. Mutates session state."""
    if "ds_presets" not in st.session_state:
        st.session_state.ds_presets = set()

    cols = st.columns(len(PRESET_LABELS))
    for label, col in zip(PRESET_LABELS, cols):
        with col:
            is_active = label in st.session_state.ds_presets
            if st.button(label, use_container_width=True, key=_preset_key(label)):
                if is_active:
                    st.session_state.ds_presets.discard(label)
                else:
                    st.session_state.ds_presets.add(label)
                st.rerun()

    active_keys = [_preset_key(p) for p in st.session_state.ds_presets]
    styles.inject_active_presets(active_keys)


def apply(df):
    """Narrow df by whichever presets are currently toggled on."""
    active = st.session_state.get("ds_presets", set())
    if "Vacant Properties" in active:
        df = df[df["combovac"].fillna(0) == 1]
    if "With Violations" in active:
        df = df[df["violation"].fillna(0) == 1]
    if "Tax Delinquent" in active:
        df = df[df["NET_TAX_DELQ_DUE"].fillna(0) > 0]
    if "Out-of-State Owners" in active:
        df = df[~df["MAIL_STATE"].fillna("").isin(["OH", "/", ""])]
    if "In Foreclosure" in active:
        df = df[df["FORECLOSURE_FLAG"].fillna(0) == 1]
    if "Failed Lead Certification" in active:
        df = df[df["lsc_stat"].fillna("").astype(str).isin(["FAIL", "REVOKED"])]
    return df
