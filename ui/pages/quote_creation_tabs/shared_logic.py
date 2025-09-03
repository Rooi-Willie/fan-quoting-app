import streamlit as st
import os
import requests
import logging
from typing import Optional, List, Dict, Any
from utils import ensure_server_summary_up_to_date

# Configure basic logging
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s')

# Create a logger object
logger = logging.getLogger(__name__)

# API_BASE_URL should be configured, e.g., via environment variable
# Docker Compose will set this from .env for the UI service.
# Fallback is provided for local development if API is on localhost:8000.
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

# Initialize callback counters in session state
if "callback_counters" not in st.session_state:
    st.session_state.callback_counters = {
        "top_level_key": 0,
        "component_detail": 0
    }

# --- New Data Structure Helpers ---

def init_quote_data_structure():
    """
    Initialize or update the quote_data structure with the new nested format.
    This ensures backward compatibility while adding the new structure.
    """
    if "quote_data" not in st.session_state:
        st.session_state.quote_data = {}
    
    qd = st.session_state.quote_data
    
    # Ensure the new structure exists
    if "project_info" not in qd:
        # Migrate existing project info if it exists
        username = st.session_state.get("username", "demo")
        default_quote_ref = f"Q{username[0].upper()}001"
        
        qd["project_info"] = {
            "name": qd.get("project_name", ""),
            "client": qd.get("client_name", ""),
            "location": qd.get("project_location", ""),
            "notes": qd.get("project_notes", ""),
            "quote_ref": qd.get("quote_ref", default_quote_ref),
        }
    
    if "fan" not in qd:
        # Migrate existing fan data if it exists
        qd["fan"] = {
            "config_id": qd.get("fan_config_id"),
            "uid": qd.get("fan_uid"),
            "hub_size_mm": qd.get("fan_hub"),
            "blade_sets": qd.get("blade_sets"),
            "markup_override": qd.get("markup_override", 1.2),  # Default markup
            "selected_components": qd.get("selected_components_unordered", []),
        }
    
    if "component_details" not in qd:
        # Preserve existing component details
        qd["component_details"] = qd.get("component_details", {})
    
    if "motor" not in qd:
        # Migrate existing motor data if it exists
        motor_details = qd.get("selected_motor_details")
        if motor_details is None:
            motor_details = {}
            
        qd["motor"] = {
            "details": motor_details,
            "mount_type": qd.get("motor_mount_type"),
            "price": qd.get("motor_price"),
            "markup_override": qd.get("motor_markup_override"),
            "price_after_markup": qd.get("motor_price_after_markup"),
        }
    
    if "buyout_items" not in qd:
        # Migrate existing buyout items
        buyout_items = qd.get("buy_out_items_list")
        if buyout_items is None:
            buyout_items = []
            
        qd["buyout_items"] = buyout_items
    
    # Ensure all nested structures have their required fields
    if not isinstance(qd.get("project_info"), dict):
        qd["project_info"] = {}
    if not isinstance(qd.get("fan"), dict):
        qd["fan"] = {}
    if not isinstance(qd.get("component_details"), dict):
        qd["component_details"] = {}
    if not isinstance(qd.get("motor"), dict):
        qd["motor"] = {}
    if not isinstance(qd.get("buyout_items"), list):
        qd["buyout_items"] = []
    
    # Keep legacy fields in sync with new structure during transition period
    # This will help avoid breaking existing code that relies on the old structure
    _sync_new_and_legacy_structures()

def _update_blade_sets(widget_key):
    """
    Update both the new and legacy structures when blade sets change
    """
    if widget_key in st.session_state:
        blade_sets_value = st.session_state[widget_key]
        # Try to convert to integer if possible
        try:
            blade_sets_value = int(blade_sets_value)
        except (ValueError, TypeError):
            pass
            
        # Update both structures
        st.session_state.quote_data["fan"]["blade_sets"] = blade_sets_value
        st.session_state.quote_data["blade_sets"] = blade_sets_value
        
        logger.debug(f"[DEBUG] Updated blade_sets to {blade_sets_value}")

