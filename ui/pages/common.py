"""Shared Streamlit UI helpers for the Create New Quote flow.

v3 Schema Implementation:
This module supports the v3 nested quote_data schema with clean section organization:
- meta: metadata and versioning
- quote: project and client information
- specification: technical specifications (fan, motor, components, buyouts)
- pricing: pricing data (motor, component overrides)
- calculations: computed values and server results
- context: runtime context (fan_configuration, motor_details, rates_and_settings)
"""
from __future__ import annotations

import os
from typing import Optional, List, Dict
import requests
import streamlit as st

from utils import ensure_server_summary_up_to_date

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

# --- Schema v3 Support ---
NEW_SCHEMA_VERSION = 3

def _fetch_default_markups() -> tuple[float, float]:
    """Fetch default markup values from the global settings API.
    
    Returns:
        tuple[float, float]: A tuple containing (component_markup, motor_markup)
                           with fallback values if API call fails.
    """
    component_default = 1.0  # Fallback value
    motor_default = 1.2      # Fallback value
    
    try:
        resp = requests.get(f"{API_BASE_URL}/settings/global")
        if resp.ok:
            settings = resp.json()
            # Get component markup from 'default_markup' key
            if "default_markup" in settings:
                try:
                    component_default = float(settings["default_markup"])
                except (TypeError, ValueError):
                    pass  # Keep fallback value
            
            # Get motor markup from 'default_motor_markup' key
            if "default_motor_markup" in settings:
                try:
                    motor_default = float(settings["default_motor_markup"])
                except (TypeError, ValueError):
                    pass  # Keep fallback value
    except requests.exceptions.RequestException:
        pass  # Keep fallback values
    
    return component_default, motor_default

def _fetch_rates_and_settings() -> dict:
    """Fetch current rates and settings from the API during quote initialization.
    
    Returns:
        dict: A dictionary containing all rates and settings, or empty dict if API fails.
    """
    try:
        resp = requests.get(f"{API_BASE_URL}/settings/rates-and-settings")
        if resp.ok:
            return resp.json()
    except requests.exceptions.RequestException:
        pass  # Return empty dict on error
    return {}

def _new_v3_quote_data(username: str | None = None) -> Dict:
    """Create a fresh v3 quote_data structure (Business Context schema).

    This replaces the v2 nested structure with a clean, organized v3 schema.
    No migration logic needed - new quotes start fresh with this structure.
    Fetches default markup values from the global settings API.
    """
    import datetime as _dt
    ref_user = (username or "demo").split("@")[0]
    
    # Fetch default markup values from the API
    component_markup, motor_markup = _fetch_default_markups()
    
    # Fetch rates and settings for context population
    rates_and_settings = _fetch_rates_and_settings()
    
    return {
        "meta": {
            "version": NEW_SCHEMA_VERSION,
            "created_at": _dt.datetime.utcnow().isoformat()+"Z",
            "updated_at": _dt.datetime.utcnow().isoformat()+"Z",
            "created_by": ref_user,
        },
        "quote": {
            "reference": f"Q{ref_user[:1].upper()}001",
            "client": "",
            "project": "",
            "location": "",
            "notes": "",
        },
        "specification": {
            "fan": {
                "blade_sets": None,
                "fan_configuration": {},
            },
            "motor": {
                "mount_type": None,
                "motor_details": {},
            },
            "components": [],
            "buyouts": [],
        },
        "pricing": {
            "component_markup": component_markup,
            "motor_markup": motor_markup,
            "overrides": {},
        },
        "calculations": {
            "timestamp": None,
            "components": {},
            "component_totals": {
                "total_length_mm": 0.0,
                "total_mass_kg": 0.0,
                "total_labour_cost": 0.0,
                "total_material_cost": 0.0,
                "subtotal_cost": 0.0,
                "final_price": 0.0,
            },
            "motor": {
                "base_price": 0.0,
                "final_price": 0.0,
            },
            "totals": {
                "components": 0.0,
                "motor": 0.0,
                "buyouts": 0.0,
                "grand_total": 0.0,
            },
        },
        "context": {
            "rates_and_settings": {
                "timestamp": _dt.datetime.utcnow().isoformat()+"Z",
                "full_settings_data": rates_and_settings if rates_and_settings else {}
            },
        },
    }

