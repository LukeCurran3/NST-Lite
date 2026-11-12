"""Central CSS for every page. Colors and theme tokens come from config.

Pages should call `styles.inject_X()` instead of defining their own <style> blocks.
`inject_global()` is called once from streamlitapp.py and loads shared styles for
every page: fonts, navbar, breadcrumb, page header, stat boxes, tabs, buttons.
"""

import streamlit as st

from config import COLOR_NAVY, COLOR_GOLD, COLOR_LIGHT_GRAY


# Shared styles loaded on every page
def _global_css():
    return f"""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif !important;
    }}

    /* Negative margins break out of Streamlit's container padding. */
    .navbar {{
        background-color: white;
        padding: 0;
        margin: 0;
        margin-top: -80px;
        margin-left: -100px;
        margin-right: -100px;
        border-bottom: 2px solid #000000;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    .navbar-container {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 3rem;
    }}
    .navbar-brand {{ display: flex; align-items: center; }}
    .navbar-brand img {{ height: 80px; width: auto; }}
    .navbar-menu {{
        display: flex;
        list-style: none;
        margin: 0;
        padding: 0;
        gap: 2rem;
        align-items: center;
    }}
    .navbar-item {{ position: relative; display: inline-block; }}
    .navbar-link {{
        color: {COLOR_NAVY};
        text-decoration: none !important;
        padding: 1rem 0;
        display: inline-block;
        font-size: 1.4rem;
        font-weight: 600;
        transition: color 0.2s;
        cursor: pointer;
    }}
    .navbar-link:link, .navbar-link:visited, .navbar-link:active {{ text-decoration: none !important; }}
    .navbar-link:hover {{ color: {COLOR_NAVY}; }}
    .navbar-link::after {{ content: " ▼"; font-size: 0.7rem; margin-left: 0.4rem; }}
    .navbar-link-home::after {{ content: none; }}
    .dropdown-menu {{
        display: none;
        position: fixed;
        background-color: white;
        width: 100vw;
        left: 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border-top: 2px solid #000000;
        z-index: 1001;
        padding: 3rem 6rem;
    }}
    .navbar-item:hover .dropdown-menu {{ display: block; }}
    .dropdown-item {{
        color: {COLOR_NAVY} !important;
        padding: 1.5rem 0;
        text-decoration: none !important;
        display: block;
        transition: all 0.2s;
        border-bottom: 1px solid #e0e0e0;
    }}
    .dropdown-item:last-child {{ border-bottom: none; }}
    .dropdown-item:hover {{ padding-left: 0.5rem; }}
    .dropdown-item-title {{
        font-size: 1.4rem;
        font-weight: 600;
        color: {COLOR_NAVY};
        margin-bottom: 0.3rem;
    }}
    .dropdown-item-description {{
        font-size: 1rem;
        font-weight: 400;
        color: #666;
        line-height: 1.4;
    }}
    .dropdown-item:hover .dropdown-item-title {{ color: {COLOR_GOLD}; }}

    /* Shared page chrome: used across every page */
    .breadcrumb {{ font-size: 0.95rem; color: #666; margin-bottom: 1.5rem; }}
    .breadcrumb a {{ color: {COLOR_NAVY}; text-decoration: none; }}
    .breadcrumb a:hover {{ text-decoration: underline; }}
    .page-header {{ font-size: 2.5rem; font-weight: 700; color: {COLOR_NAVY}; margin-bottom: 0.3rem; }}
    .page-subtitle {{ font-size: 1.1rem; color: #666; margin-bottom: 1rem; }}

    .stat-box {{ background: {COLOR_LIGHT_GRAY}; border-left: 4px solid {COLOR_NAVY}; padding: 1rem 1.2rem; border-radius: 4px; }}
    .stat-box .stat-value {{ font-size: 1.6rem; font-weight: 700; color: {COLOR_NAVY}; }}
    .stat-box .stat-label {{ font-size: 0.85rem; color: #666; }}

    .main .block-container {{ padding-top: 0rem; }}

    /* Default button styling used on home page nav cards */
    .stButton > button {{
        width: 100%;
        height: 150px;
        font-size: 1.5rem;
        font-weight: bold;
        border-radius: 10px;
        border: 2px solid {COLOR_NAVY};
        background-color: white;
        color: {COLOR_NAVY};
        transition: all 0.3s;
    }}
    .stButton > button:hover {{
        background-color: {COLOR_NAVY};
        color: white;
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }}

    /* Tabs: full-width, equal sizing, larger text */
    .stTabs [data-baseweb="tab-list"] {{ gap: 0; width: 100%; }}
    .stTabs [data-baseweb="tab"] {{
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        flex: 1 1 0 !important;
        justify-content: center !important;
        padding: 0.75rem 0.5rem !important;
    }}
    </style>"""