def _update_component_selection():
    """
    Update both the new and legacy structures when component selection changes
    """
    if "widget_fc_multiselect_components" in st.session_state:
        selected_components = st.session_state["widget_fc_multiselect_components"]
            
        # Update both structures
        st.session_state.quote_data["selected_components_unordered"] = selected_components
        if "fan" in st.session_state.quote_data:
            st.session_state.quote_data["fan"]["selected_components"] = selected_components
        
        logger.debug(f"[DEBUG] Updated selected components to {selected_components}")

def _sync_new_and_legacy_structures():
    """
    Keep the new nested structure and legacy flat structure in sync.
    This is a temporary function during the transition period.
    """
    qd = st.session_state.quote_data
    
    try:
        # Ensure all required dictionaries exist to avoid errors
        project_info = qd.get("project_info")
        if not isinstance(project_info, dict):
            project_info = {}
            qd["project_info"] = project_info
            
        fan = qd.get("fan")
        if not isinstance(fan, dict):
            fan = {}
            qd["fan"] = fan
            
        motor = qd.get("motor")
        if not isinstance(motor, dict):
            motor = {}
            qd["motor"] = motor
        
        # Project Info sync
        qd["project_name"] = project_info.get("name", "")
        qd["client_name"] = project_info.get("client", "")
        qd["project_location"] = project_info.get("location", "")
        qd["project_notes"] = project_info.get("notes", "")
        qd["quote_ref"] = project_info.get("quote_ref", qd.get("quote_ref", ""))
        
        # Fan config sync
        qd["fan_config_id"] = fan.get("config_id")
        qd["fan_uid"] = fan.get("uid")
        qd["fan_hub"] = fan.get("hub_size_mm")
        qd["blade_sets"] = fan.get("blade_sets")
        qd["markup_override"] = fan.get("markup_override", 1.2)  # Default value if None
        
        # Handle array fields specifically to avoid None errors
        selected_components = fan.get("selected_components")
        if not isinstance(selected_components, list):
            selected_components = []
        qd["selected_components_unordered"] = selected_components
        
        # Motor sync
        motor_details = motor.get("details")
        if not isinstance(motor_details, dict):
            motor_details = {}
        qd["selected_motor_details"] = motor_details
        
        qd["motor_mount_type"] = motor.get("mount_type")
        qd["motor_price"] = motor.get("price")
        qd["motor_markup_override"] = motor.get("markup_override", 1.0)  # Default value if None
        qd["motor_price_after_markup"] = motor.get("price_after_markup")
        
        # Buyout items sync
        buyout_items = qd.get("buyout_items")
        if not isinstance(buyout_items, list):
            buyout_items = []
        qd["buy_out_items_list"] = buyout_items
    
    except Exception as e:
        logger.error(f"Error in _sync_new_and_legacy_structures: {str(e)}")
        # If anything goes wrong, we should ensure we have at least empty structures
        if "project_info" not in qd:
            qd["project_info"] = {}
        if "fan" not in qd:
            qd["fan"] = {}
        if "motor" not in qd:
            qd["motor"] = {}
        if "component_details" not in qd:
            qd["component_details"] = {}
        if "buyout_items" not in qd:
            qd["buyout_items"] = []

# --- Updated Callback Functions ---

def update_project_info(field_name: str, widget_key: str):
    """
    Update a specific field in the project_info section of quote_data
    """
    if "callback_counters" not in st.session_state:
        st.session_state.callback_counters = {
            "top_level_key": 0,
            "component_detail": 0
        }
    
    st.session_state.callback_counters["top_level_key"] += 1
    logger.debug(f"[DEBUG] Project info callback fired {st.session_state.callback_counters['top_level_key']} times")
    
    logger.debug(f"[DEBUG] Project info widget change: {widget_key} = {st.session_state.get(widget_key)}")
    
    if widget_key in st.session_state:
        # Ensure project_info exists
        if "project_info" not in st.session_state.quote_data:
            st.session_state.quote_data["project_info"] = {}
            
        # Update the field
        old_value = st.session_state.quote_data.get("project_info", {}).get(field_name)
        st.session_state.quote_data["project_info"][field_name] = st.session_state[widget_key]
        logger.debug(f"[DEBUG] Updated project_info: {field_name} = {st.session_state.quote_data['project_info'][field_name]} (was {old_value})")
        
        # Keep legacy structure in sync
        _sync_new_and_legacy_structures()