def update_quote_data_top_level_key(qd_top_level_key: str, widget_sstate_key: str):
    if "quote_data" not in st.session_state:
        return
    if widget_sstate_key in st.session_state:
        st.session_state.quote_data[qd_top_level_key] = st.session_state[widget_sstate_key]


def update_quote_data_nested(path: List[str], widget_sstate_key: str):
    """Generic nested updater for quote_data using v3 schema.

    path: list of keys drilling into the nested quote_data dict.
    widget_sstate_key: key in st.session_state containing the value.
    """
    if "quote_data" not in st.session_state:
        return
    if widget_sstate_key not in st.session_state:
        return
    qd = st.session_state.quote_data
    cur = qd
    for k in path[:-1]:
        cur = cur.setdefault(k, {})
    cur[path[-1]] = st.session_state[widget_sstate_key]

def update_quote_data_with_recalc(path: List[str], widget_sstate_key: str):
    """Enhanced updater that updates quote_data AND triggers immediate calculation refresh.
    
    This prevents the "one step behind" issue by ensuring calculations are updated
    synchronously with UI input changes.
    """
    # First update the quote data
    update_quote_data_nested(path, widget_sstate_key)
    
    # Immediately trigger calculation updates
    if "quote_data" in st.session_state:
        qd = st.session_state.quote_data
        
        # Import here to avoid circular imports
        from utils import update_quote_totals, ensure_server_summary_up_to_date
        
        # Force server summary refresh if components exist
        if qd.get("calculations", {}).get("components"):
            ensure_server_summary_up_to_date(qd)
        
        # Update local totals immediately
        update_quote_totals(qd)


## Legacy update_component_detail_from_widget_state removed (nested overrides used directly)


@st.cache_data
def get_all_fan_configs() -> Optional[List[Dict]]:
    try:
        resp = requests.get(f"{API_BASE_URL}/fans/")
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: Could not fetch fan configurations. {e}")
        return None


@st.cache_data
def get_available_components(fan_config_id: int) -> Optional[List[Dict]]:
    if not fan_config_id:
        return []
    try:
        resp = requests.get(f"{API_BASE_URL}/fans/{fan_config_id}/components")
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: Could not fetch available components for fan ID {fan_config_id}. {e}")
        return None


def _handle_component_selection():
    """Handle component multiselect change - store components as objects with id and name."""
    if "quote_data" not in st.session_state:
        return
    
    selected_names = st.session_state.widget_fc_multiselect_components
    qd = st.session_state.quote_data
    
    # Get current fan configuration to fetch available components with IDs
    fan_config = st.session_state.get("current_fan_config")
    if not fan_config:
        return
    
    available_components = get_available_components(fan_config.get("id"))
    if not available_components:
        return
    
    # Create name to component mapping
    name_to_component = {comp['name']: comp for comp in available_components}
    
    # Convert selected names to component objects
    component_objects = []
    for name in selected_names:
        if name in name_to_component:
            comp = name_to_component[name]
            component_objects.append({
                "id": comp["id"],
                "name": comp["name"]
            })
    
    # Store as objects in specification.components
    spec = qd.setdefault("specification", {})
    spec["components"] = component_objects
    
    # ENHANCED: Clear calculations cache and trigger immediate recalculation
    # This prevents stale totals when components are added/removed
    calculations = qd.setdefault("calculations", {})
    
    # Clear component calculations that are no longer selected
    if "components" in calculations:
        selected_names_set = set(selected_names)
        calculations["components"] = {
            name: calc_data for name, calc_data in calculations["components"].items()
            if name in selected_names_set
        }
    
    # Trigger immediate total recalculation
    from utils import update_quote_totals
    update_quote_totals(qd)