# Home page specific
def _home_css():
    return f"""<style>
    .hero-section {{
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
    }}
    .hero-overlay {{
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0, 48, 113, 0.6);
    }}
    .hero-content {{ position: relative; z-index: 1; color: white; padding: 2rem; }}
    .hero-subtitle {{
        font-size: 1.5rem;
        font-weight: 600;
        letter-spacing: 3px;
        margin-bottom: 1rem;
        color: {COLOR_GOLD};
    }}
    .hero-title {{
        font-size: 4rem;
        font-weight: 700;
        line-height: 1.2;
        margin-bottom: 2rem;
        text-transform: uppercase;
    }}
    .hero-buttons {{ display: flex; gap: 2rem; justify-content: center; margin-top: 2rem; }}
    .hero-button {{
        padding: 1rem 2.5rem;
        border: 2px solid white;
        background-color: transparent;
        color: white !important;
        font-size: 1.3rem;
        font-weight: 600;
        text-decoration: none !important;
        transition: all 0.3s;
        cursor: pointer;
    }}
    .hero-button:hover {{ background-color: white; color: {COLOR_NAVY} !important; }}

    .data-section-title {{
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        color: {COLOR_NAVY};
        margin: 3rem 0 2rem 0;
        text-transform: uppercase;
        letter-spacing: 2px;
    }}
    .data-cards-container {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 2rem;
        margin: 2rem 0;
    }}
    .data-card {{
        background-color: white;
        border: 2px solid {COLOR_NAVY};
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
        transition: transform 0.3s, box-shadow 0.3s;
    }}
    .data-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0,48,113,0.2);
    }}
    .data-card-icon {{ font-size: 4rem; margin-bottom: 1rem; color: {COLOR_NAVY}; }}
    .data-card-title {{
        font-size: 1.5rem;
        font-weight: 700;
        color: {COLOR_NAVY};
        margin-bottom: 1.5rem;
        text-transform: uppercase;
    }}
    .data-card-links {{ list-style: none; padding: 0; margin: 0; }}
    .data-card-link {{ padding: 0.5rem 0; border-bottom: 1px solid #e0e0e0; }}
    .data-card-link:last-child {{ border-bottom: none; }}
    .data-card-link a {{ color: {COLOR_NAVY}; text-decoration: none; font-weight: 500; transition: color 0.2s; }}
    .data-card-link a:hover {{ color: {COLOR_GOLD}; }}

    .partners-section-title {{
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        color: {COLOR_NAVY};
        margin: 3rem 0 3rem 0;
        text-transform: uppercase;
        letter-spacing: 2px;
    }}
    .partners-grid {{
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 3rem;
        margin: 3rem auto;
        max-width: 1400px;
        align-items: center;
    }}
    .partner-logo {{
        background-color: transparent;
        padding: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100px;
        transition: transform 0.3s;
    }}
    .partner-logo:hover {{ transform: scale(1.05); }}
    .partner-logo img {{ max-width: 100%; max-height: 80px; object-fit: contain; }}

    .contribute-section {{
        background-color: #f5f5f5;
        padding: 4rem 3rem;
        text-align: center;
        margin: 4rem 0;
    }}
    .contribute-title {{
        font-size: 1.8rem;
        font-weight: 500;
        color: #333;
        margin-bottom: 2rem;
        font-family: 'Inter', sans-serif;
    }}
    .contribute-button {{
        display: inline-block;
        padding: 1rem 2.5rem;
        background-color: {COLOR_GOLD};
        color: {COLOR_NAVY} !important;
        font-size: 1.2rem;
        font-weight: 700;
        text-decoration: none !important;
        border: 2px solid #333;
        transition: all 0.3s;
        cursor: pointer;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .contribute-button:hover {{
        background-color: #FFC700;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }}

    .main-header {{ text-align: center; padding: 2rem 0; }}
    .main-title {{
        font-size: 3.5rem;
        font-weight: bold;
        color: {COLOR_NAVY};
        margin-bottom: 0.5rem;
    }}
    .subtitle {{ font-size: 1.5rem; color: #666; margin-bottom: 3rem; }}
    .nav-container {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
        padding: 2rem 0;
    }}
    </style>"""


