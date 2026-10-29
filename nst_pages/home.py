"""Home / landing page."""

import streamlit as st


def render(assets):
    hero_backdrop_base64 = assets["hero_backdrop"]
    partner_cleveland_base64 = assets["partner_cleveland"]
    partner_cuyahoga_base64 = assets["partner_cuyahoga"]
    partner_cclrc_base64 = assets["partner_cclrc"]
    partner_census_base64 = assets["partner_census"]

    st.markdown(f"""
        <div class="hero-section" style="background-image: url('data:image/jpeg;base64,{hero_backdrop_base64}');">
            <div class="hero-overlay"></div>
            <div class="hero-content">
                <div class="hero-subtitle">POVERTY CENTER AT CASE WESTERN RESERVE UNIVERSITY</div>
                <div class="hero-title">CLEVELAND'S<br>NEIGHBORHOOD STRATEGY TECHNOLOGY</div>
                <div class="hero-buttons">
                    <a href="?auth=1&page=datasets" target="_self" class="hero-button">Find Data</a>
                    <a href="?auth=1&page=projects" target="_self" class="hero-button">Popular Projects</a>
                    <a href="https://case.edu/socialwork/povertycenter/about" target="_blank" class="hero-button">Learn More</a>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    ### Welcome to NST!

    The Neighborhood Strategy Technology Web Application (NST) enables a diverse group of
    government and community agencies to collaborate in improving the communities of Cleveland
    and Cuyahoga County. Quickly access information on property ownership, occupancy and vacancy,
    foreclosure, sheriff's sale, and REO history, detailed tax information, code enforcement
    information, demolition information, property surveys conducted by area agencies, and more.
    In addition to linking and making data available, NST also serves as a communication platform
    and place for agencies to house their own data. Users can access, filter, and map data, as
    well as save custom queries and download spreadsheets of data.
    """)

    st.markdown("---")

    st.markdown("""
        <div class="data-section-title">GET STARTED</div>
        <div class="data-cards-container">
            <a href="?auth=1&page=maps" target="_self" class="data-card" style="text-decoration:none;">
                <div class="data-card-title">Map Explorer</div>
                <p style="color: #666; font-size: 1.1rem; margin-top: 1rem;">
                    Visualize neighborhood data on interactive maps
                </p>
            </a>
            <a href="?auth=1&page=datasets" target="_self" class="data-card" style="text-decoration:none;">
                <div class="data-card-title">Browse Data</div>
                <p style="color: #666; font-size: 1.1rem; margin-top: 1rem;">
                    Explore comprehensive datasets and statistics
                </p>
            </a>
            <a href="?auth=1&page=property-search" target="_self" class="data-card" style="text-decoration:none;">
                <div class="data-card-title">Search Properties</div>
                <p style="color: #666; font-size: 1.1rem; margin-top: 1rem;">
                    Find detailed information on specific properties
                </p>
            </a>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown(f"""
        <div class="partners-section-title">OUR DATA PARTNERS</div>
        <div class="partners-grid" style="grid-template-columns: repeat(4, 1fr);">
            <div class="partner-logo">
                <a href="https://clevelandohio.gov" target="_blank" rel="noopener">
                    <img src="data:image/svg+xml;base64,{partner_cleveland_base64}" alt="City of Cleveland" style="max-height:70px;">
                </a>
            </div>
            <div class="partner-logo">
                <a href="https://www.cuyahogacounty.gov/fiscal-officer" target="_blank" rel="noopener">
                    <img src="data:image/svg+xml;base64,{partner_cuyahoga_base64}" alt="Cuyahoga County" style="max-height:70px;">
                </a>
            </div>
            <div class="partner-logo">
                <a href="https://cuyahogalandbank.org" target="_blank" rel="noopener">
                    <img src="data:image/svg+xml;base64,{partner_cclrc_base64}" alt="Cuyahoga Land Bank" style="max-height:70px;">
                </a>
            </div>
            <div class="partner-logo">
                <a href="https://www.census.gov" target="_blank" rel="noopener">
                    <img src="data:image/svg+xml;base64,{partner_census_base64}" alt="U.S. Census Bureau" style="max-height:70px;">
                </a>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="contribute-section">
            <div class="contribute-title">Want to share data through your organization?</div>
            <a href="?auth=1&page=contact" target="_self" class="contribute-button">TALK WITH US</a>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #666; padding: 2rem 0;">
            <p>Powered by CWRU Poverty Center | Last Updated: January 2026</p>
        </div>
    """, unsafe_allow_html=True)