def _handle_fan_id_change():
    """Handle fan UID selection change updating v3 schema."""
    # Ensure quote_data exists in v3 format
    if "quote_data" not in st.session_state or not isinstance(st.session_state.quote_data, dict):
        st.session_state.quote_data = _new_v3_quote_data()
    
    qd = st.session_state.quote_data
    if qd.get("meta", {}).get("version") != NEW_SCHEMA_VERSION:
        # If not v3, start fresh
        st.session_state.quote_data = _new_v3_quote_data()
        qd = st.session_state.quote_data

    selected_fan_uid = st.session_state.get("widget_fc_fan_id")
    all_configs = get_all_fan_configs()
    if not all_configs:
        st.session_state.current_fan_config = None
        spec = qd.setdefault("specification", {})
        spec.setdefault("fan", {}).update({
            "config_id": None, "uid": None, "fan_size_mm": None, 
            "hub_size_mm": None, "blade_sets": None
        })
        spec.setdefault("components", [])
        return
    
    selected_config = next((c for c in all_configs if c['uid'] == selected_fan_uid), None)
    if not selected_config:
        st.session_state.current_fan_config = None
        spec = qd.setdefault("specification", {})
        spec.setdefault("fan", {}).update({
            "config_id": None, "uid": None, "fan_size_mm": None, 
            "hub_size_mm": None, "blade_sets": None
        })
        spec.setdefault("components", [])
        return

    st.session_state.current_fan_config = selected_config
    spec = qd.setdefault("specification", {})
    fan_node = spec.setdefault("fan", {})
    fan_node.update({
        "fan_configuration": selected_config,
    })
    
    # No longer populate context.fan_configuration as it's moved to specification.fan.fan_configuration
    
    # Ensure pricing section exists with defaults (should already be set from _new_v3_quote_data)
    pricing = qd.setdefault("pricing", {})
    if "component_markup" not in pricing or pricing["component_markup"] is None:
        # Fetch defaults if somehow missing (fallback safety)
        component_markup, _ = _fetch_default_markups()
        pricing["component_markup"] = component_markup

    available_blades = selected_config.get('available_blade_qtys', [])
    blades_str = [str(b) for b in available_blades]
    if blades_str:
        current_blade = str(fan_node.get("blade_sets")) if fan_node.get("blade_sets") is not None else None
        if current_blade not in blades_str:
            fan_node["blade_sets"] = blades_str[0]
    else:
        fan_node["blade_sets"] = None

    # Auto-selected components - store as objects with id and name
    auto_select_ids = selected_config.get('auto_selected_components', [])
    comp_objects = []
    if auto_select_ids:
        comps = get_available_components(selected_config.get('id'))
        if comps:
            id_to_component = {c['id']: c for c in comps}
            comp_objects = [
                {"id": comp_id, "name": id_to_component[comp_id]["name"]} 
                for comp_id in auto_select_ids 
                if comp_id in id_to_component
            ]
    spec.setdefault("components", [])
    spec["components"] = comp_objects


