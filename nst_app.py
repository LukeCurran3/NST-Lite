"""
NST Data Tool - Streamlit Application
Cleveland Neighborhood Data Explorer
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="NST Data Tool",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f4788;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f4788;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="main-header">NST Data Tool</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Neighborhood Strategy Technology for Cleveland</p>', unsafe_allow_html=True)

# Sidebar for filters and navigation
with st.sidebar:
    st.image("https://via.placeholder.com/300x80/1f4788/ffffff?text=NST+Logo", use_container_width=True)
    
    st.markdown("### 🔍 Data Filters")
    
    # Geographic selection
    geographic_level = st.selectbox(
        "Geographic Level",
        ["Neighborhood", "Ward", "Census Tract", "Zip Code", "City Council District"]
    )
    
    # Specific area selection (this would be dynamic based on your data)
    area = st.selectbox(
        f"Select {geographic_level}",
        ["All Areas", "Downtown", "Ohio City", "Tremont", "Detroit Shoreway", "Glenville"]
    )
    
    # Data category
    data_category = st.multiselect(
        "Data Categories",
        ["Housing", "Demographics", "Economic Development", "Health", "Education", "Crime"],
        default=["Housing"]
    )
    
    # Time period
    st.markdown("### 📅 Time Period")
    year_range = st.slider(
        "Select Year Range",
        2014, 2024, (2020, 2024)
    )
    
    st.markdown("---")
    st.markdown("### 📥 Export Data")
    if st.button("Download CSV", use_container_width=True):
        st.success("Download started!")
    
    if st.button("Download Shapefile", use_container_width=True):
        st.success("Shapefile download started!")

# Main content area with tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Data Overview", "🗺️ Map View", "📈 Analysis Tools", "ℹ️ About"])

with tab1:
    st.markdown("## Data Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Properties",
            value="12,543",
            delta="+234 from last year"
        )
    
    with col2:
        st.metric(
            label="Avg. Property Value",
            value="$125,000",
            delta="+5.2%"
        )
    
    with col3:
        st.metric(
            label="Vacancy Rate",
            value="8.4%",
            delta="-1.2%",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            label="Lead Violations",
            value="145",
            delta="-23",
            delta_color="inverse"
        )
    
    st.markdown("---")
    
    # Sample data table (you'll replace this with your actual database queries)
    st.markdown("### Property Data Table")
    
    # Create sample data
    sample_data = pd.DataFrame({
        'Property ID': [f'PROP-{i:05d}' for i in range(1, 101)],
        'Address': [f'{100+i*10} Main St' for i in range(100)],
        'Neighborhood': ['Downtown', 'Ohio City', 'Tremont', 'Glenville', 'Detroit Shoreway'] * 20,
        'Property Value': [125000 + (i * 1000) for i in range(100)],
        'Year Built': [1950 + (i % 70) for i in range(100)],
        'Bedrooms': [(i % 4) + 1 for i in range(100)],
        'Vacancy Status': ['Occupied', 'Vacant', 'Occupied', 'Occupied', 'Occupied'] * 20,
    })
    
    # Add search functionality
    search = st.text_input("🔍 Search by address or property ID", "")
    if search:
        filtered_data = sample_data[
            sample_data['Address'].str.contains(search, case=False) | 
            sample_data['Property ID'].str.contains(search, case=False)
        ]
    else:
        filtered_data = sample_data
    
    # Display dataframe with formatting
    st.dataframe(
        filtered_data.head(20),
        use_container_width=True,
        hide_index=True
    )
    
    st.caption(f"Showing {min(20, len(filtered_data))} of {len(filtered_data)} properties")

with tab2:
    st.markdown("## Interactive Map")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.markdown("### Map Controls")
        
        map_data_type = st.radio(
            "Display Data",
            ["Property Values", "Vacancy Rates", "Lead Violations", "Owner Type"]
        )
        
        show_heat_map = st.checkbox("Show Heat Map", value=False)
        show_boundaries = st.checkbox("Show Neighborhood Boundaries", value=True)
    
    with col1:
        # Create a basic map centered on Cleveland
        m = folium.Map(
            location=[41.4993, -81.6944],  # Cleveland coordinates
            zoom_start=12,
            tiles="OpenStreetMap"
        )
        
        # Add some sample markers (you'll replace with actual property data)
        neighborhoods = [
            {"name": "Downtown", "lat": 41.5017, "lon": -81.6937, "value": 145000},
            {"name": "Ohio City", "lat": 41.4842, "lon": -81.7100, "value": 125000},
            {"name": "Tremont", "lat": 41.4764, "lon": -81.6934, "value": 135000},
            {"name": "Glenville", "lat": 41.5298, "lon": -81.6149, "value": 95000},
            {"name": "Detroit Shoreway", "lat": 41.4883, "lon": -81.7267, "value": 115000},
        ]
        
        for hood in neighborhoods:
            folium.CircleMarker(
                location=[hood['lat'], hood['lon']],
                radius=15,
                popup=f"{hood['name']}<br>Avg Value: ${hood['value']:,}",
                tooltip=hood['name'],
                color='#1f4788',
                fill=True,
                fillColor='#4a90e2',
                fillOpacity=0.6
            ).add_to(m)
        
        # Display map
        st_folium(m, width=700, height=500)
    
    st.info("💡 Click on markers to see neighborhood details. Map features will expand as you add your actual NST data.")

with tab3:
    st.markdown("## Analysis Tools")
    
    analysis_type = st.selectbox(
        "Select Analysis Type",
        ["Trend Analysis", "Comparative Analysis", "Geographic Distribution", "Custom Query"]
    )
    
    if analysis_type == "Trend Analysis":
        st.markdown("### Property Value Trends Over Time")
        
        # Sample trend data
        years = list(range(2014, 2025))
        trend_data = pd.DataFrame({
            'Year': years,
            'Avg Property Value': [100000 + (i * 2500) for i in range(len(years))],
            'Median Property Value': [95000 + (i * 2200) for i in range(len(years))],
        })
        
        fig = px.line(
            trend_data,
            x='Year',
            y=['Avg Property Value', 'Median Property Value'],
            title=f'Property Value Trends - {area}',
            labels={'value': 'Property Value ($)', 'variable': 'Metric'},
            markers=True
        )
        
        fig.update_layout(
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    elif analysis_type == "Comparative Analysis":
        st.markdown("### Neighborhood Comparison")
        
        neighborhoods_compare = st.multiselect(
            "Select neighborhoods to compare",
            ["Downtown", "Ohio City", "Tremont", "Glenville", "Detroit Shoreway"],
            default=["Ohio City", "Tremont"]
        )
        
        # Sample comparison data
        comparison_data = pd.DataFrame({
            'Neighborhood': neighborhoods_compare * 3,
            'Metric': ['Property Value', 'Vacancy Rate', 'Median Income'] * len(neighborhoods_compare),
            'Value': [125000, 8.4, 45000] * len(neighborhoods_compare)
        })
        
        fig = px.bar(
            comparison_data,
            x='Neighborhood',
            y='Value',
            color='Metric',
            barmode='group',
            title='Neighborhood Comparison'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "Custom Query":
        st.markdown("### Custom Data Query")
        
        st.info("🔧 Custom query builder coming soon! This will allow you to create complex filters across multiple data sources.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Property characteristic", placeholder="e.g., Year Built > 1970")
            st.text_input("Owner type", placeholder="e.g., Out-of-state investor")
        
        with col2:
            st.text_input("Violation type", placeholder="e.g., Lead violations")
            st.text_input("Price range", placeholder="e.g., $100k - $200k")
        
        if st.button("Run Query", type="primary"):
            st.success("Query executed! Results shown below.")

with tab4:
    st.markdown("## About NST Data Tool")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### What is NST?
        
        The **Neighborhood Strategy Technology (NST)** platform is a comprehensive data tool developed by the 
        CWRU Poverty Center to provide access to integrated neighborhood-level data for Cleveland.
        
        #### Key Features:
        - 📊 **Comprehensive Data**: Property, demographic, economic, health, and education data
        - 🗺️ **Geographic Analysis**: Interactive mapping and spatial analysis tools
        - 📈 **Trend Analysis**: Track changes over time across multiple indicators
        - 🔍 **Advanced Search**: Find properties by address, owner, or characteristics
        - 💾 **Data Export**: Download data in multiple formats (CSV, Shapefile, JSON)
        
        #### Data Sources:
        - Cuyahoga County Fiscal Office
        - Cleveland City Planning Commission
        - US Census Bureau
        - Cleveland Metropolitan School District
        - And many more...
        
        #### Need Help?
        - 📧 Email: nst@case.edu
        - 📚 [View Training Materials](#)
        - 🎥 [Watch Tutorial Videos](#)
        """)
    
    with col2:
        st.markdown("### Quick Stats")
        st.markdown("""
        - **Properties**: 150,000+
        - **Data Points**: 200+ variables
        - **Years Covered**: 2014-2024
        - **Users**: 500+ organizations
        - **Last Updated**: January 2026
        """)
        
        st.markdown("### Resources")
        if st.button("📖 User Guide", use_container_width=True):
            st.info("User guide opening...")
        if st.button("🎓 Training Schedule", use_container_width=True):
            st.info("Training schedule opening...")
        if st.button("💬 Contact Support", use_container_width=True):
            st.info("Opening contact form...")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>NST Data Tool v2.0 | Developed by CWRU Poverty Center | © 2026</p>
    <p style='font-size: 0.9rem;'>Data updated January 2026 | <a href='#'>Privacy Policy</a> | <a href='#'>Terms of Use</a></p>
</div>
""", unsafe_allow_html=True)
