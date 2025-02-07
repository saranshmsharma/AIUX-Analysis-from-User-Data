import streamlit as st
from dashboard_components import (
    render_dashboard,
    render_sales_analysis,
    render_product_insights,
    render_customer_analytics,
    render_detailed_recommendations,
    render_prediction_page
)
from chatbot_component import render_chatbot

def render_dashboard_ui(store_data):
    """Render the main dashboard UI with navigation."""
    
    # Custom CSS for navigation and layout
    st.markdown("""
        <style>
        .stHorizontalBlock {
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .nav-link {
            text-decoration: none;
            color: #1f1f1f;
            padding: 10px 15px;
            border-radius: 5px;
        }
        .nav-link:hover {
            background-color: #e9ecef;
        }
        .metric-card {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 15px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Get the current query parameters
    query_params = st.query_params
    
    # Navigation menu
    pages = {
        "Dashboard": render_dashboard,
        "AI Assistant": render_chatbot
    }

    # Horizontal navigation
    selected_page = st.radio(
        "Navigation",
        list(pages.keys()),
        horizontal=True,
        label_visibility="collapsed"
    )

    # Update query parameters when page changes
    if selected_page:
        st.query_params['page'] = selected_page.lower().replace(' ', '_')

    # Render the selected page content
    try:
        pages[selected_page](store_data)
    except Exception as e:
        st.error(f"Error rendering page: {str(e)}")