def recompute_all_components(request_func) -> None:
	"""Utility to recompute all selected components' calculated data in-place.
	
	Updated for v3 schema compatibility.
	
	Parameters
	----------
	request_func : callable
		A function accepting a hashable request_payload_tuple and returning a
		result dict (mirrors get_component_details in fan_config_tab).
		
	Behavior
	--------
	- Ensures quote_data uses v3 schema.
	- Iterates specification.components preserving order.
	- Builds request payload per component (using overrides & current fan config).
	- Writes results into calculations.components[name].
	- Silently skips components lacking an id mapping.
	"""
	if "quote_data" not in st.session_state:
		return
		
	qd = st.session_state.quote_data
	if not isinstance(qd, dict):
		return
	
	# Get v3 schema sections
	spec = qd.get("specification", {})
	fan_config = spec.get("fan", {})
	selected_components = spec.get("components", [])
	calculations_components = qd.setdefault("calculations", {}).setdefault("components", {})
	
	fan_config_id = fan_config.get("config_id")
	markup_override = qd.get("pricing", {}).get("component_markup")
	
	# Process component objects with id and name
	for comp_item in selected_components:
		comp_id = comp_item.get("id")
		comp_name = comp_item.get("name")
			
		if comp_id is None or not comp_name:
			continue
			
		# Get component overrides from pricing.overrides
		comp_overrides = qd.get("pricing", {}).get("overrides", {}).get(comp_name, {})
		
		# Build request payload
		fabrication_waste_percentage = comp_overrides.get("fabrication_waste_pct")
		fabrication_waste_factor = (fabrication_waste_percentage / 100.0) if fabrication_waste_percentage is not None else None
		
		request_payload = {
			"fan_configuration_id": fan_config_id,
			"component_id": comp_id,
			"blade_quantity": int(fan_config.get("blade_sets", 0)) if fan_config.get("blade_sets") else None,
			"thickness_mm_override": comp_overrides.get("material_thickness_mm"),
			"fabrication_waste_factor_override": fabrication_waste_factor,
			"markup_override": markup_override,
		}
		
		request_payload_tuple = tuple(sorted(request_payload.items()))
		result = request_func(request_payload_tuple)
		
		if result:
			calculations_components[comp_name] = result
	
	# Update session state
	st.session_state.quote_data = qd


