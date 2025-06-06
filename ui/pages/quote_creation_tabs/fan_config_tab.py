import streamlit as st
import os
import pandas as pd # Keep for potential future use, though not strictly needed if not building DF here
from typing import Optional, List, Dict # Added for type hinting
import requests # Added for API calls
from config import COMPONENT_ORDER, COMPONENT_IMAGES, ROW_DEFINITIONS, IMAGE_FOLDER_PATH

# API_BASE_URL should be configured, e.g., via environment variable
# Docker Compose will set this from .env for the UI service.
# Fallback is provided for local development if API is on localhost:8000.
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

def _update_quote_data_top_level_key(qd_top_level_key, widget_sstate_key):
    """
    Callback to update a key in st.session_state.quote_data
    from a widget's state in st.session_state.
    """
    if widget_sstate_key in st.session_state:
        st.session_state.quote_data[qd_top_level_key] = st.session_state[widget_sstate_key]
        # Example: If blade_sets needs to be int downstream, convert here or where it's used.
        # if qd_top_level_key == "blade_sets" and st.session_state[widget_sstate_key] is not None:
        #     try:
        #         st.session_state.quote_data[qd_top_level_key] = int(st.session_state[widget_sstate_key])
        #     except ValueError:
        #         st.warning(f"Blade sets value '{st.session_state[widget_sstate_key]}' is not a valid number.")


def _update_component_detail_from_widget_state(component_name, detail_key, widget_sstate_key):
    """
    Callback to update a specific detail for a component in
    st.session_state.quote_data["component_details"].
    """
    qd = st.session_state.quote_data
    # Ensure component_details and the specific component dictionary exist
    component_dict = qd.setdefault("component_details", {}).setdefault(component_name, {})

    if widget_sstate_key in st.session_state:
        component_dict[detail_key] = st.session_state[widget_sstate_key]

