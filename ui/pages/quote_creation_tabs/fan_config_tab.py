import streamlit as st
import os
import pandas as pd # Keep for potential future use, though not strictly needed if not building DF here
from typing import Optional, List, Dict # Added for type hinting
import requests # Added for API calls
from config import COMPONENT_ORDER, COMPONENT_IMAGES, ROW_DEFINITIONS, IMAGE_FOLDER_PATH, CURRENCY_SYMBOL

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

def _update_component_detail_from_widget_state(component_name, detail_key, widget_sstate_key):
    """
    Callback to update a specific detail for a component in
    st.session_state.quote_data["component_details"].
    """
    qd = st.session_state.quote_data
    component_dict = qd.setdefault("component_details", {}).setdefault(component_name, {})

    if widget_sstate_key in st.session_state:
        component_dict[detail_key] = st.session_state[widget_sstate_key]

# --- API Helper Functions with Caching ---
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
        qd.update({"fan_config_id": None, "fan_uid": None, "fan_hub": None, "blade_sets": None, "selected_components_unordered": []})
        return

    # Find the full configuration for the selected UID
    selected_config = next((c for c in all_configs if c['uid'] == selected_fan_uid), None)

    # If user selects the placeholder or the selection is invalid, clear everything
    if not selected_config:
        st.session_state.current_fan_config = None
        qd.update({"fan_config_id": None, "fan_uid": None, "fan_hub": None, "blade_sets": None, "selected_components_unordered": []})
        return

    # A valid fan was selected. Update session state.
    st.session_state.current_fan_config = selected_config

    # We store the integer 'id' for future API calls and the 'uid' for display.
    qd["fan_config_id"] = selected_config.get('id')
    qd["fan_uid"] = selected_config.get('uid')
    qd["fan_hub"] = selected_config.get('hub_size_mm')

    # Update blade quantity options based on the new fan
    available_blades = selected_config.get('available_blade_qtys', [])
    str_available_blades = [str(b) for b in available_blades]

    if str_available_blades:
        # If the currently selected blade quantity is not valid for the new fan,
        # default to the first available option.
        current_blade_set = str(qd.get("blade_sets")) if qd.get("blade_sets") is not None else None
        if current_blade_set not in str_available_blades:
            qd["blade_sets"] = str_available_blades[0]
    else:
        # No blade options for this fan
        qd["blade_sets"] = None

    # --- Auto-select default components for the new fan ---
    auto_select_ids = selected_config.get('auto_selected_components', [])
    if auto_select_ids:
        available_components = get_available_components(qd["fan_config_id"])
        if available_components:
            id_to_name_map = {comp['id']: comp['name'] for comp in available_components}
            # Translate the auto-select IDs to names, preserving order if needed (though not critical here)
            auto_selected_names = [id_to_name_map[id] for id in auto_select_ids if id in id_to_name_map]
            qd["selected_components_unordered"] = auto_selected_names
        else:
            qd["selected_components_unordered"] = [] # API call failed or no components
    else:
        qd["selected_components_unordered"] = [] # No auto-select components defined

def render_sidebar_widgets():
    """Renders the specific sidebar widgets for Fan Configuration."""
    if "quote_data" not in st.session_state:
        st.warning("quote_data not found in session_state. Initializing.")
        st.session_state.quote_data = {}
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

        # Ensure the default selection is valid for the current fan's available components
        current_selection = qd.get("selected_components_unordered", [])
        valid_selection = [comp for comp in current_selection if comp in component_options]
        qd["selected_components_unordered"] = valid_selection # Update state with only valid items

        default_markup = 1.4 # Or fetch from a config/API if it can be dynamic
        markup_input = st.number_input(
            "Markup Override",
            min_value=1.0,
            value=float(qd.get("markup_override", default_markup)),
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
            on_change=_update_quote_data_top_level_key,
            args=("selected_components_unordered", "widget_fc_multiselect_components"),
            help="Select a Fan ID to populate this list.",
            disabled=is_disabled
        )
        st.divider()

