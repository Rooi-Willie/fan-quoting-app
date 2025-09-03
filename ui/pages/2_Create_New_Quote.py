import streamlit as st
from config import APP_TITLE
# Import tab display functions using relative imports
from pages.quote_creation_tabs import (
    project_info_tab,
    motor_selection_tab,
    fan_config_tab,
    buyout_items_tab,
    review_quote_tab,
    shared_logic
)

# Page Configuration
st.set_page_config(page_title=f"Create Quote - {APP_TITLE}", layout="wide")

print(f"STREAMLIT VERSION IN APP: {st.__version__}") # Add this line
st.write(f"Streamlit Version (displayed in app): {st.__version__}")

if not st.session_state.get("logged_in"):
    st.warning("Please log in first through the main Login page.")
    if st.button("Go to Login"):
        st.switch_page("login_page.py")
    st.stop()

st.title("Create New Quote")

# --- Define Tab Titles (used for session state key) ---
tab_titles = ["1. Project Info", "2. Motor Selection", "3. Fan Configuration", "4. Buy-out Items", "5. Review & Finalize"]

# --- Initialize Session State for Quote Data ---
# This ensures data persists across tab switches and reruns within this page.
if "quote_data" not in st.session_state:
    # Initialize with the new nested structure
    username = st.session_state.get("username", "demo")
    quote_ref = f"Q{username[0].upper()}001"
    
    st.session_state.quote_data = {
        # Project Info with sensible defaults
        "project_info": {
            "name": "",
            "client": "",
            "location": "",
            "notes": "",
            "quote_ref": quote_ref,
        },
        
        # Fan configuration data
        "fan": {
            "config_id": None,
            "uid": None,
            "hub_size_mm": None,
            "blade_sets": None,
            "markup_override": 1.2,  # Default markup
            "selected_components": [],
        },
        
        # Component details
        "component_details": {},  # Stores user overrides (thickness, waste)
        
        # Motor data
        "motor": {
            "details": {},
            "mount_type": None,
            "price": None,
            "markup_override": None,
            "price_after_markup": None,
        },
        
        # Buy-out Items
        "buyout_items": [],
        
        # Legacy flat structure for backward compatibility
        # These will be kept in sync with the nested structure during transition
        "project_name": "",
        "client_name": "",
        "project_location": "",
        "project_notes": "",
        "quote_ref": quote_ref,
        "selected_components_unordered": [],
        "buy_out_items_list": [],
    }

elif st.sidebar.button("🔄 Start New Quote / Reset Form", use_container_width=True):
    # Reset specific quote data, keep login info
    logged_in_status = st.session_state.get("logged_in", False)
    username = st.session_state.get("username", "")
    st.session_state.clear() # Clears everything
    st.session_state.logged_in = logged_in_status # Restore login
    st.session_state.username = username
    
    # Re-initialize quote data with new structure
    quote_ref = f"Q{username[0].upper()}001"
    
    st.session_state.quote_data = {
        # Project Info with sensible defaults
        "project_info": {
            "name": "",
            "client": "",
            "location": "",
            "notes": "",
            "quote_ref": quote_ref,
        },
        
        # Fan configuration data
        "fan": {
            "config_id": None,
            "uid": None,
            "hub_size_mm": None,
            "blade_sets": None,
            "markup_override": 1.2,  # Default markup
            "selected_components": [],
        },
        
        # Component details
        "component_details": {},
        
        # Motor data
        "motor": {
            "details": {},
            "mount_type": None,
            "price": None,
            "markup_override": None,
            "price_after_markup": None,
        },
        
        # Buy-out Items
        "buyout_items": [],
        
        # Legacy flat structure for backward compatibility
        "project_name": "",
        "client_name": "",
        "project_location": "",
        "project_notes": "",
        "quote_ref": quote_ref,
        "selected_components_unordered": [],
        "buy_out_items_list": [],
    }
    
    st.success("Quote form has been reset.")
    st.rerun()

# This section now renders the same sidebar content regardless of the active tab.
# First, ensure the quote_data structure is initialized with the new format
shared_logic.init_quote_data_structure()
# Then render the sidebar widgets
shared_logic.render_sidebar_widgets() # Always render fan config widgets in sidebar from shared_logic
st.sidebar.divider()
st.sidebar.json(st.session_state.quote_data, expanded=False) # For debugging


# --- Define Tabs ---
# The 'key' argument for st.tabs is not supported.
# We will manually set st.session_state.active_quote_tab_key within each tab's context.
tab_project, tab_motor, tab_fan_config, tab_buyout, tab_review = st.tabs(
    tab_titles
)

with tab_project:
    project_info_tab.render_main_content()

with tab_motor:
    motor_selection_tab.render_main_content()

with tab_fan_config:
    fan_config_tab.render_main_content()

with tab_buyout:
    buyout_items_tab.render_main_content()

with tab_review:
    review_quote_tab.render_main_content()

# The "Start New Quote / Reset Form" button is already in the sidebar from earlier.
# The st.sidebar.divider() and st.sidebar.json() are also managed above.

# Common sidebar elements (like the JSON dump for debugging) can go here,
# after the conditional block for tab-specific items.
st.sidebar.divider() # Placed after potential fan_config_tab sidebar content
st.sidebar.json(st.session_state.quote_data, expanded=False) # For debugging