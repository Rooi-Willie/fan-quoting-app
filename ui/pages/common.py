"""Shared Streamlit UI helpers for the Create New Quote flow.

Stage 2 NOTE:
This module now supports the nested quote_data schema (version 2). Some
legacy flat keys are still written for transitional compatibility with
tabs not yet migrated (e.g. review / buy-out). These will be removed once
all consumers are updated. New code should read & write ONLY the nested
structure (meta/project/fan/components/motor/buy_out_items/calculation).
"""
from __future__ import annotations

import os
from typing import Optional, List, Dict
import requests
import streamlit as st

from utils import ensure_server_summary_up_to_date
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

# --- Schema v3 Support ---
NEW_SCHEMA_VERSION = 3

def _new_v3_quote_data(username: str | None = None) -> Dict:
    """Create a fresh v3 quote_data structure (Business Context schema).

    This replaces the v2 nested structure with a clean, organized v3 schema.
    No migration logic needed - new quotes start fresh with this structure.
    """
    import datetime as _dt
    ref_user = (username or "demo").split("@")[0]
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
                "config_id": None,
                "uid": None,
                "fan_size_mm": None,
                "hub_size_mm": None,
                "blade_sets": None,
            },
            "motor": {
                "selection_id": None,
                "mount_type": None,
                "supplier_name": None,
                "rated_output": None,
                "poles": None,
            },
            "components": [],
            "buyouts": [],
        },
        "pricing": {
            "component_markup": 1.0,
            "motor_markup": 1.2,
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
            "totals": {
                "components": 0.0,
                "motor": 0.0,
                "buyouts": 0.0,
                "grand_total": 0.0,
            },
        },
        "context": {
            "fan_configuration": {},
            "motor_details": {},
            "rates_and_settings": {},
        },
    }

