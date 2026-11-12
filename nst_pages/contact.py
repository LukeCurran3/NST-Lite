"""Contact page."""

import streamlit as st

import styles


def render():
    styles.inject_contact()

    st.markdown("""
        <div class="breadcrumb"><a href="?auth=1&page=home">Home</a> &rsaquo; Talk With Us</div>
        <div class="page-header">Talk With Us</div>
        <div class="page-subtitle">Reach out to the Center on Poverty &amp; Community Development at Case Western Reserve University.</div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
            <div class="contact-card">
                <div class="contact-card-title">Mailing Address</div>
                <div class="contact-org">Center on Poverty &amp; Community Development</div>
                <div class="contact-school">Jack, Joseph and Morton Mandel School of Applied Social Sciences</div>
                <div class="contact-univ">Case Western Reserve University</div>
                <div class="contact-addr">
                    10900 Euclid Avenue<br>
                    Cleveland, Ohio 44106-7167
                </div>
                <div class="contact-detail">Tel: <a href="tel:2163686946">216.368.6946</a></div>
                <div class="contact-detail">Fax: 216.368.8592</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="contact-card">
                <div class="contact-card-title">Location &amp; Visitor Address</div>
                <div class="contact-org">Center on Poverty &amp; Community Development</div>
                <div class="contact-school">Jack, Joseph and Morton Mandel Community Studies Center</div>
                <div class="contact-univ">Case Western Reserve University</div>
                <div class="contact-addr">
                    11402 Bellflower Road<br>
                    Cleveland, Ohio 44106-7167
                </div>
                <div class="contact-detail">Tel: <a href="tel:2163686946">216.368.6946</a></div>
                <div class="contact-detail">Fax: 216.368.8592</div>
                <div class="contact-detail">Email: <a href="mailto:povcenter@case.edu">povcenter@case.edu</a></div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("""
        <div class="contact-card" style="text-align:center; padding: 2rem;">
            <div class="contact-card-title" style="text-align:center; border-bottom:none; margin-bottom:0.8rem;">Get in Touch</div>
            <p style="color:#555; font-size:0.95rem; margin-bottom:1.5rem;">
                Visit the Poverty Center's website to learn more about our research and team,
                or go directly to our faculty and staff directory to reach a specific person.
            </p>
            <a href="https://case.edu/socialwork/povertycenter/" target="_blank" class="contact-link-btn" style="margin-right:1rem;">
                Poverty Center Website
            </a>
            <a href="https://case.edu/socialwork/povertycenter/about/faculty-staff" target="_blank" class="contact-link-btn gold">
                Faculty &amp; Staff Directory
            </a>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #666; padding: 2rem 0;">
            <p>Powered by CWRU Poverty Center | Last Updated: March 2026</p>
        </div>
    """, unsafe_allow_html=True)
