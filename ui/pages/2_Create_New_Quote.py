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
from common import (
    render_sidebar_widgets,  # Shared sidebar renderer
    _new_quote_data,
    NEW_SCHEMA_VERSION,
    initialize_session_state_from_quote_data,
)

# Page Configuration
st.set_page_config(page_title=f"Create Quote - {APP_TITLE}", layout="wide")

if not st.session_state.get("logged_in"):
    st.warning("Please log in first through the main Login page.")
    if st.button("Go to Login"):
        st.switch_page("Login_Page.py")
    st.stop()

st.title("Create New Quote")

# --- Define Tab Titles (used for session state key) ---
tab_titles = ["1. Project Info", "2. Motor Selection", "3. Fan Configuration", "4. Buy-out Items", "5. Review & Finalize"]

# --- Initialize Session State for Quote Data ---
# This ensures data persists across tab switches and reruns within this page.
if "quote_data" not in st.session_state:
    st.session_state.quote_data = _new_quote_data(st.session_state.get("username"))
else:
    # Ensure we're using current schema, start fresh if not
    qd = st.session_state.quote_data
    if not isinstance(qd, dict) or qd.get("meta", {}).get("version") != NEW_SCHEMA_VERSION:
        st.session_state.quote_data = _new_quote_data(st.session_state.get("username"))
    else:
        # If quote_data exists and is v3, initialize session state from it
        # This handles the case where a quote was loaded for editing
        initialize_session_state_from_quote_data(st.session_state.quote_data)

# Ensure totals are calculated if component data exists
from utils import update_quote_totals
if st.session_state.quote_data.get("calculations", {}).get("components"):
    update_quote_totals(st.session_state.quote_data)

if st.sidebar.button("🔄 Start New Quote / Reset Form", use_container_width=True):
    # Reset specific quote data, keep login info
    logged_in_status = st.session_state.get("logged_in", False)
    username = st.session_state.get("username", "")
    
    # Increment widget reset counter to force all widgets to recreate with new keys
    # This is more reliable than st.rerun() for resetting widget states
    current_counter = st.session_state.get("widget_reset_counter", 0)
    
    st.session_state.clear() # Clears everything
    st.session_state.logged_in = logged_in_status # Restore login
    st.session_state.username = username
    st.session_state.widget_reset_counter = current_counter + 1  # Increment to force widget reset
    
    # Create fresh quote data
    st.session_state.quote_data = _new_quote_data(username)
    
    # Rerun to apply changes immediately
    st.rerun()

# This section now renders the same sidebar content regardless of the active tab.
render_sidebar_widgets()  # Always render shared sidebar widgets

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