# Datasets page specific
def _datasets_css():
    return f"""<style>
    [class*="st-key-preset_"] button {{
        min-height: 6rem !important;
        height: auto !important;
        white-space: normal !important;
    }}
    [class*="st-key-preset_"] button p {{
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        line-height: 1.4 !important;
        white-space: normal !important;
    }}
    </style>"""


def active_presets_css(active_keys):
    """Dynamic styling for the currently toggled preset buttons."""
    if not active_keys:
        return ""
    selectors = ", ".join(f".st-key-{k} button" for k in active_keys)
    text_selectors = ", ".join(f".st-key-{k} button p" for k in active_keys)
    return f"""<style>
    {selectors} {{
        background-color: {COLOR_NAVY} !important;
        border: 3px solid {COLOR_GOLD} !important;
        box-shadow: 0 4px 12px rgba(0,48,113,0.3) !important;
    }}
    {text_selectors} {{ color: white !important; }}
    </style>"""


# Property search page specific
def _property_search_css():
    return f"""<style>
    .ps-header {{ font-size:2rem;font-weight:700;color:{COLOR_NAVY};margin-bottom:0.15rem; }}
    .ps-meta   {{ font-size:0.9rem;color:#888;margin-bottom:1.2rem; }}
    .kpi-val   {{ font-size:1.5rem;font-weight:700;color:{COLOR_NAVY}; }}
    .kpi-lbl   {{ font-size:0.8rem;color:#666; }}
    </style>"""


# Maps page specific (sidebar + profile cards)
def _maps_css():
    return f"""<style>
    .map-page-header {{
        font-size: 2.5rem;
        font-weight: 700;
        color: {COLOR_NAVY};
        margin-bottom: 0.3rem;
    }}
    .map-page-subtitle {{ font-size: 1.1rem; color: #666; margin-bottom: 1rem; }}
    .map-sidebar-prompt {{
        background: #f0f4fa;
        border: 2px dashed {COLOR_NAVY};
        border-radius: 8px;
        padding: 2rem 1.5rem;
        text-align: center;
        margin: 1rem 0;
    }}
    .map-sidebar-prompt-icon {{ font-size: 2.5rem; margin-bottom: 0.5rem; }}
    .map-sidebar-prompt-text {{
        font-size: 1.1rem;
        font-weight: 600;
        color: {COLOR_NAVY};
    }}
    .hood-list-item {{
        display: block;
        padding: 0.7rem 1rem;
        border-bottom: 1px solid #e8e8e8;
        color: {COLOR_NAVY} !important;
        text-decoration: none !important;
        font-weight: 500;
        font-size: 1rem;
        transition: background 0.2s, padding-left 0.2s;
    }}
    .hood-list-item:hover {{ background: #f0f4fa; padding-left: 1.4rem; }}
    .hood-list-item-count {{
        float: right;
        color: #999;
        font-weight: 400;
        font-size: 0.9rem;
    }}
    {_hood_profile_shared_css()}
    </style>"""


def _hood_profile_shared_css():
    """Neighborhood profile styles reused by both maps.py and neighborhood.py."""
    return f"""
    .hood-profile-header {{
        font-size: 2.2rem;
        font-weight: 700;
        color: {COLOR_NAVY};
        margin-bottom: 0.2rem;
    }}
    .hood-profile-sub {{ font-size: 1rem; color: #666; margin-bottom: 1.5rem; }}
    .hood-stat-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }}
    .hood-stat-card {{
        background: {COLOR_LIGHT_GRAY};
        border-left: 4px solid {COLOR_NAVY};
        padding: 1rem 1.2rem;
        border-radius: 4px;
    }}
    .hood-stat-card-value {{ font-size: 1.6rem; font-weight: 700; color: {COLOR_NAVY}; }}
    .hood-stat-card-label {{ font-size: 0.85rem; color: #666; }}
    .hood-section-title {{
        font-size: 1.3rem;
        font-weight: 600;
        color: {COLOR_NAVY};
        margin: 1.5rem 0 0.8rem 0;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid {COLOR_NAVY};
    }}
    .hood-back-link {{
        display: inline-block;
        color: {COLOR_NAVY} !important;
        text-decoration: none !important;
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 1rem;
        padding: 0.4rem 0;
    }}
    .hood-back-link:hover {{ color: {COLOR_GOLD} !important; }}
    """


