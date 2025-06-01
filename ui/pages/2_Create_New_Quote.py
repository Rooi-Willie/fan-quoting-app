import streamlit as st
from config import APP_TITLE
# Import tab display functions using relative imports
from pages.quote_creation_tabs import (
    project_info_tab,
    motor_selection_tab,
    fan_config_tab,
    buyout_items_tab,
    review_quote_tab
)

# Page Configuration
st.set_page_config(page_title=f"Create Quote - {APP_TITLE}", layout="wide")

if not st.session_state.get("logged_in"):
    st.warning("Please log in first through the main Login page.")
    if st.button("Go to Login"):
        st.switch_page("login_page.py")
    st.stop()

st.title("Create New Quote")

# --- Initialize Session State for Quote Data ---
# This ensures data persists across tab switches and reruns within this page.
if "quote_data" not in st.session_state:
    st.session_state.quote_data = {
        # Project Info
        "project_name": "", "client_name": "", "project_location": "", "quote_ref": "Q" + st.session_state.get("username","demo")[0].upper() + "001",
        # Motor Selection
        "motor_type": "Standard AC", "motor_power_kw": 11.0, "motor_voltage": "400V", "motor_frequency": "50Hz",
        # Fan Configuration
        "fan_id": 570, "fan_hub": 400, "blade_sets": 1,
        "selected_components_unordered": [], # Stores raw multiselect output
        "component_details": {}, # Will store detailed data for each selected component's rows
        # Buy-out Items
        "buy_out_items_list": [], # List of dicts: {'description': '', 'cost': 0.0, 'quantity': 1}
        # Review & Quote Summary will be derived from the above
    }
elif st.sidebar.button("🔄 Start New Quote / Reset Form", use_container_width=True):
    # Reset specific quote data, keep login info
    logged_in_status = st.session_state.get("logged_in", False)
    username = st.session_state.get("username", "")
    st.session_state.clear() # Clears everything
    st.session_state.logged_in = logged_in_status # Restore login
    st.session_state.username = username
    # Re-initialize quote data
    st.session_state.quote_data = {
        "project_name": "", "client_name": "", "project_location": "", "quote_ref": "Q" + st.session_state.get("username","demo")[0].upper() + "001",
        "motor_type": "Standard AC", "motor_power_kw": 11.0, "motor_voltage": "400V", "motor_frequency": "50Hz",
        "fan_id": 570, "fan_hub": 400, "blade_sets": 1,
        "selected_components_unordered": [],
        "component_details": {},
        "buy_out_items_list": [],
    }
    st.success("Quote form has been reset.")
    st.rerun()


# --- Define Tabs ---
tab_titles = ["1. Project Info", "2. Motor Selection", "3. Fan Configuration", "4. Buy-out Items", "5. Review & Finalize"]
tab_project, tab_motor, tab_fan_config, tab_buyout, tab_review = st.tabs(tab_titles)

with tab_project:
    project_info_tab.display_tab()

with tab_motor:
    motor_selection_tab.display_tab()

with tab_fan_config:
    fan_config_tab.display_tab() # This tab module will import from config.py

with tab_buyout:
    buyout_items_tab.display_tab()

with tab_review:
    review_quote_tab.display_tab() # This tab module will import from config.py

st.sidebar.divider()
st.write("Hello")
st.sidebar.json(st.session_state.quote_data, expanded=False) # For debugging