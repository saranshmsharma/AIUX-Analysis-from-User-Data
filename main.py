import streamlit as st
import os
import time
from dotenv import load_dotenv
from shopify_integration import ShopifyIntegration, validate_shopify_credentials
from dashboard_ui import render_dashboard_ui

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="ShopAI Insight",
    page_icon="🛍️",
    layout="wide"
)

def render_setup_page():
    """Render the initial setup page for platform selection and integration."""
    # Custom CSS for setup page
    st.markdown("""
        <style>
        .platform-card {
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
            margin: 10px 0;
            cursor: pointer;
        }
        .platform-card:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .platform-logo {
            width: 50px;
            height: 50px;
            margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Center-aligned title and description
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("Welcome to ShopAI Insight!")
        st.write("Connect your e-commerce store to get started with AI-powered analytics")

    # Platform selection cards
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Shopify", use_container_width=True):
            st.session_state['selected_platform'] = 'Shopify'
            st.session_state['show_credentials'] = True

    with col2:
        if st.button("WooCommerce", use_container_width=True):
            st.session_state['selected_platform'] = 'WooCommerce'
            st.session_state['show_credentials'] = True

    # Show credentials form if platform is selected
    if 'show_credentials' in st.session_state and st.session_state['show_credentials']:
        st.divider()
        
        if st.session_state['selected_platform'] == 'Shopify':
            st.subheader("Connect your Shopify Store")
            
            col1, col2 = st.columns(2)
            with col1:
                shop_url = st.text_input(
                    "Shop URL",
                    placeholder="your-store.myshopify.com"
                )
            
            with col2:
                access_token = st.text_input(
                    "Access Token",
                    type="password",
                    placeholder="shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                )

            # Help text
            with st.expander("Need help finding these?"):
                st.markdown("""
                1. Go to your Shopify admin panel
                2. Click on **Apps** → **App and sales channel settings**
                3. Click **Develop apps** → **Create an app**
                4. Name your app and configure Admin API scopes
                5. Install the app and copy the access token
                """)

            if st.button("Connect Store", type="primary", use_container_width=True):
                if shop_url and access_token:
                    with st.spinner("Connecting to your store..."):
                        is_valid, message = validate_shopify_credentials(access_token, shop_url)
                        
                        if is_valid:
                            st.session_state['shopify_token'] = access_token
                            st.session_state['shop_url'] = shop_url
                            st.session_state['setup_completed'] = True
                            
                            st.success(message)
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
                else:
                    st.error("Please fill in all fields")

        elif st.session_state['selected_platform'] == 'WooCommerce':
            st.info("WooCommerce integration coming soon!")

def main():
    # Initialize session state
    if 'setup_completed' not in st.session_state:
        st.session_state['setup_completed'] = False

    # Show setup page or dashboard based on setup status
    if not st.session_state['setup_completed']:
        render_setup_page()
    else:
        try:
            # Initialize platform integration based on selection
            if 'shopify_token' in st.session_state:
                integration = ShopifyIntegration(
                    st.session_state['shopify_token'],
                    st.session_state['shop_url']
                )
                
                # Get store data
                store_data = integration.get_store_data()
                
                # Render dashboard
                render_dashboard_ui(store_data)
                
                # Add logout button in sidebar
                with st.sidebar:
                    if st.button("Disconnect Store", type="secondary"):
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                        st.rerun()
            
        except Exception as e:
            st.error(f"Error loading dashboard: {str(e)}")
            if st.button("Return to Setup"):
                st.session_state['setup_completed'] = False
                st.rerun()

if __name__ == "__main__":
    main()
