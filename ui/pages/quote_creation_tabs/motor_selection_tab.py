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

## Local widget update helper removed (using common.update_quote_data_top_level_key)

def render_main_content():
    st.header("2. Motor Selection")
    
    # Work with v3 schema structure
    qd = st.session_state.quote_data
    spec_section = qd.setdefault("specification", {})
    pricing_section = qd.setdefault("pricing", {})
    calc_section = qd.setdefault("calculations", {})
    
    # Motor specification in v3
    motor_spec = spec_section.setdefault("motor", {})
    # Motor pricing moved to calculations section
    motor_calc = calc_section.setdefault("motor", {})
    
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
    
    # Check if a motor is already selected in quote_data (for loaded quotes)
    existing_motor = motor_spec.get('motor_details')
    if existing_motor and isinstance(existing_motor, dict):
        existing_motor_id = existing_motor.get('id')
        st.info(f"**Currently Selected Motor:** {existing_motor.get('supplier_name', 'Unknown')} - "
                f"{existing_motor.get('rated_output', 'N/A')} kW, {existing_motor.get('poles', 'N/A')} poles, "
                f"{existing_motor.get('speed', 'N/A')} RPM ({existing_motor.get('product_range', 'N/A')})")
        st.caption("Select a different motor from the table below to change the selection, or keep the current motor.")
        st.divider()

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

        st.success(
            f"**Selected Motor:**   {selected_motor['supplier_name']} - {selected_motor['rated_output']} kW, {selected_motor['poles']} poles, {selected_motor['speed']} RPM ({selected_motor['product_range']})"
        )

        # Store the full motor details in v3 structure (renamed from 'selection' to 'motor_details')
        motor_spec['motor_details'] = selected_motor.to_dict()
        
        # No longer populate context.motor_details as it's moved to specification.motor.motor_details

        # Fixed to Flange mount for now
        st.caption("Foot mount option is currently unavailable.")
        st.divider()
        motor_spec['mount_type'] = "Flange"
        motor_calc['base_price'] = selected_motor['flange_price']

        # Get default motor markup from quote_data (already loaded from database in _new_v3_quote_data)
        default_motor_markup = pricing_section.get("motor_markup", 1.2)  # Fallback to 1.2 if missing

        motor_markup_col1, motor_markup_col2 = st.columns([2, 1])
        with motor_markup_col1:
            # Use existing motor markup from quote_data (loaded from database defaults)
            current_motor_markup = pricing_section.get("motor_markup")
            try:
                initial_markup_val = float(current_motor_markup) if current_motor_markup is not None else float(default_motor_markup)
            except (TypeError, ValueError):
                initial_markup_val = float(default_motor_markup)
            
            motor_markup = st.number_input(
                "Motor Markup",
                min_value=1.0,
                value=initial_markup_val,
                step=0.01,
                format="%.2f",
                key="widget_motor_markup_override",
                help=f"Markup multiplier for motor pricing (default: {default_motor_markup:.2f} from database).",
            )
        with motor_markup_col2:
            motor_markup_percentage = (motor_markup - 1) * 100
            st.metric("Motor Markup:", f"{motor_markup_percentage:.1f}%")

        # Check if markup changed and update session state
        markup_changed = pricing_section.get('motor_markup') != motor_markup
        pricing_section['motor_markup'] = motor_markup

        if pd.notna(motor_calc.get('base_price')):
            base_price = float(motor_calc['base_price'])
            marked_up_price = base_price * motor_markup
            motor_calc['final_price'] = marked_up_price
            
            # ENHANCED: Update totals immediately when markup changes to prevent lag
            if markup_changed:
                from utils import update_quote_totals
                st.session_state.quote_data = qd  # Sync session state first
                update_quote_totals(qd)  # Calculate totals immediately
                st.rerun()
                
            price_cols = st.columns(2)
            with price_cols[0]:
                st.metric("Base Motor Price", f"{selected_motor['currency']} {base_price:,.2f}")
            with price_cols[1]:
                st.metric("Final Motor Price (after markup)", f"{selected_motor['currency']} {marked_up_price:,.2f}")
        else:
            st.metric("Final Motor Price", "N/A")

        st.divider()
        with st.expander("Show all selected motor data"):
            st.json(motor_spec['motor_details'])