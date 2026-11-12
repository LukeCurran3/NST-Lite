"""NST 2.0 entry point. Sets up page config, auth, styles, navbar, then routes."""

import streamlit as st

import auth
import navbar
import styles
from nst_pages import (
    home, datasets, maps, property_search, neighborhood,
    distressed_rentals, methodology, projects, contact, oos_owners,
)


# Must be the first st call.
st.set_page_config(
    page_title="Cleveland NST 2.0",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if not auth.check_password():
    st.stop()

ASSETS = navbar.load_assets()

styles.inject_global()
navbar.render(ASSETS)


# Route by ?page= query param. Add new pages here plus a link in navbar.py.
query_params = st.query_params
current_page = query_params.get("page", "home")

if current_page == "datasets":
    datasets.render()
elif current_page == "maps":
    maps.render()
elif current_page == "property-search":
    property_search.render()
elif current_page == "neighborhood":
    neighborhood.render(query_params.get("hood", None))
elif current_page == "methodology":
    methodology.render()
elif current_page == "contact":
    contact.render()
elif current_page == "projects":
    projects.render()
elif current_page == "oos-owners":
    oos_owners.render()
elif current_page == "distressed-rentals":
    distressed_rentals.render()
else:
    home.render(ASSETS)
