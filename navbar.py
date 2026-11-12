"""Top navbar: loads logo assets once and emits the markup every page uses."""

import base64

import streamlit as st


def _b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


@st.cache_data
def load_assets():
    """Base64-encoded images shared across pages. Cached so file reads happen once."""
    return {
        "navbar_logo": _b64("assets/upperleft logo.jpg"),
        "hero_backdrop": _b64("assets/cleveland backdrop.jpg"),
        "partner_cleveland": _b64("assets/partner_cleveland.svg"),
        "partner_cuyahoga": _b64("assets/updated_Cuyahoga_County_logo.svg"),
        "partner_cclrc": _b64("assets/partner_cclrc.svg"),
        "partner_census": _b64("assets/partner_census.svg"),
    }


def render(assets):
    """Render the fixed navbar. Call after styles.inject_global()."""
    st.markdown(f"""
        <div class="navbar">
            <div class="navbar-container">
                <div class="navbar-brand">
                    <a href="?auth=1&page=home" target="_self"><img src="data:image/jpeg;base64,{assets['navbar_logo']}" alt="Cleveland NST Logo"></a>
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
