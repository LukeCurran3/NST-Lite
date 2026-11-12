"""Popular Projects hub page."""

import streamlit as st

import styles


def render():
    styles.inject_projects()

    st.markdown('<div class="breadcrumb"><a href="?auth=1&page=home" target="_self">Home</a> &nbsp;/&nbsp; <strong>Popular Projects</strong></div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="page-header">Popular Projects</div>
        <div class="page-subtitle">Pre-built investigation tools designed around the most common NST workflows.</div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="project-grid">
            <a href="?auth=1&page=oos-owners" target="_self" class="project-card">
                <div class="project-card-title">Out-of-State Owner Finder</div>
                <div class="project-card-desc">
                    Identify parcels with out-of-state mailing addresses and layer on risk indicators
                    including tax delinquency, vacancy, condemnation, and corporate ownership
                    to build targeted outreach and enforcement lists.
                </div>
                <div class="project-card-tag">Ownership &nbsp;&middot;&nbsp; Tax &nbsp;&middot;&nbsp; Vacancy</div>
            </a>
            <a href="?auth=1&page=distressed-rentals" target="_self" class="project-card">
                <div class="project-card-title">Distressed Rentals</div>
                <div class="project-card-desc">
                    Flag rental properties showing signs of extractive ownership using five distress
                    indicators: tax delinquency, violations, complaints, grade decline, and evictions.
                    Classify owners as individual, corporate, trust, or non-profit to support tenant
                    advocacy and research.
                </div>
                <div class="project-card-tag">Rentals &nbsp;&middot;&nbsp; Distress &nbsp;&middot;&nbsp; Ownership</div>
            </a>
            <div class="project-card-coming">
                <div class="project-card-title">Coming Soon</div>
                <div class="project-card-desc">
                    A new project tool is currently in development. Check back for updates.
                </div>
                <div class="coming-label">In Development</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #666; padding: 2rem 0;">
            <p>Powered by CWRU Poverty Center | Last Updated: January 2026</p>
        </div>
    """, unsafe_allow_html=True)
