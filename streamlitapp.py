"""NST 2.0: Cleveland Neighborhood Strategy Technology. Entry point: auth, navbar, routing."""

import base64

import streamlit as st

from config import SITE_PASSWORD
from nst_pages import (
    home, datasets, maps, property_search, neighborhood,
    distressed_rentals, methodology, projects, contact, oos_owners,
)


def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


# Must be the first st call.
st.set_page_config(
    page_title="Cleveland NST 2.0",
    page_icon="assets/updated_nst_favicon.svg",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def check_password():
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


if not check_password():
    st.stop()


ASSETS = {
    "navbar_logo": get_base64_image("assets/upperleft logo.jpg"),
    "hero_backdrop": get_base64_image("assets/cleveland backdrop.jpg"),
    "partner_cleveland": get_base64_image("assets/partner_cleveland.svg"),
    "partner_cuyahoga": get_base64_image("assets/updated_Cuyahoga_County_logo.svg"),
    "partner_cclrc": get_base64_image("assets/partner_cclrc.svg"),
    "partner_census": get_base64_image("assets/partner_census.svg"),
}

query_params = st.query_params
current_page = query_params.get("page", "home")


st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    /* Negative margins break out of Streamlit's container padding. */
    .navbar {
        background-color: white;
        padding: 0;
        margin: 0;
        margin-top: -80px;
        margin-left: -100px;
        margin-right: -100px;
        border-bottom: 2px solid #000000;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .navbar-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 3rem;
    }
    .navbar-brand {
        display: flex;
        align-items: center;
    }
    .navbar-brand img {
        height: 80px;
        width: auto;
    }
    .navbar-menu {
        display: flex;
        list-style: none;
        margin: 0;
        padding: 0;
        gap: 2rem;
        align-items: center;
    }
    .navbar-item {
        position: relative;
        display: inline-block;
    }
    .navbar-link {
        color: #003071;
        text-decoration: none !important;
        padding: 1rem 0;
        display: inline-block;
        font-size: 1.4rem;
        font-weight: 600;
        transition: color 0.2s;
        cursor: pointer;
    }
    .navbar-link:link, .navbar-link:visited, .navbar-link:active {
        text-decoration: none !important;
    }
    .navbar-link:hover {
        color: #003071;
    }
    .navbar-link::after {
        content: " ▼";
        font-size: 0.7rem;
        margin-left: 0.4rem;
    }
    .navbar-link-home::after {
        content: none;
    }
    .dropdown-menu {
        display: none;
        position: fixed;
        background-color: white;
        width: 100vw;
        left: 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border-top: 2px solid #000000;
        z-index: 1001;
        padding: 3rem 6rem;
    }
    .navbar-item:hover .dropdown-menu {
        display: block;
    }
    .dropdown-item {
        color: #003071 !important;
        padding: 1.5rem 0;
        text-decoration: none !important;
        display: block;
        transition: all 0.2s;
        border-bottom: 1px solid #e0e0e0;
    }
    .dropdown-item:last-child {
        border-bottom: none;
    }
    .dropdown-item:hover {
        padding-left: 0.5rem;
    }
    .dropdown-item-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: #003071;
        margin-bottom: 0.3rem;
    }
    .dropdown-item-description {
        font-size: 1rem;
        font-weight: 400;
        color: #666;
        line-height: 1.4;
    }
    .dropdown-item:hover .dropdown-item-title {
        color: #FFD700;
    }

    .hero-section {
        position: relative;
        width: calc(100% + 200px);
        margin-left: -100px;
        margin-right: -100px;
        margin-top: 0;
        height: 500px;
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
    }
    .hero-overlay {
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0, 48, 113, 0.6);
    }
    .hero-content {
        position: relative;
        z-index: 1;
        color: white;
        padding: 2rem;
    }
    .hero-subtitle {
        font-size: 1.5rem;
        font-weight: 600;
        letter-spacing: 3px;
        margin-bottom: 1rem;
        color: #FFD700;
    }
    .hero-title {
        font-size: 4rem;
        font-weight: 700;
        line-height: 1.2;
        margin-bottom: 2rem;
        text-transform: uppercase;
    }
    .hero-buttons {
        display: flex;
        gap: 2rem;
        justify-content: center;
        margin-top: 2rem;
    }
    .hero-button {
        padding: 1rem 2.5rem;
        border: 2px solid white;
        background-color: transparent;
        color: white !important;
        font-size: 1.3rem;
        font-weight: 600;
        text-decoration: none !important;
        transition: all 0.3s;
        cursor: pointer;
    }
    .hero-button:hover {
        background-color: white;
        color: #003071;
    }

    .data-section-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        color: #003071;
        margin: 3rem 0 2rem 0;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .data-cards-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 2rem;
        margin: 2rem 0;
    }
    .data-card {
        background-color: white;
        border: 2px solid #003071;
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
        transition: transform 0.3s, box-shadow 0.3s;
    }
    .data-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0,48,113,0.2);
    }
    .data-card-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        color: #003071;
    }
    .data-card-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #003071;
        margin-bottom: 1.5rem;
        text-transform: uppercase;
    }
    .data-card-links {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    .data-card-link {
        padding: 0.5rem 0;
        border-bottom: 1px solid #e0e0e0;
    }
    .data-card-link:last-child {
        border-bottom: none;
    }
    .data-card-link a {
        color: #003071;
        text-decoration: none;
        font-weight: 500;
        transition: color 0.2s;
    }
    .data-card-link a:hover {
        color: #FFD700;
    }

    .partners-section-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        color: #003071;
        margin: 3rem 0 3rem 0;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .partners-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 3rem;
        margin: 3rem auto;
        max-width: 1400px;
        align-items: center;
    }
    .partner-logo {
        background-color: transparent;
        padding: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100px;
        transition: transform 0.3s;
    }
    .partner-logo:hover {
        transform: scale(1.05);
    }
    .partner-logo img {
        max-width: 100%;
        max-height: 80px;
        object-fit: contain;
    }

    .contribute-section {
        background-color: #f5f5f5;
        padding: 4rem 3rem;
        text-align: center;
        margin: 4rem 0;
    }
    .contribute-title {
        font-size: 1.8rem;
        font-weight: 500;
        color: #333;
        margin-bottom: 2rem;
        font-family: 'Inter', sans-serif;
    }
    .contribute-button {
        display: inline-block;
        padding: 1rem 2.5rem;
        background-color: #FFD700;
        color: #003071 !important;
        font-size: 1.2rem;
        font-weight: 700;
        text-decoration: none !important;
        border: 2px solid #333;
        transition: all 0.3s;
        cursor: pointer;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .contribute-button:hover {
        background-color: #FFC700;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }

    .main .block-container {
        padding-top: 0rem;
    }
    .main-header {
        text-align: center;
        padding: 2rem 0;
    }
    .main-title {
        font-size: 3.5rem;
        font-weight: bold;
        color: #003071;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.5rem;
        color: #666;
        margin-bottom: 3rem;
    }
    .nav-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
        padding: 2rem 0;
    }
    .stButton > button {
        width: 100%;
        height: 150px;
        font-size: 1.5rem;
        font-weight: bold;
        border-radius: 10px;
        border: 2px solid #003071;
        background-color: white;
        color: #003071;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #003071;
        color: white;
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    </style>
""", unsafe_allow_html=True)


st.markdown(f"""
    <div class="navbar">
        <div class="navbar-container">
            <div class="navbar-brand">
                <a href="?auth=1&page=home" target="_self"><img src="data:image/jpeg;base64,{ASSETS['navbar_logo']}" alt="Cleveland NST Logo"></a>
            </div>
            <ul class="navbar-menu">
                <li class="navbar-item">
                    <a href="?auth=1&page=home" target="_self" class="navbar-link navbar-link-home">Home</a>
                </li>
                <li class="navbar-item">
                    <a href="#" class="navbar-link">Data</a>
                    <div class="dropdown-menu">
                        <a href="?auth=1&page=datasets" target="_self" class="dropdown-item">
                            <div class="dropdown-item-title">Datasets</div>
                            <div class="dropdown-item-description">Browse and download comprehensive neighborhood data</div>
                        </a>
                        <a href="?auth=1&page=maps" target="_self" class="dropdown-item">
                            <div class="dropdown-item-title">Interactive Maps</div>
                            <div class="dropdown-item-description">Visualize Cleveland data on interactive maps</div>
                        </a>
                        <a href="?auth=1&page=property-search" target="_self" class="dropdown-item">
                            <div class="dropdown-item-title">Property Search</div>
                            <div class="dropdown-item-description">Look up detailed information for a specific address or parcel</div>
                        </a>
                    </div>
                </li>
                <li class="navbar-item">
                    <a href="#" class="navbar-link">Our Work</a>
                    <div class="dropdown-menu">
                        <a href="https://case.edu/socialwork/povertycenter/about" target="_blank" class="dropdown-item">
                            <div class="dropdown-item-title">About</div>
                            <div class="dropdown-item-description">Learn about NST and our mission</div>
                        </a>
                        <a href="?auth=1&page=methodology" target="_self" class="dropdown-item">
                            <div class="dropdown-item-title">Methodology</div>
                            <div class="dropdown-item-description">Our data collection and analysis approach</div>
                        </a>
                        <a href="?auth=1&page=projects" target="_self" class="dropdown-item">
                            <div class="dropdown-item-title">Projects</div>
                            <div class="dropdown-item-description">Dedicated pages for each of our projects</div>
                        </a>
                    </div>
                </li>
                <li class="navbar-item">
                    <a href="#" class="navbar-link">Resources</a>
                    <div class="dropdown-menu">
                        <a href="?auth=1&page=resources" target="_self" class="dropdown-item">
                            <div class="dropdown-item-title">Resources</div>
                            <div class="dropdown-item-description">Tools and guides for using NST data</div>
                        </a>
                        <a href="?auth=1&page=contact" target="_self" class="dropdown-item">
                            <div class="dropdown-item-title">Contact</div>
                            <div class="dropdown-item-description">How to reach us or work with us</div>
                        </a>
                    </div>
                </li>
            </ul>
        </div>
    </div>
""", unsafe_allow_html=True)


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
