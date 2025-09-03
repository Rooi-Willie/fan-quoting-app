import streamlit as st
import os
import requests
import pandas as pd
from typing import Optional, List, Dict

# API_BASE_URL should be configured, e.g., via environment variable
# Fallback is provided for local development.
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

@st.cache_data
def get_available_motors(available_kw: List[int], poles: Optional[int] = None) -> Optional[List[Dict]]:
    """
    Fetches a list of available motors from the API based on a list of kW ratings
    and an optional poles filter. Returns a list of motor dictionaries on success,
    empty list if no kWs are provided, or None on error.
    """
    if not available_kw:
        return []  # No need to call API if no kWs are specified

    try:
        params = {'available_kw': available_kw}
        if poles is not None:
            params['poles'] = poles
        response = requests.get(f"{API_BASE_URL}/motors/", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: Could not fetch available motors. {e}")
        return None

@st.cache_data
def get_global_settings() -> Optional[Dict]:
    """
    Fetches global settings from the API, including default markups.
    Returns a dict of settings on success, or None on error.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/settings/global")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.warning(f"Could not fetch global settings: {e}")
        return None

def _update_quote_data_from_widget(key, widget_key):
    """
    Helper function to update quote_data based on widget value changes.
    """
    if widget_key in st.session_state:
        # Update the value in both old and new structure
        qd = st.session_state.quote_data
        
        # Update the legacy flat structure
        qd[key] = st.session_state[widget_key]
        
        # Also update the new nested structure if this is a field we're tracking
        if key == "motor_markup_override":
            # Ensure motor dict exists
            if "motor" not in qd:
                qd["motor"] = {}
            qd["motor"]["markup_override"] = st.session_state[widget_key]
        elif key == "motor_mount_type":
            if "motor" not in qd:
                qd["motor"] = {}
            qd["motor"]["mount_type"] = st.session_state[widget_key]
        elif key == "motor_price":
            if "motor" not in qd:
                qd["motor"] = {}
            qd["motor"]["price"] = st.session_state[widget_key]
        elif key == "motor_price_after_markup":
            if "motor" not in qd:
                qd["motor"] = {}
            qd["motor"]["price_after_markup"] = st.session_state[widget_key]
        elif key == "selected_motor_details":
            if "motor" not in qd:
                qd["motor"] = {}
            qd["motor"]["details"] = st.session_state[widget_key]

def render_main_content():
    st.header("2. Motor Selection")
    
    # Import shared_logic here to avoid circular imports
    from pages.quote_creation_tabs import shared_logic
    
    # Initialize/ensure the nested structure exists
    shared_logic.init_quote_data_structure()
    
    qd = st.session_state.quote_data
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

    # Derive poles filter from the fan configuration (support either single int or list)
    raw_poles = fan_config.get('available_motor_poles') or fan_config.get('motor_poles') or fan_config.get('motor_pole') or fan_config.get('preferred_motor_poles')
    poles_filter = None
    if isinstance(raw_poles, list):
        poles_filter = raw_poles[0] if raw_poles else None
    elif isinstance(raw_poles, int):
        poles_filter = raw_poles

    motors_list = get_available_motors(available_kw, poles=poles_filter)

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
        
        st.success(f"**Selected Motor:**   {selected_motor['supplier_name']} - {selected_motor['rated_output']} kW, {selected_motor['poles']} poles, {selected_motor['speed']} RPM ({selected_motor['product_range']})")

        # Store the full motor details in quote_data for later use
        motor_details = selected_motor.to_dict()
        
        # Update both structures
        # Legacy flat structure
        qd['selected_motor_details'] = motor_details
        
        # New nested structure
        if "motor" not in qd:
            qd["motor"] = {}
        qd["motor"]["details"] = motor_details

        # --- Fix for st.radio TypeError and to enforce Flange-only selection ---
        st.caption("Foot mount option is currently unavailable.")
        st.divider()

        # Set the motor type and price based on the fixed selection (Flange)
        # Update both structures
        mount_type = "Flange"
        motor_price = selected_motor['flange_price']
        
        # Legacy flat structure
        qd['motor_mount_type'] = mount_type
        qd['motor_price'] = motor_price
        
        # New nested structure
        qd["motor"]["mount_type"] = mount_type
        qd["motor"]["price"] = motor_price
        
        # Add motor markup override widget
        # Try to fetch default motor markup from API, fall back to 1.0
        global_settings = get_global_settings()
        default_motor_markup = 1.0
        if global_settings and "default_motor_markup" in global_settings:
            try:
                default_motor_markup = float(global_settings["default_motor_markup"])
            except (ValueError, TypeError):
                pass  # Keep the default 1.0
                
        motor_markup_col1, motor_markup_col2 = st.columns([2, 1])
        with motor_markup_col1:
            # Get the motor markup override value, checking both new and legacy structure
            motor_markup_override = qd.get("motor", {}).get("markup_override")
            if motor_markup_override is None:
                motor_markup_override = qd.get("motor_markup_override")
            
            # If still None, use the default
            if motor_markup_override is None:
                motor_markup_override = default_motor_markup
                
            # Ensure it's a float
            try:
                motor_markup_override = float(motor_markup_override)
            except (TypeError, ValueError):
                motor_markup_override = float(default_motor_markup)
                
            motor_markup = st.number_input(
                "Motor Markup Override",
                min_value=1.0,
                value=motor_markup_override,
                step=0.01,
                format="%.2f",
                key="widget_motor_markup_override",
                on_change=_update_quote_data_from_widget,
                args=("motor_markup_override", "widget_motor_markup_override"),
                help=f"Override the default markup ({default_motor_markup}) for the motor."
            )
        with motor_markup_col2:
            motor_markup_percentage = (motor_markup - 1) * 100
            st.metric("Motor Markup:",f"{motor_markup_percentage:.1f}%")

        # Calculate and display the final price with markup
        if pd.notna(qd['motor_price']):
            base_price = float(qd['motor_price'])
            marked_up_price = base_price * motor_markup
            
            # Update both structures
            # Legacy flat structure
            qd['motor_price_after_markup'] = marked_up_price
            
            # New nested structure
            if "motor" not in qd:
                qd["motor"] = {}
            qd["motor"]["price_after_markup"] = marked_up_price
            
            # Display both base and marked-up prices
            price_cols = st.columns(2)
            with price_cols[0]:
                st.metric("Base Motor Price", f"{selected_motor['currency']} {base_price:,.2f}")
            with price_cols[1]:
                st.metric("Final Motor Price (after markup)", f"{selected_motor['currency']} {marked_up_price:,.2f}")
        else:
            st.metric("Final Motor Price", "N/A")
        
        st.divider()
        with st.expander("Show all selected motor data"):
            st.json(qd['selected_motor_details'])