def _neighborhood_css():
    return f"""<style>
    {_hood_profile_shared_css()}
    </style>"""


# Projects hub page specific
def _projects_css():
    return f"""<style>
    .project-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 2rem;
        margin-top: 1.5rem;
    }}
    .project-card {{
        background: white;
        border: 1px solid #e0e0e0;
        border-top: 4px solid {COLOR_NAVY};
        border-radius: 6px;
        padding: 2rem;
        text-decoration: none !important;
        color: inherit;
        display: block;
        transition: box-shadow 0.2s, transform 0.15s;
    }}
    .project-card:hover {{
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }}
    .project-card-coming {{
        background: {COLOR_LIGHT_GRAY};
        border: 1px solid #e0e0e0;
        border-top: 4px solid #ccc;
        border-radius: 6px;
        padding: 2rem;
        opacity: 0.6;
    }}
    .project-card-tag {{
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 600;
        color: {COLOR_NAVY};
        background: #eef2fa;
        border-radius: 20px;
        padding: 0.25rem 0.75rem;
        margin-top: 1rem;
        letter-spacing: 0.04em;
    }}
    .project-card-title {{
        font-size: 1.25rem;
        font-weight: 700;
        color: {COLOR_NAVY};
        margin-bottom: 0.75rem;
    }}
    .project-card-coming .project-card-title {{ color: #999; }}
    .project-card-desc {{ font-size: 0.95rem; color: #555; line-height: 1.6; }}
    .project-card-coming .project-card-desc {{ color: #bbb; }}
    .coming-label {{
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 600;
        color: #999;
        background: #e8e8e8;
        border-radius: 20px;
        padding: 0.25rem 0.75rem;
        margin-top: 1rem;
        letter-spacing: 0.04em;
    }}
    .page-subtitle {{ margin-bottom: 2rem; }}
    </style>"""


# Contact page specific
def _contact_css():
    return f"""<style>
    .contact-card {{
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 2rem;
        margin-bottom: 1.5rem;
    }}
    .contact-card-title {{
        font-size: 1.1rem;
        font-weight: 700;
        color: {COLOR_NAVY};
        text-transform: uppercase;
        letter-spacing: 1px;
        border-bottom: 2px solid {COLOR_GOLD};
        padding-bottom: 0.5rem;
        margin-bottom: 1.2rem;
    }}
    .contact-org {{
        font-size: 1rem;
        font-weight: 700;
        color: {COLOR_NAVY};
        margin-bottom: 0.2rem;
    }}
    .contact-school {{
        font-size: 0.9rem;
        color: #444;
        font-style: italic;
        margin-bottom: 0.15rem;
    }}
    .contact-univ {{
        font-size: 0.9rem;
        color: #444;
        margin-bottom: 0.15rem;
    }}
    .contact-addr {{
        font-size: 0.9rem;
        color: #555;
        line-height: 1.6;
        margin-bottom: 0.8rem;
    }}
    .contact-detail {{
        font-size: 0.9rem;
        color: #555;
        margin-bottom: 0.2rem;
    }}
    .contact-detail a {{ color: {COLOR_NAVY}; text-decoration: none; }}
    .contact-detail a:hover {{ text-decoration: underline; }}
    .contact-link-btn {{
        display: inline-block;
        margin-top: 1rem;
        padding: 0.6rem 1.4rem;
        background: {COLOR_NAVY};
        color: white !important;
        border-radius: 4px;
        font-size: 0.9rem;
        font-weight: 600;
        text-decoration: none;
        letter-spacing: 0.5px;
    }}
    .contact-link-btn:hover {{ background: #00245a; text-decoration: none !important; }}
    .contact-link-btn.gold {{ background: {COLOR_GOLD}; color: {COLOR_NAVY} !important; }}
    .contact-link-btn.gold:hover {{ background: #e6c200; }}
    .page-subtitle {{ margin-bottom: 2rem; }}
    </style>"""