def _update_quote_data_top_level_key(qd_top_level_key, widget_sstate_key):
    """
    Callback to update a key in st.session_state.quote_data
    from a widget's state in st.session_state.
    
    This is maintained for backward compatibility with the original flat structure.
    New code should use the more specific update functions.
    """
    # Ensure callback_counters is initialized
    if "callback_counters" not in st.session_state:
        st.session_state.callback_counters = {
            "top_level_key": 0,
            "component_detail": 0
        }
    
    # Ensure quote_data structure is initialized
    init_quote_data_structure()
    
    st.session_state.callback_counters["top_level_key"] += 1
    logger.debug(f"[DEBUG] Top-level callback fired {st.session_state.callback_counters['top_level_key']} times")

    logger.debug(f"[DEBUG] Top-level widget change: {widget_sstate_key} = {st.session_state.get(widget_sstate_key)}")

    old_value = st.session_state.quote_data.get(qd_top_level_key)
    logger.debug(f"[DEBUG] Old value in quote_data: {old_value}")

    if widget_sstate_key in st.session_state:
        # Update the legacy flat structure
        st.session_state.quote_data[qd_top_level_key] = st.session_state[widget_sstate_key]
        logger.debug(f"[DEBUG] Updated quote_data: {qd_top_level_key} = {st.session_state.quote_data[qd_top_level_key]}")
        
        # Also update the new nested structure if this is a field we're tracking
        # Project info fields
        if qd_top_level_key == "project_name":
            st.session_state.quote_data["project_info"]["name"] = st.session_state[widget_sstate_key]
        elif qd_top_level_key == "client_name":
            st.session_state.quote_data["project_info"]["client"] = st.session_state[widget_sstate_key]
        elif qd_top_level_key == "project_location":
            st.session_state.quote_data["project_info"]["location"] = st.session_state[widget_sstate_key]
        elif qd_top_level_key == "project_notes":
            st.session_state.quote_data["project_info"]["notes"] = st.session_state[widget_sstate_key]
        elif qd_top_level_key == "quote_ref":
            st.session_state.quote_data["project_info"]["quote_ref"] = st.session_state[widget_sstate_key]
        # Fan config fields
        elif qd_top_level_key == "fan_config_id":
            st.session_state.quote_data["fan"]["config_id"] = st.session_state[widget_sstate_key]
        elif qd_top_level_key == "fan_uid":
            st.session_state.quote_data["fan"]["uid"] = st.session_state[widget_sstate_key]
        elif qd_top_level_key == "fan_hub":
            st.session_state.quote_data["fan"]["hub_size_mm"] = st.session_state[widget_sstate_key]
        elif qd_top_level_key == "blade_sets":
            st.session_state.quote_data["fan"]["blade_sets"] = st.session_state[widget_sstate_key]
        elif qd_top_level_key == "markup_override":
            st.session_state.quote_data["fan"]["markup_override"] = st.session_state[widget_sstate_key]
        elif qd_top_level_key == "selected_components_unordered":
            st.session_state.quote_data["fan"]["selected_components"] = st.session_state[widget_sstate_key]

