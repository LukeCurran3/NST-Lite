"""Password gate. Grants access once per session or whenever ?auth=1 is on the URL."""

import streamlit as st

from config import SITE_PASSWORD


def check_password():
    """Returns True if the session is authenticated. Otherwise shows the login UI."""
    if st.query_params.get("auth") == "1":
        return True

    def password_entered():
        if st.session_state["password"] == SITE_PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            params = dict(st.query_params)
            params["auth"] = "1"
            st.query_params.update(params)
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct"):
        return True

    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("Password incorrect")
    return False