# --- API Helper Functions with Caching ---
@st.cache_data
def get_fan_ids() -> Optional[List[str]]:
    """
    Fetches the list of all available Fan IDs from the API.
    Returns a list of strings on success, None on failure.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/fan_ids")
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: Could not fetch Fan IDs. {e}")
        return None

@st.cache_data
def get_fan_config(fan_id: str) -> Optional[Dict]:
    """
    Fetches the full configuration for a specific Fan ID from the API.
    Returns a dictionary on success, None on failure.
    """
    if not fan_id:
        return None
    try:
        response = requests.get(f"{API_BASE_URL}/fan_config/{fan_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: Could not fetch config for Fan ID '{fan_id}'. {e}")
        return None

def _handle_fan_id_change():
    """Callback to handle changes in Fan ID selection."""
    qd = st.session_state.quote_data
    selected_fan_id_from_widget = st.session_state.get("widget_fc_fan_id")
    previous_fan_id_in_qd = qd.get("fan_id")

    if selected_fan_id_from_widget and selected_fan_id_from_widget != "--- Please select a Fan ID ---":
        if previous_fan_id_in_qd != selected_fan_id_from_widget: # Fan ID actually changed
            qd["fan_id"] = selected_fan_id_from_widget
            fan_config = get_fan_config(selected_fan_id_from_widget)
            st.session_state.current_fan_config = fan_config

            if fan_config:
                qd["fan_hub"] = fan_config.get('hub_size_mm')
                api_blade_qty = fan_config.get('different_blade_qty', [])
                str_api_blade_qty = [str(bq) for bq in api_blade_qty] if api_blade_qty else []
                
                if str_api_blade_qty:
                    # Preserve current blade_sets if valid, else default to first new option
                    current_blade_set_in_qd = str(qd.get("blade_sets")) if qd.get("blade_sets") is not None else None
                    if current_blade_set_in_qd in str_api_blade_qty:
                        qd["blade_sets"] = current_blade_set_in_qd
                    else:
                        qd["blade_sets"] = str_api_blade_qty[0]
                else:
                    qd["blade_sets"] = None # No blade options
            else: # Failed to fetch fan_config
                qd["fan_hub"] = None
                qd["blade_sets"] = None
        # Case: Fan ID in widget is same as in qd, but current_fan_config might be lost (e.g., page refresh)
        elif st.session_state.get("current_fan_config") is None and qd.get("fan_id"):
            fan_config = get_fan_config(qd["fan_id"]) # Re-fetch
            st.session_state.current_fan_config = fan_config
            if fan_config:
                qd["fan_hub"] = fan_config.get('hub_size_mm') # Re-affirm hub
                api_blade_qty = fan_config.get('different_blade_qty', [])
                str_api_blade_qty = [str(bq) for bq in api_blade_qty] if api_blade_qty else []
                current_blade_set_in_qd = str(qd.get("blade_sets")) if qd.get("blade_sets") is not None else None

                if str_api_blade_qty:
                    if current_blade_set_in_qd not in str_api_blade_qty:
                        qd["blade_sets"] = str_api_blade_qty[0] # Reset if invalid
                else:
                    qd["blade_sets"] = None
            else: # Re-fetch failed
                qd["fan_hub"] = None
                qd["blade_sets"] = None

    elif selected_fan_id_from_widget == "--- Please select a Fan ID ---":
        if previous_fan_id_in_qd is not None: # Changed to placeholder
            qd["fan_id"] = None
            qd["fan_hub"] = None
            qd["blade_sets"] = None
            st.session_state.current_fan_config = None
    # If selected_fan_id_from_widget is None (initial state), do nothing until user selects.

def render_sidebar_widgets():
    """Renders the specific sidebar widgets for Fan Configuration."""
    if "quote_data" not in st.session_state:
        st.warning("quote_data not found in session_state. Initializing to empty dictionary. "
                   "Consider initializing in the parent page for better state management.")
        st.session_state.quote_data = {}
    if "current_fan_config" not in st.session_state: # Initialize for API response
        st.session_state.current_fan_config = None

    qd = st.session_state.quote_data # Shorthand for quote_data

    with st.sidebar:
        st.subheader("Base Fan Parameters")

        # 1. Fan ID Selectbox (API Driven)
        api_fan_ids = get_fan_ids()
        fan_id_select_options = ["--- Please select a Fan ID ---"]
        if api_fan_ids:
            fan_id_select_options.extend(api_fan_ids)
        else:
            st.caption("Could not load Fan IDs from API.") # Error already shown by get_fan_ids

        current_fan_id_val = str(qd.get("fan_id")) if qd.get("fan_id") is not None else None
        fan_id_idx = 0
        if current_fan_id_val and current_fan_id_val in fan_id_select_options:
            fan_id_idx = fan_id_select_options.index(current_fan_id_val)
        
        st.selectbox(
            "Fan ID", options=fan_id_select_options,
            index=fan_id_idx,
            key="widget_fc_fan_id",
            on_change=_handle_fan_id_change
        )

        # 2. Fan Hub (Display Only - Derived from Fan ID)
        fan_config = st.session_state.get("current_fan_config")
        fan_hub_display = str(fan_config.get('hub_size_mm', "N/A")) if fan_config else str(qd.get("fan_hub", "N/A"))
        st.text_input(
            "Fan Hub (mm)",
            value=fan_hub_display,
            disabled=True,
            key="display_fc_fan_hub" # Not directly tied to quote_data top-level via simple callback
        )

        # 3. Blade Sets (Blade Quantity - API Driven, dependent on Fan ID)
        blade_qty_select_options = ["N/A"]
        blade_qty_disabled = True
        blade_qty_idx = 0
        
        if fan_config and fan_config.get('different_blade_qty'):
            blade_qty_select_options = [str(bq) for bq in fan_config.get('different_blade_qty')]
            blade_qty_disabled = False
            current_blade_sets_val = str(qd.get("blade_sets")) if qd.get("blade_sets") is not None else None
            if current_blade_sets_val and current_blade_sets_val in blade_qty_select_options:
                blade_qty_idx = blade_qty_select_options.index(current_blade_sets_val)
        elif qd.get("blade_sets"): # Show existing if no new options yet
            blade_qty_select_options = [str(qd.get("blade_sets"))]

        st.selectbox(
            "Blade Sets", options=blade_qty_select_options,
            index=blade_qty_idx,
            key="widget_fc_blade_sets",
            on_change=_update_quote_data_top_level_key,
            args=("blade_sets", "widget_fc_blade_sets"),
            disabled=blade_qty_disabled,
            help="Options populated after selecting a Fan ID."
        )
        st.divider()

        # --- Component Selection ---
        st.subheader("Fan Components Selection")
        st.multiselect(
            "Select Fan Components",
            options=COMPONENT_ORDER,
            default=qd.get("selected_components_unordered", []),
            key="widget_fc_multiselect_components",
            on_change=_update_quote_data_top_level_key,
            args=("selected_components_unordered", "widget_fc_multiselect_components"),
            help="Components will be ordered automatically in the main view. Select Fan ID first."
        )
        st.divider()

def render_main_content():
    """Renders the main content area for the Fan Configuration tab."""
    st.header("3. Fan Configuration Details")

    if "quote_data" not in st.session_state:
        # This should ideally be handled by the main page (2_Create_New_Quote.py)
        st.error("Quote data not initialized. Please start a new quote or refresh.")
        st.session_state.quote_data = {} # Basic fallback
        # return # Optionally stop if quote_data is critical and missing

    qd = st.session_state.quote_data # Shorthand for quote_data
    cd = qd.setdefault("component_details", {}) # Shorthand for component_details

    # --- Main Tab Display Area ---
    st.subheader("Configure Selected Fan Components")

    # Derive the ordered list for processing
    ordered_selected_components = [
        comp for comp in COMPONENT_ORDER if comp in qd.get("selected_components_unordered", [])
    ]

    if not ordered_selected_components:
        st.info("Select fan components from the sidebar to configure them.")
        # Clean up details for components that are no longer selected
        keys_to_remove = [k for k in cd if k not in ordered_selected_components]
        for k_rem in keys_to_remove:
            del cd[k_rem]
        return

    num_selected_components = len(ordered_selected_components)
    column_layout_config = [1.5] + [1] * num_selected_components # Label col + component cols

    # --- Component Image Row ---
    image_cols = st.columns(column_layout_config)
    with image_cols[0]: st.markdown("**Image**")
    for i, comp_name in enumerate(ordered_selected_components):
        with image_cols[i + 1]:
            image_full_path = COMPONENT_IMAGES.get(comp_name)
            if image_full_path and os.path.exists(image_full_path):
                st.image(image_full_path, use_column_width='always', caption=comp_name[:15]+"...") # Keep caption short
            elif image_full_path: # Path defined but file missing
                st.warning(f"Img missing: {os.path.basename(image_full_path)}")
            else: # Path not configured
                st.markdown("*(No Image)*")

    # --- Header Row for Parameters ---
    header_cols = st.columns(column_layout_config)
    with header_cols[0]: st.markdown("**Parameter**")
    for i, comp_name in enumerate(ordered_selected_components):
        with header_cols[i + 1]: st.markdown(f"**{comp_name}**", help=comp_name) # Use help for full name if truncated
    st.divider()

    # --- Data Input/Display Area ---
    for row_idx, (row_label, row_type, default_val, unit_or_curr) in enumerate(ROW_DEFINITIONS):
        param_row_cols = st.columns(column_layout_config)
        with param_row_cols[0]:
            display_label = f"{row_label} ({unit_or_curr})" if unit_or_curr not in ["factor", "%"] else row_label
            st.markdown(display_label)
            if unit_or_curr in ["factor", "%"]:
                 st.caption(f"Unit: {unit_or_curr}")


        for comp_idx, comp_name in enumerate(ordered_selected_components):
            cd.setdefault(comp_name, {}) # Ensure component dict exists in component_details
            widget_key_unique = f"fc_{comp_name}_{row_label.replace(' ', '_')}_{row_idx}_{comp_idx}"

            with param_row_cols[comp_idx + 1]:
                current_value_for_display = cd[comp_name].get(row_label, default_val)

                if row_type == 'DB':
                    # For demo, vary DB values slightly. In real app, fetch from DB/rules engine
                    # based on fan_id, comp_name etc.
                    # This value should ideally be calculated/fetched once and stored if it's complex
                    # For simplicity, using a placeholder:
                    db_value_to_display = default_val * (1 + comp_idx * 0.02) # Example variation
                    st.text(f"{db_value_to_display:.2f}")
                    cd[comp_name][row_label] = db_value_to_display # Store the displayed value
                elif row_type == 'Calc':
                    # Placeholder: Actual calculation should happen here or be triggered
                    # For now, just use a dummy value variation
                    # This calculation would use other values from cd[comp_name] or qd
                    calc_value_to_display = default_val * (1 - comp_idx * 0.01) # Example variation
                    st.text(f"{calc_value_to_display:.2f}")
                    cd[comp_name][row_label] = calc_value_to_display # Store the displayed value
                elif row_type == 'Mod':
                    step_val = 0.1
                    fmt_str = "%.2f"
                    if unit_or_curr == '%':
                        step_val = 1.0
                        fmt_str = "%.1f"
                    elif unit_or_curr == "mm":
                        step_val = 0.5
                        fmt_str = "%.1f"
                    elif unit_or_curr == "factor":
                        step_val = 0.01
                    elif unit_or_curr == "hrs":
                        step_val = 0.5
                        fmt_str = "%.1f"

                    user_value = st.number_input(
                        label=f"_{row_label}_{comp_name}", # Underscore for hidden label
                        label_visibility="collapsed",
                        value=float(current_value_for_display), # Ensure float for number_input
                        step=step_val,
                        format=fmt_str,
                        key=widget_key_unique,
                        on_change=_update_component_detail_from_widget_state,
                        args=(comp_name, row_label, widget_key_unique)
                    )
                    # Value is now updated in session state via the callback

    # Clean up details for components that are no longer selected (can be done here or at start)
    # keys_to_remove_at_end = [k for k in cd if k not in ordered_selected_components]
    # for k_rem_end in keys_to_remove_at_end:
    #     del cd[k_rem_end]
    # Note: The cleanup is already present at the beginning if no components are selected.
    # Consider if a second cleanup here is always necessary or if the initial one covers all cases.
    # For now, the initial cleanup when `not ordered_selected_components` and the implicit removal
    # by not processing unselected components should suffice. If issues arise with stale data
    # for deselected components while others remain, this end-cleanup can be reinstated.