# Out-of-state owners page specific
def _oos_owners_css():
    return f"""<style>
    .breadcrumb {{ margin-bottom: 1rem; }}

    .oos-hero {{
        background: {COLOR_NAVY};
        border-radius: 8px;
        padding: 2.5rem 2.5rem 2rem 2.5rem;
        margin-bottom: 2rem;
    }}
    .oos-hero-title {{
        font-size: 2.4rem;
        font-weight: 800;
        color: white;
        margin-bottom: 0.5rem;
        line-height: 1.1;
    }}
    .oos-hero-sub {{
        font-size: 1rem;
        color: rgba(255,255,255,0.75);
        margin-bottom: 2rem;
    }}
    .oos-stat-num {{
        font-size: 2.6rem;
        font-weight: 800;
        color: white;
        line-height: 1.05;
    }}
    .oos-stat-label {{
        display: inline-block;
        background: {COLOR_GOLD};
        color: {COLOR_NAVY};
        font-weight: 700;
        font-size: 0.72rem;
        padding: 0.2rem 0.75rem;
        border-radius: 3px;
        margin-top: 0.45rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .oos-stat-divider {{
        border-left: 1px solid rgba(255,255,255,0.2);
        margin: 0 0.5rem;
    }}

    .states-row {{
        display: flex;
        gap: 0.6rem;
        flex-wrap: wrap;
        margin: 1rem 0 0.5rem 0;
    }}
    .state-chip {{
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.25);
        border-radius: 20px;
        padding: 0.25rem 0.85rem;
        font-size: 0.85rem;
        color: white;
        font-weight: 600;
    }}
    .state-chip span {{ opacity: 0.65; font-weight: 400; margin-left: 0.25rem; }}

    .step-wrap {{
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        margin: 2.5rem 0 1rem 0;
    }}
    .step-num {{
        background: {COLOR_NAVY};
        color: white;
        min-width: 34px;
        height: 34px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 1rem;
        flex-shrink: 0;
        margin-top: 2px;
    }}
    .step-title {{ font-size: 1.25rem; font-weight: 700; color: {COLOR_NAVY}; }}
    .step-sub   {{ font-size: 0.88rem; color: #888; margin-top: 0.15rem; }}

    .ind-icon  {{ font-size: 1.5rem; margin-bottom: 0.35rem; }}
    .ind-title {{ font-size: 0.95rem; font-weight: 700; color: {COLOR_NAVY}; margin-bottom: 0.5rem; }}
    .ind-count {{ font-size: 2rem; font-weight: 800; color: {COLOR_NAVY}; line-height: 1.1; }}
    .ind-pct   {{ font-size: 0.78rem; color: #888; margin-top: 0.15rem; margin-bottom: 0.5rem; }}
    .ind-desc  {{ font-size: 0.8rem; color: #555; line-height: 1.45; padding-bottom: 0.6rem; border-bottom: 1px solid #eee; margin-bottom: 0.5rem; }}

    .match-banner {{
        background: {COLOR_NAVY};
        color: white;
        border-radius: 8px;
        padding: 1.4rem 2rem;
        display: flex;
        align-items: center;
        gap: 1.25rem;
        margin-bottom: 1.25rem;
    }}
    .match-num   {{ font-size: 3rem; font-weight: 800; line-height: 1; }}
    .match-text  {{ font-size: 1rem; opacity: 0.8; }}
    .match-label {{ font-size: 0.75rem; opacity: 0.6; text-transform: uppercase; letter-spacing: 0.06em; margin-top: 0.15rem; }}

    .filter-pill {{
        display: inline-block;
        background: #eef2fa;
        color: {COLOR_NAVY};
        border: 1px solid #c5d0e8;
        border-radius: 20px;
        padding: 0.2rem 0.75rem;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0.2rem 0.2rem 0.2rem 0;
    }}
    </style>"""


# Public injectors: each page calls its own one. Global runs once in streamlitapp.
def inject_global():
    st.markdown(_global_css(), unsafe_allow_html=True)


def inject_home():
    st.markdown(_home_css(), unsafe_allow_html=True)


def inject_datasets():
    st.markdown(_datasets_css(), unsafe_allow_html=True)


def inject_active_presets(active_keys):
    css = active_presets_css(active_keys)
    if css:
        st.markdown(css, unsafe_allow_html=True)


def inject_property_search():
    st.markdown(_property_search_css(), unsafe_allow_html=True)


def inject_maps():
    st.markdown(_maps_css(), unsafe_allow_html=True)


def inject_neighborhood():
    st.markdown(_neighborhood_css(), unsafe_allow_html=True)


def inject_projects():
    st.markdown(_projects_css(), unsafe_allow_html=True)


def inject_contact():
    st.markdown(_contact_css(), unsafe_allow_html=True)


def inject_oos_owners():
    st.markdown(_oos_owners_css(), unsafe_allow_html=True)