def render_sidebar_widgets():
	"""Render the sidebar using the v3 schema."""
	# Ensure quote_data exists in v3 format
	if "quote_data" not in st.session_state or not isinstance(st.session_state.quote_data, dict):
		st.session_state.quote_data = _new_v3_quote_data()
	
	qd = st.session_state.quote_data
	if qd.get("meta", {}).get("version") != NEW_SCHEMA_VERSION:
		# If not v3, start fresh
		st.session_state.quote_data = _new_v3_quote_data()
		qd = st.session_state.quote_data
	
	if "current_fan_config" not in st.session_state:
		st.session_state.current_fan_config = None
	
	spec = qd.setdefault("specification", {})
	fan_node = spec.setdefault("fan", {})
	pricing = qd.setdefault("pricing", {})
	pricing.setdefault("component_markup", 1.0)

	with st.sidebar:
		st.divider()
		st.subheader("Base Fan Parameters")
		all_fan_configs = get_all_fan_configs()
		fan_uid_options = ["--- Please select a Fan Configuration ---"]
		if all_fan_configs:
			sorted_configs = sorted(all_fan_configs, key=lambda c: c['fan_size_mm'])
			fan_uid_options.extend([c['uid'] for c in sorted_configs])
		else:
			st.caption("Could not load Fan IDs from API.")
		
		current_fan_uid = fan_node.get("uid")
		fan_uid_idx = fan_uid_options.index(current_fan_uid) if current_fan_uid in fan_uid_options else 0
		st.selectbox(
			"Fan Configuration",
			options=fan_uid_options,
			index=fan_uid_idx,
			key="widget_fc_fan_id",
			on_change=_handle_fan_id_change,
		)
		
		fan_config = st.session_state.get("current_fan_config")
		blade_qty_select_options = ["N/A"]
		blade_qty_disabled = True
		blade_qty_idx = 0
		existing_blade_sets = fan_node.get("blade_sets")
		if fan_config and fan_config.get('available_blade_qtys'):
			blade_qty_select_options = [str(bq) for bq in fan_config.get('available_blade_qtys')]
			blade_qty_disabled = False
			current_blade_val = str(existing_blade_sets) if existing_blade_sets is not None else None
			if current_blade_val in blade_qty_select_options:
				blade_qty_idx = blade_qty_select_options.index(current_blade_val)
		elif existing_blade_sets:
			blade_qty_select_options = [str(existing_blade_sets)]
		
		st.selectbox(
			"Blade Sets",
			options=blade_qty_select_options,
			index=blade_qty_idx,
			key="widget_fc_blade_sets",
			on_change=update_quote_data_nested,
			args=(["specification", "fan", "blade_sets"], "widget_fc_blade_sets"),
			disabled=blade_qty_disabled,
			help="Options populated after selecting a Fan ID."
		)

		if fan_config:
			col1, col2 = st.columns(2)
			with col1:
				st.metric("Fan Size (mm)", fan_config.get('fan_size_mm', 'N/A'))
				st.text_input("Available Blade Counts", value=", ".join(map(str, fan_config.get('available_blade_qtys', []))), disabled=True)
				st.text_input("Available Motor kW", value=", ".join(map(str, fan_config.get('available_motor_kw', []))), disabled=True)
			with col2:
				st.metric("Hub Size (mm)", fan_config.get('hub_size_mm', 'N/A'))
				st.text_input("Blade Name & Material", value=f"{fan_config.get('blade_name', 'N/A')} ({fan_config.get('blade_material', 'N/A')})", disabled=True)
				st.text_input("Motor Poles", value=str(fan_config.get('motor_pole', 'N/A')), disabled=True)
			with st.expander("Show Raw API Response"):
				st.json(fan_config)
		else:
			st.info("Select a Fan ID to view its configuration details.")
		
		st.divider()
		st.subheader("Fan Components Selection")
		component_options: List[str] = []
		is_disabled = True
		if fan_config:
			fan_config_id = fan_config.get('id')
			comps = get_available_components(fan_config_id)
			if comps:
				component_options = [c['name'] for c in comps]
				is_disabled = False
		
		# Extract component names for multiselect from component objects
		current_selection = spec.get("components", [])
		current_names = [c.get("name") for c in current_selection if isinstance(c, dict) and "name" in c]
		valid_selection = [c for c in current_names if c in component_options]

		# Component markup number input (v3: pricing.component_markup)
		# Get current markup value, ensuring it's a valid float
		current_component_markup = pricing.get("component_markup")
		if current_component_markup is None:
			# Fallback: fetch from API if missing
			current_component_markup, _ = _fetch_default_markups()
			pricing["component_markup"] = current_component_markup
		
		try:
			markup_value = float(current_component_markup)
		except (TypeError, ValueError):
			markup_value = 1.0  # Final fallback
			
		st.number_input(
			"Component Markup",
			min_value=1.0,
			value=markup_value,
			step=0.01,
			format="%.2f",
			key="widget_markup_override",
			on_change=update_quote_data_with_recalc,
			args=(["pricing", "component_markup"], "widget_markup_override"),
			help="Markup multiplier for component pricing (default loaded from database).",
			disabled=is_disabled,
		)
		
		st.multiselect(
			"Select Fan Components",
			options=component_options,
			default=valid_selection,
			key="widget_fc_multiselect_components",
			on_change=_handle_component_selection,
			help=(
				"Select a Fan ID to populate this list. "
				"If ordering matters it will be handled later in the component tab."
			),
			disabled=is_disabled,
		)
		
		st.divider()
		if st.button("Test Direct Markup Update"):
			current_markup = pricing.get("component_markup", 1.0)
			pricing["component_markup"] = current_markup + 0.01
			ensure_server_summary_up_to_date(qd)
			# ENHANCED: Update totals immediately to prevent lag
			from utils import update_quote_totals
			update_quote_totals(qd)
			st.rerun()
		
		# Ensure totals are calculated if component data exists
		from utils import update_quote_totals
		if qd.get("calculations", {}).get("components"):
			update_quote_totals(qd)
