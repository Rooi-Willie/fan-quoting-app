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

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

# --- Stage 2 Nested Schema Support ---
NEW_SCHEMA_VERSION = 2

def _new_nested_quote_data(username: str | None = None) -> Dict:
    """Create a fresh nested quote_data structure (schema version 2).

    This will progressively replace the previous flat structure. Some
    sections (motor, calculation.settings_snapshot) may start partially empty
    and be populated later by user interaction or API calls.
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
        "project": {
            "name": "",
            "client": "",
            "location": "",
            "notes": "",
            "reference": f"Q{ref_user[:1].upper()}001",
        },
        "fan": {
            "config_id": None,
            "uid": None,
            "hub_size_mm": None,
            "blade_sets": None,
        },
        "components": {
            "selected": [],  # ordered by API order
            "by_name": {},   # name -> {overrides:{..}, calculated:{..}}
        },
        "motor": {
            "selection": None,  # dict from motor table
            "mount_type": None,
            "base_price": None,
            "markup_override": None,
            "final_price": None,
        },
        "buy_out_items": [],  # list of {id, description, qty, unit_cost, subtotal}
        "calculation": {
            "markup_override": 1.4,
            "server_summary": {},
            "derived_totals": {},
        },
        "settings_snapshot": {},
    }

def migrate_flat_to_nested_if_needed(data: Dict) -> Dict:
    """Upgrade an older flat quote_data dict to the new nested schema.

    This is idempotent: if meta.version>=NEW_SCHEMA_VERSION returns unchanged.
    Only minimal mapping for currently used fields; legacy keys are left in place
    (can be pruned later) to avoid breaking code still transitioning.
    """
    if not isinstance(data, dict):
        return _new_nested_quote_data()
    meta = data.get("meta") or {}
    if isinstance(meta, dict) and meta.get("version", 0) >= NEW_SCHEMA_VERSION:
        return data  # Already new

    # Create base new structure
    username = meta.get("created_by") if isinstance(meta, dict) else None
    upgraded = _new_nested_quote_data(username)

    # Project fields
    upgraded["project"]["name"] = data.get("project_name", "")
    upgraded["project"]["client"] = data.get("client_name", "")
    upgraded["project"]["location"] = data.get("project_location", "")
    upgraded["project"]["notes"] = data.get("project_notes", "")
    if data.get("quote_ref"):
        upgraded["project"]["reference"] = data["quote_ref"]

    # Fan
    upgraded["fan"].update({
        "config_id": data.get("fan_config_id"),
        "uid": data.get("fan_uid"),
        "hub_size_mm": data.get("fan_hub"),
        "blade_sets": data.get("blade_sets"),
    })

    # Components selection
    legacy_selected = data.get("selected_components_unordered") or []
    upgraded["components"]["selected"] = list(legacy_selected)
    legacy_details = data.get("component_details") or {}
    for name, det in legacy_details.items():
        overrides = {}
        if isinstance(det, dict):
            # Map known override labels
            if "Material Thickness" in det:
                overrides["material_thickness_mm"] = det["Material Thickness"]
            if "Fabrication Waste" in det:
                overrides["fabrication_waste_pct"] = det["Fabrication Waste"]
        upgraded["components"]["by_name"][name] = {"overrides": overrides, "calculated": {}}

    # Markup (general) -> calculation.markup_override
    if "markup_override" in data:
        upgraded["calculation"]["markup_override"] = data.get("markup_override")

    # Motor
    motor_selection = data.get("selected_motor_details")
    if motor_selection:
        upgraded["motor"]["selection"] = motor_selection
        upgraded["motor"]["mount_type"] = data.get("motor_mount_type")
        upgraded["motor"]["markup_override"] = data.get("motor_markup_override")
        upgraded["motor"]["final_price"] = data.get("motor_price_after_markup")

    # Buy-out items
    legacy_buyouts = data.get("buy_out_items_list") or []
    if isinstance(legacy_buyouts, list):
        upgraded["buy_out_items"] = legacy_buyouts

    # Server summary if present
    if "server_summary" in st.session_state:
        upgraded["calculation"]["server_summary"] = st.session_state.get("server_summary") or {}

    # Stamp updated_at
    from datetime import datetime as _dt
    upgraded["meta"]["updated_at"] = _dt.utcnow().isoformat()+"Z"
    # Prune legacy keys now that upgraded structure is created
    upgraded = prune_legacy_flat_keys(upgraded)
    return upgraded


def prune_legacy_flat_keys(qd: Dict) -> Dict:
    """Remove deprecated flat schema keys once nested schema is authoritative.

    Safe to call multiple times; ignores missing keys. Only removes keys that
    have migrated equivalents in the nested structure.
    """
    if not isinstance(qd, dict):
        return qd
    legacy_keys = [
        "fan_config_id", "fan_uid", "fan_hub", "blade_sets", "selected_components_unordered",
        "component_details", "markup_override", "motor_price_after_markup", "motor_markup_override",
        "quote_ref", "buy_out_items_list", "server_summary"
    ]
    for k in legacy_keys:
        qd.pop(k, None)
    return qd


def recompute_all_components(request_func) -> None:
    """Utility to recompute all selected components' calculated data in-place.

    Parameters
    ----------
    request_func : callable
        A function accepting a hashable request_payload_tuple and returning a
        result dict (mirrors get_component_details in fan_config_tab).

    Behavior
    --------
    - Ensures quote_data migrated.
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
    """Handle fan UID selection change updating nested schema (and legacy keys)."""
    # Ensure quote_data exists & migrated
    if "quote_data" not in st.session_state or not isinstance(st.session_state.quote_data, dict):
        st.session_state.quote_data = _new_nested_quote_data()
    else:
        st.session_state.quote_data = migrate_flat_to_nested_if_needed(st.session_state.quote_data)

    qd = st.session_state.quote_data
    selected_fan_uid = st.session_state.get("widget_fc_fan_id")
    all_configs = get_all_fan_configs()
    if not all_configs:
        st.session_state.current_fan_config = None
        qd.setdefault("fan", {}).update({"config_id": None, "uid": None, "hub_size_mm": None, "blade_sets": None})
        qd.setdefault("components", {}).setdefault("selected", [])
        return
    selected_config = next((c for c in all_configs if c['uid'] == selected_fan_uid), None)
    if not selected_config:
        st.session_state.current_fan_config = None
        qd.setdefault("fan", {}).update({"config_id": None, "uid": None, "hub_size_mm": None, "blade_sets": None})
        qd.setdefault("components", {}).setdefault("selected", [])
        return

    st.session_state.current_fan_config = selected_config
    fan_node = qd.setdefault("fan", {})
    fan_node.update({
        "config_id": selected_config.get('id'),
        "uid": selected_config.get('uid'),
        "hub_size_mm": selected_config.get('hub_size_mm'),
    })

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
    qd.setdefault("components", {}).setdefault("selected", [])
    qd["components"]["selected"] = comp_sel


