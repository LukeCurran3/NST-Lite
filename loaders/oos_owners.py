"""Loader for the Out-of-State Owners page sample dataset."""

import pandas as pd
import streamlit as st


@st.cache_data
def load_oos_data():
    return pd.read_csv("data/nstsample.csv", low_memory=False)