def recompute_all_components(request_func) -> None:
    """Utility to recompute all selected components' calculated data in-place.

    Parameters
    ----------
    request_func : callable
        A function accepting a hashable request_payload_tuple and returning a
        result dict (mirrors get_component_details in fan_config_tab).

    Behavior
    --------
    Ensures quote_data is v3 format.
    Iterates specification.components preserving order.
    Builds request payload per component using pricing.overrides and current fan node.
    Writes results into calculations.components[name].
    Silently skips components lacking an id mapping.
    """
    if "quote_data" not in st.session_state:
        return
    qd = st.session_state.quote_data
    if not isinstance(qd, dict) or qd.get("meta", {}).get("version") != NEW_SCHEMA_VERSION:
        return  # Only work with v3 schema
    
    spec = qd.get("specification", {})
    fan = spec.get("fan", {})
    pricing = qd.get("pricing", {})
    calc = qd.setdefault("calculations", {})
    selected = spec.get("components", [])
    overrides = pricing.get("overrides", {})
    fan_config_id = fan.get("config_id")
    available = get_available_components(fan_config_id) if fan_config_id else []
    id_map = {c['name']: c['id'] for c in available} if available else {}

    for comp_name in selected:
        comp_id = id_map.get(comp_name)
        if not comp_id:
            continue
        
        # Build request payload
        comp_overrides = overrides.get(comp_name, {})
        payload = {
            "fan_configuration_id": fan_config_id,
            "component_id": comp_id,
            "blade_quantity": int(fan.get("blade_sets", 8)),
            "thickness_mm_override": comp_overrides.get("thickness_mm"),
            "fabrication_waste_factor_override": comp_overrides.get("waste_pct", 0) / 100.0 if comp_overrides.get("waste_pct") else None,
        }
        
        # Call calculation function
        result = request_func(tuple(sorted(payload.items())))
        if result:
            calc.setdefault("components", {})[comp_name] = result
    
    # Stamp back
    st.session_state.quote_data = qd
    - Iterates components.selected preserving order.
    - Builds request payload per component (using overrides & current fan node).
    - Writes results into components.by_name[name].calculated.
    - Silently skips components lacking an id mapping (caller must manage id resolution).
    """
    if "quote_data" not in st.session_state:
        return
    qd = migrate_flat_to_nested_if_needed(st.session_state.quote_data)
    fan = qd.get("fan", {})
    comps = qd.get("components", {})
    calc = qd.get("calculation", {})
    selected = comps.get("selected", [])
    by_name = comps.setdefault("by_name", {})
    fan_config_id = fan.get("config_id")
    available = get_available_components(fan_config_id) if fan_config_id else []
    id_map = {c['name']: c['id'] for c in available} if available else {}

    for comp_name in selected:
        comp_id = id_map.get(comp_name)
        if comp_id is None:
            continue
        overrides = by_name.setdefault(comp_name, {}).setdefault("overrides", {})
        fabrication_waste_percentage = overrides.get("fabrication_waste_pct")
        fabrication_waste_factor = (fabrication_waste_percentage / 100.0) if fabrication_waste_percentage is not None else None
        request_payload = {
            "fan_configuration_id": fan_config_id,
            "component_id": comp_id,
            "blade_quantity": int(fan.get("blade_sets", 0)) if fan.get("blade_sets") else None,
            "thickness_mm_override": overrides.get("material_thickness_mm"),
            "fabrication_waste_factor_override": fabrication_waste_factor,
            "markup_override": calc.get("markup_override"),
        }
        request_payload_tuple = tuple(sorted(request_payload.items()))
        result = request_func(request_payload_tuple)
        if result:
            by_name.setdefault(comp_name, {})["calculated"] = result
    # Stamp back
    st.session_state.quote_data = qd


def update_quote_data_top_level_key(qd_top_level_key: str, widget_sstate_key: str):
    if "quote_data" not in st.session_state:
        return
    if widget_sstate_key in st.session_state:
        st.session_state.quote_data[qd_top_level_key] = st.session_state[widget_sstate_key]


def update_quote_data_nested(path: List[str], widget_sstate_key: str, mirror_legacy: Optional[str] = None):
    """Generic nested updater for quote_data.

    path: list of keys drilling into the nested quote_data dict.
    widget_sstate_key: key in st.session_state containing the value.
    mirror_legacy: optional legacy top-level key also updated for compatibility.
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
    if mirror_legacy:
        qd[mirror_legacy] = st.session_state[widget_sstate_key]


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
        spec.setdefault("fan", {}).update({"config_id": None, "uid": None, "fan_size_mm": None, "hub_size_mm": None, "blade_sets": None})
        spec.setdefault("components", [])
        return
    selected_config = next((c for c in all_configs if c['uid'] == selected_fan_uid), None)
    if not selected_config:
        st.session_state.current_fan_config = None
        spec = qd.setdefault("specification", {})
        spec.setdefault("fan", {}).update({"config_id": None, "uid": None, "fan_size_mm": None, "hub_size_mm": None, "blade_sets": None})
        spec.setdefault("components", [])
        return

    st.session_state.current_fan_config = selected_config
    spec = qd.setdefault("specification", {})
    fan_node = spec.setdefault("fan", {})
    fan_node.update({
        "config_id": selected_config.get('id'),
        "uid": selected_config.get('uid'),
        "fan_size_mm": selected_config.get('fan_size_mm'),
        "hub_size_mm": selected_config.get('hub_size_mm'),
    })

    # If no markup set yet, fetch default from global settings API
    pricing = qd.setdefault("pricing", {})
    if pricing.get("component_markup") in (None, ""):
        try:
            resp = requests.get(f"{API_BASE_URL}/settings/global")
            if resp.ok:
                settings = resp.json()
                default_markup = settings.get("default_markup")
                try:
                    pricing["component_markup"] = float(default_markup)
                except (TypeError, ValueError):
                    pricing.setdefault("component_markup", 1.0)
        except Exception:
            pricing.setdefault("component_markup", 1.0)

    available_blades = selected_config.get('available_blade_qtys', [])
    blades_str = [str(b) for b in available_blades]
    if blades_str:
        current_blade = str(fan_node.get("blade_sets")) if fan_node.get("blade_sets") is not None else None
        if current_blade not in blades_str:
            fan_node["blade_sets"] = blades_str[0]
    else:
        fan_node["blade_sets"] = None

    # Auto-selected components
    auto_select_ids = selected_config.get('auto_selected_components', [])
    comp_sel: List[str] = []
    if auto_select_ids:
        comps = get_available_components(fan_node["config_id"])
        if comps:
            id_to_name = {c['id']: c['name'] for c in comps}
            comp_sel = [id_to_name[i] for i in auto_select_ids if i in id_to_name]
    spec.setdefault("components", [])
    spec["components"] = comp_sel


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
        fan_uid_options = ["--- Please select a Fan ID ---"]
        if all_fan_configs:
            sorted_configs = sorted(all_fan_configs, key=lambda c: c['fan_size_mm'])
            fan_uid_options.extend([c['uid'] for c in sorted_configs])
        else:
            st.caption("Could not load Fan IDs from API.")
        current_fan_uid = fan_node.get("uid")
        fan_uid_idx = fan_uid_options.index(current_fan_uid) if current_fan_uid in fan_uid_options else 0
        st.selectbox(
            "Fan ID",
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
            args=(("specification","fan","blade_sets"), "widget_fc_blade_sets",),
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
        current_selection = spec.get("components", [])
        valid_selection = [c for c in current_selection if c in component_options]
        spec["components"] = valid_selection

    # Markup override number input (nested pricing.component_markup)
    st.number_input(
            "Markup Override",
            min_value=1.0,
            value=float(pricing.get("component_markup", 1.0)),
            step=0.01,
            format="%.2f",
            key="widget_markup_override",
            on_change=update_quote_data_nested,
            args=(("pricing","component_markup"), "widget_markup_override"),
            help="Override the default markup for the selected components.",
            disabled=is_disabled,
        )
    st.multiselect(
            "Select Fan Components",
            options=component_options,
            default=valid_selection,
            key="widget_fc_multiselect_components",
            on_change=update_quote_data_nested,
            args=(("specification","components"), "widget_fc_multiselect_components"),
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
            st.rerun()