def render_sidebar_widgets():
    """Render the sidebar using the nested schema.

    Keeps legacy flat keys in sync temporarily for unmigrated tabs.
    """
    # Ensure quote_data exists & migrated
    if "quote_data" not in st.session_state or not isinstance(st.session_state.quote_data, dict):
        st.session_state.quote_data = _new_nested_quote_data()
    else:
        st.session_state.quote_data = migrate_flat_to_nested_if_needed(st.session_state.quote_data)
    if "current_fan_config" not in st.session_state:
        st.session_state.current_fan_config = None
    qd = st.session_state.quote_data
    fan_node = qd.setdefault("fan", {})
    calc_node = qd.setdefault("calculation", {})
    comp_node = qd.setdefault("components", {})
    comp_node.setdefault("selected", [])
    calc_node.setdefault("markup_override", 1.4)

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
            args=(("fan","blade_sets"), "widget_fc_blade_sets",),
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
        current_selection = comp_node.get("selected", [])
        valid_selection = [c for c in current_selection if c in component_options]
        comp_node["selected"] = valid_selection

        # Markup override number input (nested calculation.markup_override)
        st.number_input(
            "Markup Override",
            min_value=1.0,
            value=float(calc_node.get("markup_override", 1.4)),
            step=0.01,
            format="%.2f",
            key="widget_markup_override",
            on_change=update_quote_data_nested,
            args=(("calculation","markup_override"), "widget_markup_override"),
            help="Override the default markup for the selected components.",
            disabled=is_disabled,
        )

        st.multiselect(
            "Select Fan Components",
            options=component_options,
            default=valid_selection,
            key="widget_fc_multiselect_components",
            on_change=update_quote_data_nested,
            args=(("components","selected"), "widget_fc_multiselect_components"),
            help=(
                "Select a Fan ID to populate this list. "
                "If ordering matters it will be handled later in the component tab."
            ),
            disabled=is_disabled,
        )

        st.divider()
        if st.sidebar.button("Test Direct Markup Update"):
            current_markup = calc_node.get("markup_override", 1.4)
            calc_node["markup_override"] = current_markup + 0.01
            # No legacy mirror; nested only
            ensure_server_summary_up_to_date(qd)
            st.rerun()