@st.cache_data
def get_all_fan_configs() -> Optional[List[Dict]]:
    """
    Fetches the list of all available fan configurations from the API.
    Each item in the list is a dictionary representing a fan configuration.
    Returns a list of dictionaries on success, None on failure.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/fans/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: Could not fetch fan configurations. {e}")
        return None

@st.cache_data
def get_available_components(fan_config_id: int) -> Optional[List[Dict]]:
    """
    Fetches the list of components available for a specific fan configuration ID.
    Returns a list of component dictionaries on success, None on failure.
    """
    if not fan_config_id:
        return [] # No components if no fan is selected

    try:
        response = requests.get(f"{API_BASE_URL}/fans/{fan_config_id}/components")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: Could not fetch available components for fan ID {fan_config_id}. {e}")
        return None

def _handle_fan_id_change():
    """Callback to handle changes in Fan ID selection."""
    qd = st.session_state.quote_data
    # The widget now provides the UID of the selected fan
    selected_fan_uid = st.session_state.get("widget_fc_fan_id")

    # Get all fan configurations from the cached API call
    all_configs = get_all_fan_configs()
    if not all_configs:
        # Error is already shown by the helper function, just clear state
        st.session_state.current_fan_config = None
        # Clear both legacy and new structure fields
        qd.update({"fan_config_id": None, "fan_uid": None, "fan_hub": None, "blade_sets": None, "selected_components_unordered": []})
        if "fan" in qd:
            qd["fan"].update({
                "config_id": None,
                "uid": None,
                "hub_size_mm": None,
                "blade_sets": None,
                "selected_components": []
            })
        return

    # Find the full configuration for the selected UID
    selected_config = next((c for c in all_configs if c['uid'] == selected_fan_uid), None)

    # If user selects the placeholder or the selection is invalid, clear everything
    if not selected_config:
        st.session_state.current_fan_config = None
        # Clear both legacy and new structure fields
        qd.update({"fan_config_id": None, "fan_uid": None, "fan_hub": None, "blade_sets": None, "selected_components_unordered": []})
        if "fan" in qd:
            qd["fan"].update({
                "config_id": None,
                "uid": None,
                "hub_size_mm": None,
                "blade_sets": None,
                "selected_components": []
            })
        return

    # A valid fan was selected. Update session state.
    st.session_state.current_fan_config = selected_config
    
    # Get fan markup from the selected config
    markup_override = selected_config.get('markup_override', 1.2)  # Default to 1.2 if not set

    # We store the integer 'id' for future API calls and the 'uid' for display.
    # Update both legacy and new structure
    qd["fan_config_id"] = selected_config.get('id')
    qd["fan_uid"] = selected_config.get('uid')
    qd["fan_hub"] = selected_config.get('hub_size_mm')
    qd["markup_override"] = markup_override
    
    # Also update the new nested structure
    if "fan" in qd:
        qd["fan"]["config_id"] = selected_config.get('id')
        qd["fan"]["uid"] = selected_config.get('uid')
        qd["fan"]["hub_size_mm"] = selected_config.get('hub_size_mm')
        qd["fan"]["markup_override"] = markup_override

    # Update blade quantity options based on the new fan
    available_blades = selected_config.get('available_blade_qtys', [])
    str_available_blades = [str(b) for b in available_blades]

    if str_available_blades:
        # If the currently selected blade quantity is not valid for the new fan,
        # default to the first available option.
        current_blade_set = str(qd.get("blade_sets")) if qd.get("blade_sets") is not None else None
        if current_blade_set not in str_available_blades:
            blade_sets_value = int(str_available_blades[0])
            qd["blade_sets"] = blade_sets_value
            if "fan" in qd:
                qd["fan"]["blade_sets"] = blade_sets_value
    else:
        # No blade options for this fan
        qd["blade_sets"] = None
        if "fan" in qd:
            qd["fan"]["blade_sets"] = None

    # --- Auto-select default components for the new fan ---
    auto_select_ids = selected_config.get('auto_selected_components', [])
    if auto_select_ids:
        available_components = get_available_components(qd["fan_config_id"])
        if available_components:
            id_to_name_map = {comp['id']: comp['name'] for comp in available_components}
            # Translate the auto-select IDs to names, preserving order if needed (though not critical here)
            auto_selected_names = [id_to_name_map[id] for id in auto_select_ids if id in id_to_name_map]
            qd["selected_components_unordered"] = auto_selected_names
            if "fan" in qd:
                qd["fan"]["selected_components"] = auto_selected_names
        else:
            qd["selected_components_unordered"] = [] # API call failed or no components
            if "fan" in qd:
                qd["fan"]["selected_components"] = []
    else:
        qd["selected_components_unordered"] = [] # No auto-select components defined
        if "fan" in qd:
            qd["fan"]["selected_components"] = []
    
    # Make sure both structures are fully in sync
    _sync_new_and_legacy_structures()
    
    logger.debug(f"[DEBUG] After fan selection - Legacy fan_config_id: {qd.get('fan_config_id')}")
    logger.debug(f"[DEBUG] After fan selection - New fan.config_id: {qd.get('fan', {}).get('config_id')}")
    logger.debug(f"[DEBUG] After fan selection - Components: {qd.get('selected_components_unordered')}")

def render_sidebar_widgets():
    """Renders the specific sidebar widgets for Fan Configuration."""
    # Initialize/update the nested structure
    init_quote_data_structure()
    
    if "current_fan_config" not in st.session_state: # Initialize for API response
        st.session_state.current_fan_config = None

    qd = st.session_state.quote_data

    with st.sidebar:
        st.divider()
        st.subheader("Base Fan Parameters")

        # 1. Fan ID Selectbox (API Driven by full fan configs)
        all_fan_configs = get_all_fan_configs()
        # The options for the selectbox are the user-friendly UIDs
        fan_uid_options = ["--- Please select a Fan ID ---"]
        if all_fan_configs:
            # Sort by fan size for a consistent, logical order in the dropdown
            sorted_configs = sorted(all_fan_configs, key=lambda c: c['fan_size_mm'])
            fan_uid_options.extend([c['uid'] for c in sorted_configs])
        else:
            st.caption("Could not load Fan IDs from API.") # Error is already shown by get_all_fan_configs

        # The selectbox should display the currently selected fan UID
        # Get fan_uid from either new or legacy structure
        current_fan_uid = None
        if "fan" in qd and isinstance(qd["fan"], dict):
            current_fan_uid = qd["fan"].get("uid")
        if current_fan_uid is None:
            current_fan_uid = qd.get("fan_uid")
            
        fan_uid_idx = 0
        if current_fan_uid and current_fan_uid in fan_uid_options:
            fan_uid_idx = fan_uid_options.index(current_fan_uid)
            
        st.selectbox(
            "Fan ID", options=fan_uid_options,
            index=fan_uid_idx,
            key="widget_fc_fan_id",
            on_change=_handle_fan_id_change
        )

        fan_config = st.session_state.get("current_fan_config")

        # Note: The Fan Hub is now displayed below in the st.metric widget
        # when a fan configuration is selected.

        # 3. Blade Sets (Blade Quantity - API Driven, dependent on Fan ID)
        blade_qty_select_options = ["N/A"]
        blade_qty_disabled = True
        blade_qty_idx = 0
        
        if fan_config and fan_config.get('available_blade_qtys'):
            blade_qty_select_options = [str(bq) for bq in fan_config.get('available_blade_qtys')]
            blade_qty_disabled = False
            # Get blade sets from the new structure first, fall back to legacy
            current_blade_sets_val = str(qd["fan"].get("blade_sets")) if qd["fan"].get("blade_sets") is not None else str(qd.get("blade_sets")) if qd.get("blade_sets") is not None else None
            if current_blade_sets_val and current_blade_sets_val in blade_qty_select_options:
                blade_qty_idx = blade_qty_select_options.index(current_blade_sets_val)
        elif qd["fan"].get("blade_sets") or qd.get("blade_sets"): # Show existing if no new options yet
            blade_sets_val = qd["fan"].get("blade_sets") or qd.get("blade_sets")
            blade_qty_select_options = [str(blade_sets_val)]

        st.selectbox(
            "Blade Sets", options=blade_qty_select_options,
            index=blade_qty_idx,
            key="widget_fc_blade_sets",
            on_change=lambda: _update_blade_sets("widget_fc_blade_sets"),
            disabled=blade_qty_disabled,
            help="Options populated after selecting a Fan ID."
        )
        
        if fan_config:
            # Display the fetched data in a more structured way
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="Fan Size (mm)", value=fan_config.get('fan_size_mm', 'N/A'))
                st.text_input("Available Blade Counts", value=", ".join(map(str, fan_config.get('available_blade_qtys', []))), disabled=True)
                st.text_input("Available Motor kW", value=", ".join(map(str, fan_config.get('available_motor_kw', []))), disabled=True)
            with col2:
                st.metric(label="Hub Size (mm)", value=fan_config.get('hub_size_mm', 'N/A'))
                st.text_input("Blade Name & Material", value=f"{fan_config.get('blade_name', 'N/A')} ({fan_config.get('blade_material', 'N/A')})", disabled=True)
                st.text_input("Motor Poles", value=str(fan_config.get('motor_pole', 'N/A')), disabled=True)
            
            # Optionally, show the raw JSON data for debugging
            with st.expander("Show Raw API Response"):
                st.json(fan_config)
        else:
            st.info("Select a Fan ID to view its configuration details.")

        st.divider()

        # --- Component Selection ---
        st.subheader("Fan Components Selection")

        component_options = []
        is_disabled = True
        
        if fan_config:
            fan_config_id = fan_config.get('id')
            # Fetch components available for the selected fan
            available_components = get_available_components(fan_config_id)
            if available_components:
                # The API returns components pre-sorted by 'order_by'. We just extract the names.
                component_options = [comp['name'] for comp in available_components]
                is_disabled = False

        # Get selected components from either new or legacy structure
        current_selection = []
        if "fan" in qd and isinstance(qd["fan"], dict):
            current_selection = qd["fan"].get("selected_components", [])
        if not current_selection:
            current_selection = qd.get("selected_components_unordered", [])
            
        valid_selection = [comp for comp in current_selection if comp in component_options]
        
        # Update both structures
        qd["selected_components_unordered"] = valid_selection
        if "fan" in qd:
            qd["fan"]["selected_components"] = valid_selection

        # Get markup from either new or legacy structure
        markup_value = None
        if "fan" in qd and isinstance(qd["fan"], dict):
            markup_value = qd["fan"].get("markup_override")
        if markup_value is None:
            markup_value = qd.get("markup_override")
            
        default_markup = 1.4 # Default if no markup is found
        
        # If a fan config is selected but no markup set, try to get the markup from the fan config
        if fan_config and (markup_value is None):
            markup_value = fan_config.get('markup_override', default_markup)
            
        if markup_value is None:
            markup_value = default_markup
            
        markup_input = st.number_input(
            "Markup Override",
            min_value=1.0,
            value=float(markup_value),
            step=0.01,
            format="%.2f",
            key="widget_markup_override",
            on_change=_update_quote_data_top_level_key,
            args=("markup_override", "widget_markup_override"),
            help="Override the default markup for the selected components.",
            disabled=is_disabled
        )

        st.multiselect(
            "Select Fan Components",
            options=component_options,
            default=valid_selection,
            key="widget_fc_multiselect_components",
            on_change=_update_component_selection,
            help="Select a Fan ID to populate this list.",
            disabled=is_disabled
        )
        
        st.divider()

        # Test button for direct markup update
        if st.button("Test Direct Markup Update"):
            logger.debug("[DEBUG] Test Direct Markup Update button clicked.")
            # Get current value
            current_markup = st.session_state.quote_data.get("markup_override", 1.4)
            # Update by a small amount
            st.session_state.quote_data["markup_override"] = current_markup + 0.01
            # Try to trigger recalculation
            ensure_server_summary_up_to_date(st.session_state.quote_data)
            st.rerun()
