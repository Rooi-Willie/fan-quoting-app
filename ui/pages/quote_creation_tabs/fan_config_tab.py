import streamlit as st
import os
import pandas as pd  # Keep for potential future use
from typing import Optional, List, Dict
import requests
from config import COMPONENT_ORDER, COMPONENT_IMAGES, ROW_DEFINITIONS, IMAGE_FOLDER_PATH, CURRENCY_SYMBOL
from utils import ensure_server_summary_up_to_date, build_summary_dataframe
from pages.common import recompute_all_components
from pages.common import (
    get_available_components,
    get_all_fan_configs,
)
import logging

# Configure basic logging (optional, but good for quick setup)
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

## Local callbacks moved to pages.common

## Removed duplicated cached API helpers (now provided in pages.common)

@st.cache_data
def get_component_details(request_payload_tuple: tuple) -> Optional[Dict]:
    """
    Posts a request to the single-component calculation endpoint.
    The request body dictionary is passed as a tuple to make it hashable for caching.
    """
    if not request_payload_tuple:
        return None

    request_payload = dict(request_payload_tuple)

    try:
        response = requests.post(f"{API_BASE_URL}/quotes/components/calculate-details", json=request_payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: Could not calculate component details. {e}")
        try:
            st.json(response.json())
        except:
            st.text(response.text)
        return None

## Removed local _handle_fan_id_change and render_sidebar_widgets (moved to pages.common)

def render_main_content():
    """Renders the main content area for the Fan Configuration tab."""
    st.header("3. Fan Configuration Details")

    if "quote_data" not in st.session_state:
        # This should ideally be handled by the main page (2_Create_New_Quote.py)
        st.error("Quote data not initialized. Please start a new quote or refresh.")
        return

    # Work with v3 schema structure
    qd = st.session_state.quote_data
    
    # Extract v3 sections
    spec_section = qd.setdefault("specification", {})
    pricing_section = qd.setdefault("pricing", {})
    calc_section = qd.setdefault("calculations", {})
    
    # Fan configuration in specification.fan (v3 schema)
    fan_config = spec_section.setdefault("fan", {})
    
    # Components in specification.components (v3 schema - simple array of names)
    components_list = spec_section.setdefault("components", [])
    
    # Component overrides in pricing.overrides (v3 schema)
    component_overrides = pricing_section.setdefault("overrides", {})

    st.subheader("Configure Selected Fan Components")

    # Derive the ordered list for processing from the API-provided order
    fan_config_id = fan_config.get("config_id")  # v3 uses config_id, not id
    available_components_list = get_available_components(fan_config_id)
    if available_components_list:
        ordered_available_names = [comp['name'] for comp in available_components_list]
        # In v3, components_list is a simple array of component names
        user_selected_names = components_list  # components_list is already a list of names
        ordered_selected_components = [name for name in ordered_available_names if name in user_selected_names]
    else:
        ordered_selected_components = []

    if not ordered_selected_components:
        st.info("Select fan components from the sidebar to configure them.")
        return

    name_to_id_map = {comp['name']: comp['id'] for comp in available_components_list}

    for comp_name in ordered_selected_components:
        if comp_name not in name_to_id_map:
            continue

        component_id = name_to_id_map[comp_name]
        
        # Prepare request for this single component
        # Overrides stored in pricing.overrides[comp_name] in v3 structure
        overrides = component_overrides.setdefault(comp_name, {})
        
        fabrication_waste_percentage = overrides.get("fabrication_waste_pct")
        fabrication_waste_factor = (fabrication_waste_percentage / 100.0) if fabrication_waste_percentage is not None else None

        request_payload = {
            "fan_configuration_id": fan_config_id,
            "component_id": component_id,
            "blade_quantity": int(fan_config.get("blade_sets", 0)) if fan_config.get("blade_sets") else None,
            "thickness_mm_override": overrides.get("material_thickness_mm"),
            "fabrication_waste_factor_override": fabrication_waste_factor,
            "markup_override": pricing_section.get("component_markup")  # v3: component markup location
        }
        
        # Make it hashable for st.cache_data
        request_payload_tuple = tuple(sorted(request_payload.items()))

        # Call API and store result
        result = get_component_details(request_payload_tuple)
        if result:
            # Store calculated results in calculations.components[comp_name] in v3 structure
            calc_section.setdefault("components", {})[comp_name] = result

    # --- Display Area ---
    num_selected_components = len(ordered_selected_components)
    column_layout_config = [1.5] + [1] * num_selected_components

    # --- Component Image Row ---
    image_cols = st.columns(column_layout_config)
    with image_cols[0]: st.markdown("**Image**")
    for i, comp_name in enumerate(ordered_selected_components):
        with image_cols[i + 1]:
            image_full_path = COMPONENT_IMAGES.get(comp_name)
            if image_full_path and os.path.exists(image_full_path):
                st.image(image_full_path, use_column_width='always', caption=comp_name[:15]+"...")
            else:
                st.markdown("*(No Image)*")

    # --- Header Row for Parameters ---
    header_cols = st.columns(column_layout_config)
    with header_cols[0]: st.markdown("**Parameter**")
    for i, comp_name in enumerate(ordered_selected_components):
        with header_cols[i + 1]: st.markdown(f"**{comp_name}**", help=comp_name)
    st.divider()

    # --- Data Input/Display Area ---
    api_response_rows = [
        ("Overall Diameter", "overall_diameter_mm", "mm"),
        ("Total Length", "total_length_mm", "mm"),
        ("Material Thickness", "material_thickness_mm", "mm"),
        ("Stiffening Factor", "stiffening_factor", "factor"),
        ("Ideal Mass", "ideal_mass_kg", "kg"),
        ("Real Mass", "real_mass_kg", "kg"),
        ("Fabrication Waste", "fabrication_waste_percentage", "%"),
        ("Feedstock Mass", "feedstock_mass_kg", "kg"),
        ("Material Cost", "material_cost", CURRENCY_SYMBOL),
        ("Labour Cost", "labour_cost", CURRENCY_SYMBOL),
        ("Cost Before Markup", "total_cost_before_markup", CURRENCY_SYMBOL),
        ("Cost After Markup", "total_cost_after_markup", CURRENCY_SYMBOL),
    ]
    # dividers = [3, 7]
    dividers = [8]

    # Extract calculated results from v3 structure
    calculated_components = calc_section.get("components", {})
    component_calcs = {k: v for k, v in calculated_components.items() if k in ordered_selected_components}

    for row_idx, (row_label, api_field, unit) in enumerate(api_response_rows):
        if row_idx in dividers:
            st.divider()
            
        param_row_cols = st.columns(column_layout_config)
        with param_row_cols[0]:
            display_label = f"{row_label} ({unit})" if unit not in ["factor", "%"] else row_label
            st.markdown(display_label)
            if unit in ["factor", "%"]:
                 st.caption(f"Unit: {unit}")

        for comp_idx, comp_name in enumerate(ordered_selected_components):
            with param_row_cols[comp_idx + 1]:
                widget_key = f"fc_{comp_name}_{row_label.replace(' ', '_')}"
                api_value = component_calcs.get(comp_name, {}).get(api_field)

                # IMPORTANT: fetch per-component overrides INSIDE loop.
                # Previous bug: code referenced outer 'overrides' variable from
                # the initial pre-fetch loop, so all widgets wrote to the LAST
                # component's overrides dict. This rebind ensures isolation.
                overrides_local = component_overrides.setdefault(comp_name, {})

                if row_label in ["Material Thickness", "Fabrication Waste"]:
                    if row_label == "Fabrication Waste":
                        default_value = api_value if api_value is not None else 15.0
                        current_value = overrides_local.get("fabrication_waste_pct", default_value)
                    else:  # Material Thickness
                        default_value = api_value if api_value is not None else 5.0
                        current_value = overrides_local.get("material_thickness_mm", default_value)

                    user_value = st.number_input(
                        label=f"_{widget_key}",
                        label_visibility="collapsed",
                        value=float(current_value),
                        step=1.0,
                        format="%.1f",
                        key=widget_key,
                    )
                    changed = (user_value != current_value)
                    if row_label == "Fabrication Waste":
                        overrides_local["fabrication_waste_pct"] = user_value
                    else:
                        overrides_local["material_thickness_mm"] = user_value
                    
                    if changed:
                        # CRITICAL: Ensure session state is synchronized and force recompute
                        st.session_state.quote_data = qd
                        # Clear any cached component details to force fresh calculations
                        if hasattr(st.session_state, '_cache'):
                            st.session_state._cache.clear()
                        # Force cache clear for get_component_details
                        get_component_details.clear()
                        recompute_all_components(get_component_details)
                        ensure_server_summary_up_to_date(qd)
                        # Force UI refresh to show updated calculations
                        st.rerun()
                else:
                    if api_value is not None:
                        if isinstance(api_value, (int, float)):
                            if unit == CURRENCY_SYMBOL:
                                st.text(f"{api_value:.2f}")
                            elif unit == "factor":
                                st.text(f"{api_value:.3f}")
                            else:
                                st.text(f"{api_value:.1f}")
                        else:
                            st.text(str(api_value))
                    else:
                        st.text("N/A")

    # --- Selected Component Summary ---
    st.divider()
    st.subheader("Component Summary")

    # safe accessor (already built above)

    def _sum_field(name):
        return sum((c.get(name) or 0) for c in component_calcs.values())

    total_length_mm = _sum_field("total_length_mm")
    total_ideal_mass_kg = _sum_field("ideal_mass_kg")
    total_real_mass_kg = _sum_field("real_mass_kg")
    total_feedstock_mass_kg = _sum_field("feedstock_mass_kg")
    total_material_cost = _sum_field("material_cost")
    total_labour_cost = _sum_field("labour_cost")
    subtotal_cost = _sum_field("total_cost_before_markup")
    final_price = _sum_field("total_cost_after_markup")
    markup_pct = ((final_price / subtotal_cost) - 1) * 100 if subtotal_cost > 0 else 0.0

    # Prefer authoritative server totals when available
    server_summary = st.session_state.get("server_summary") or {}
    if server_summary:
        total_length_mm = server_summary.get("total_length_mm", total_length_mm) or 0
        total_real_mass_kg = server_summary.get("total_mass_kg", total_real_mass_kg) or 0
        # Ideal mass and feedstock may not be returned by the server; keep UI values if missing
        total_material_cost = server_summary.get("total_material_cost", total_material_cost) or 0
        total_labour_cost = server_summary.get("total_labour_cost", total_labour_cost) or 0
        subtotal_cost = server_summary.get("subtotal_cost", subtotal_cost) or 0
        final_price = server_summary.get("final_price", final_price) or 0

        markup_applied = server_summary.get("markup_applied")
        if isinstance(markup_applied, (int, float)):
            # markup_applied is a multiplier (e.g., 1.40) -> convert to %
            markup_pct = (markup_applied - 1.0) * 100.0
        else:
            markup_pct = ((final_price / subtotal_cost) - 1) * 100 if subtotal_cost > 0 else 0.0

    # KPI display (unchanged UI, now prefers server totals if present)
    kpi_col_1, kpi_col_2, kpi_col_3 = st.columns(3)
    with kpi_col_1:
        st.metric("Total Mass (real)", f"{total_real_mass_kg:.2f} kg")
        st.metric("Total Ideal Mass", f"{total_ideal_mass_kg:.2f} kg")
    with kpi_col_2:
        st.metric("Total Length", f"{total_length_mm:.0f} mm")
        st.metric("Feedstock Mass", f"{total_feedstock_mass_kg:.2f} kg")
    with kpi_col_3:
        st.metric("Material Cost", f"{CURRENCY_SYMBOL} {total_material_cost:.2f}")
        st.metric("Labour Cost", f"{CURRENCY_SYMBOL} {total_labour_cost:.2f}")

    st.divider()
    # Pricing row
    price_col_1, price_col_2, price_col_3 = st.columns(3)
    with price_col_1:
        st.metric("Subtotal (before markup)", f"{CURRENCY_SYMBOL} {subtotal_cost:.2f}")
    with price_col_2:
        st.metric("Final Price (after markup)", f"{CURRENCY_SYMBOL} {final_price:.2f}")
    with price_col_3:
        st.metric("Markup Applied", f"{markup_pct:.1f}%")

    st.divider()
    st.caption("Provisional totals calculated from the component results currently in the UI. Press 'Recalculate server totals' before finalising to get authoritative values.")

    # Per-component compact table for quick inspection
    if component_calcs:
        rows = []
        for name, c in component_calcs.items():
            rows.append({
                "Component": name,
                "Length (mm)": c.get("total_length_mm"),
                "Real Mass (kg)": c.get("real_mass_kg"),
                "Material Cost": c.get("material_cost"),
                "Labour Cost": c.get("labour_cost"),
                "Cost Before Markup": c.get("total_cost_before_markup"),
                "Cost After Markup": c.get("total_cost_after_markup"),
            })
        styler = build_summary_dataframe(rows, CURRENCY_SYMBOL)
        st.write(styler)

    # Action to explicitly request authoritative server totals (using shared helper)
    recalc_col1, recalc_col2 = st.columns([1, 3])
    with recalc_col1:
        if st.button("Recalculate server totals"):
            ensure_server_summary_up_to_date(qd)
            if st.session_state.get("server_summary"):
                st.success("Server totals updated.")
            else:
                st.warning("Could not update server totals. Check API logs.")
    with recalc_col2:
        st.caption("Use this to fetch server-calculated totals (recommended before finalising).")

    # Status block for Stage 4 persistence keys
    calc_node = qd.get("calculation", {}) or {}
    status_cols = st.columns(3)
    with status_cols[0]:
        st.caption("server_summary")
        st.write("✅" if calc_node.get("server_summary") else "❌")
    with status_cols[1]:
        st.caption("derived_totals")
        st.write("✅" if calc_node.get("derived_totals") else "❌")
    with status_cols[2]:
        st.caption("rates_and_settings_used")
        st.write("✅" if calc_node.get("rates_and_settings_used") else "❌")

    with st.expander("View Raw Calculation Results"):
        st.json(component_calcs)