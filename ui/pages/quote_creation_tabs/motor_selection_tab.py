import streamlit as st
import os
import requests
import pandas as pd
from typing import Optional, List, Dict

# API_BASE_URL should be configured, e.g., via environment variable
# Fallback is provided for local development.
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

@st.cache_data
def get_available_motors(available_kw: List[int]) -> Optional[List[Dict]]:
    """
    Fetches a list of available motors from the API based on a list of kW ratings.
    Returns a list of motor dictionaries on success, None on failure.
    """
    if not available_kw:
        return [] # No need to call API if no kWs are specified

    try:
        # The `requests` library can handle a list of values for a single key
        # by passing it as the `params` argument (e.g., ?available_kw=22&available_kw=30)
        params = {'available_kw': available_kw}
        response = requests.get(f"{API_BASE_URL}/motors/", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: Could not fetch available motors. {e}")
        return None

def render_main_content():
    st.header("2. Motor Selection")
    qd = st.session_state.get("quote_data", {})
    fan_config = st.session_state.get("current_fan_config")

    # --- 1. Prerequisite Check: Ensure a fan is selected first. ---
    if not fan_config:
        st.info("Please select a fan on the 'Fan Configuration' tab to see available motors.")
        return # Stop execution of this tab if no fan is selected

    # --- 2. Fetch available motors based on the selected fan's kW ratings ---
    available_kw = fan_config.get('available_motor_kw', [])
    if not available_kw:
        st.warning("The selected fan configuration has no specified motor kW ratings.")
        return

    motors_list = get_available_motors(available_kw)

    # --- 3. Display motors in a selectable dataframe (initial setup) ---
    if motors_list is None:
        # API call failed, error is already shown by the helper function.
        st.error("Could not retrieve motor data from the API.")
        return
    
    if not motors_list:
        st.info(f"No motors found in the database for the available kW ratings: {', '.join(map(str, available_kw))}.")
        return
    
    motors_df = pd.DataFrame(motors_list)
    # Store the full dataframe in session state to access it after rerun on selection
    st.session_state.available_motors_df = motors_df

    # Prepare a user-friendly dataframe for display
    display_df = motors_df.copy()
    
    # Create formatted price columns for both mount types
    display_df['price_flange'] = display_df.apply(
        lambda row: f"{row['currency']} {row['flange_price']:.2f}" if pd.notna(row['flange_price']) else "N/A",
        axis=1
    )
    display_df['price_foot'] = display_df.apply(
        lambda row: f"{row['currency']} {row['foot_price']:.2f}" if pd.notna(row['foot_price']) else "N/A",
        axis=1
    )
    
    # Define the columns to show and their friendly names
    cols_to_display = {
        'supplier_name': 'Supplier',
        'product_range': 'Range',
        'rated_output': 'kW',
        'poles': 'Poles',
        'speed': 'Speed (RPM)',
        'price_flange': 'Price (Flange)',
        'price_foot': 'Price (Foot)',
        'latest_price_date': 'Price Date'
    }
    
    # Filter to only the columns we want to show, in the desired order
    display_df_final = display_df[list(cols_to_display.keys())].rename(columns=cols_to_display)

    st.write("Please select a motor from the list below:")
    st.dataframe(
        display_df_final,
        key="motor_selection_df",
        on_select="rerun", # Rerun the script when a row is selected
        selection_mode="single-row",
        hide_index=True,
        use_container_width=True
    )

    # --- 4. Handle the selection and finalize ---
    selection = st.session_state.get("motor_selection_df", {}).get("selection", {})
    if selection.get("rows"):
        selected_index = selection["rows"][0]
        selected_motor = st.session_state.available_motors_df.iloc[selected_index]
        
        st.success(f"**Selected Motor:**   {selected_motor['supplier_name']} - {selected_motor['rated_output']} kW, {selected_motor['poles']} poles, {selected_motor['speed']} RPM")

        # Store the full motor details in quote_data for later use
        qd['selected_motor_details'] = selected_motor.to_dict()

        # --- Fix for st.radio TypeError and to enforce Flange-only selection ---
        st.subheader("Finalize Motor Configuration")
        st.markdown("Mounting Type: **Flange**")
        st.caption("Foot mount option is currently unavailable.")

        # Set the motor type and price based on the fixed selection (Flange)
        qd['motor_mount_type'] = "Flange"
        qd['motor_price'] = selected_motor['flange_price']
        
        # Display the final price, handling potential None values
        if pd.notna(qd['motor_price']):
            st.metric("Final Motor Price", f"{selected_motor['currency']} {qd['motor_price']:,.2f}")
        else:
            st.metric("Final Motor Price", "N/A")
        
        with st.expander("Show all selected motor data"):
            st.json(qd['selected_motor_details'])