def render_main_content():
    """Renders the main content area for the Fan Configuration tab."""
    st.header("3. Fan Configuration Details")

    if "quote_data" not in st.session_state:
        # This should ideally be handled by the main page (2_Create_New_Quote.py)
        st.error("Quote data not initialized. Please start a new quote or refresh.")
        return

    qd = st.session_state.quote_data
    cd = qd.setdefault("component_details", {})
    
    if "component_calculations" not in st.session_state:
        st.session_state.component_calculations = {}

    st.subheader("Configure Selected Fan Components")

    # Derive the ordered list for processing from the API-provided order
    fan_config_id = qd.get("fan_config_id")
    available_components_list = get_available_components(fan_config_id)
    if available_components_list:
        ordered_available_names = [comp['name'] for comp in available_components_list]
        user_selected_names = qd.get("selected_components_unordered", [])
        ordered_selected_components = [name for name in ordered_available_names if name in user_selected_names]
    else:
        ordered_selected_components = []

    if not ordered_selected_components:
        st.info("Select fan components from the sidebar to configure them.")
        st.session_state.component_calculations = {}
        return

    name_to_id_map = {comp['name']: comp['id'] for comp in available_components_list}

    for comp_name in ordered_selected_components:
        if comp_name not in name_to_id_map:
            continue

        component_id = name_to_id_map[comp_name]
        
        # Prepare request for this single component
        fabrication_waste_percentage = cd.get(comp_name, {}).get("Fabrication Waste")
        fabrication_waste_factor = fabrication_waste_percentage / 100.0 if fabrication_waste_percentage is not None else None

        request_payload = {
            "fan_configuration_id": fan_config_id,
            "component_id": component_id,
            "blade_quantity": int(qd.get("blade_sets", 0)) if qd.get("blade_sets") else None,
            "thickness_mm_override": cd.get(comp_name, {}).get("Material Thickness"),
            "fabrication_waste_factor_override": fabrication_waste_factor,
            "markup_override": qd.get("markup_override")
        }
        
        # Make it hashable for st.cache_data
        request_payload_tuple = tuple(sorted(request_payload.items()))

        # Call API and store result
        result = get_component_details(request_payload_tuple)
        if result:
            st.session_state.component_calculations[comp_name] = result

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

    component_calcs = st.session_state.component_calculations

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

                if row_label in ["Material Thickness", "Fabrication Waste"]:
                    if row_label == "Fabrication Waste":
                        default_value = api_value if api_value is not None else 15.0
                    else: # Material Thickness
                        default_value = api_value if api_value is not None else 5.0
                    current_value = cd.setdefault(comp_name, {}).get(row_label, default_value)
                    
                    user_value = st.number_input(
                        label=f"_{widget_key}",
                        label_visibility="collapsed",
                        value=float(current_value),
                        step=1.0,
                        format="%.1f",
                        key=widget_key,
                        on_change=_update_component_detail_from_widget_state,
                        args=(comp_name, row_label, widget_key)
                    )
                    cd[comp_name][row_label] = user_value
                else:
                    if api_value is not None:
                        if isinstance(api_value, (int, float)):
                            if unit == CURRENCY_SYMBOL: st.text(f"{api_value:.2f}")
                            elif unit == "factor": st.text(f"{api_value:.3f}")
                            else: st.text(f"{api_value:.1f}")
                        else:
                            st.text(str(api_value))
                    else:
                        st.text("N/A")

    # --- Selected Component Summary ---
    st.divider()
    st.subheader("Component Summary")

    # safe accessor
    component_calcs = st.session_state.get("component_calculations", {}) or {}

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

    # Top-level KPI row (grouped)
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

        df = pd.DataFrame(rows)

        # Append totals row using totals already computed above
        totals_row = {
            "Component": "TOTAL",
            "Length (mm)": float(total_length_mm or 0),
            "Real Mass (kg)": float(total_real_mass_kg or 0),
            "Material Cost": float(total_material_cost or 0),
            "Labour Cost": float(total_labour_cost or 0),
            "Cost Before Markup": float(subtotal_cost or 0),
            "Cost After Markup": float(final_price or 0),
        }
        df = pd.concat([df, pd.DataFrame([totals_row])], ignore_index=True, sort=False).fillna("N/A")

        # Styling: make the TOTAL row bold and larger font
        def _highlight_totals(row):
            return ['font-weight: bold; font-size: 20px; color: #66b1d1;' if row['Component'] == 'TOTAL' else '' for _ in row]

        def _fmt_length(x):
            return f"{int(x):,d}" if isinstance(x, (int, float)) else x
        def _fmt_float2(x):
            return f"{x:,.2f}" if isinstance(x, (int, float)) else x
        def _fmt_currency(x):
            return f"{CURRENCY_SYMBOL} {x:,.2f}" if isinstance(x, (int, float)) else x

        styler = df.style.apply(_highlight_totals, axis=1).format({
            "Length (mm)": _fmt_length,
            "Real Mass (kg)": _fmt_float2,
            "Material Cost": _fmt_currency,
            "Labour Cost": _fmt_currency,
            "Cost Before Markup": _fmt_currency,
            "Cost After Markup": _fmt_currency,
        })

        # Render styled table
        st.write(styler)

    # Action to explicitly request authoritative server totals (hook up your API endpoint)
    recalc_col1, recalc_col2 = st.columns([1, 3])
    with recalc_col1:
        if st.button("Recalculate server totals"):
            # Build payload for server summary
            comp_list = []
            available_map = {comp['name']: comp['id'] for comp in available_components_list or []}
            for name in ordered_selected_components:
                comp_id = available_map.get(name)
                overrides = cd.get(name, {})
                comp_list.append({
                    "component_id": comp_id,
                    "thickness_mm_override": overrides.get("Material Thickness"),
                    "fabrication_waste_factor_override": (overrides.get("Fabrication Waste") / 100.0) if overrides.get("Fabrication Waste") is not None else None
                })
            payload = {
                "fan_configuration_id": fan_config_id,
                "blade_quantity": int(qd.get("blade_sets", 0)) if qd.get("blade_sets") else None,
                "components": comp_list,
                "markup_override": qd.get("markup_override"),
                "motor_markup_override": qd.get("motor_markup_override")
            }
            try:
                resp = requests.post(f"{API_BASE_URL}/quotes/components/summary", json=payload)
                resp.raise_for_status()
                server_summary = resp.json()
                # Update UI with authoritative totals (or show them in a modal / info)
                st.session_state.server_summary = server_summary
                st.success("Server totals updated.")
            except requests.RequestException as e:
                st.error(f"Server error: {e}")
    with recalc_col2:
        st.caption("Use this to fetch server-calculated totals (recommended before finalising).")

    with st.expander("View Raw Calculation Results"):
        st.json(component_calcs)