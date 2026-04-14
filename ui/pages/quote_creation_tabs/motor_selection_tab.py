import math
import streamlit as st
import os
import requests
import pandas as pd
from typing import Optional, List, Dict
from utils import get_api_headers, sanitize_for_json

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8080")


@st.cache_data
def get_available_motors(
    available_kw: List[int], poles: Optional[int] = None
) -> Optional[List[Dict]]:
    """
    Fetches a list of available motors from the API based on a list of kW ratings
    and an optional poles filter. Returns a list of motor dictionaries on success,
    empty list if no kWs are provided, or None on error.
    """
    if not available_kw:
        return []

    try:
        params = {'available_kw': available_kw}
        if poles is not None:
            params['poles'] = poles
        response = requests.get(
            f"{API_BASE_URL}/motors/",
            params=params,
            headers=get_api_headers(),
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: Could not fetch available motors. {e}")
        return None


def _render_motor_summary_card(motor, motor_spec, currency):
    """Render a bordered card showing selected motor specs."""
    supplier = motor.get('supplier_name', 'Unknown')
    product_range = motor.get('product_range', 'N/A')
    rated_output = motor.get('rated_output', 'N/A')
    rated_unit = motor.get('rated_output_unit', 'kW')
    poles = motor.get('poles', 'N/A')
    speed = motor.get('speed', 'N/A')
    mount = motor_spec.get('mount_type', 'N/A')

    with st.container(border=True):
        st.markdown("##### Selected Motor")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f"**{supplier}** {product_range}  \n"
                f"**Output:** {rated_output} {rated_unit} | "
                f"**Poles:** {poles} | "
                f"**Speed:** {speed} RPM"
            )
        with col2:
            st.markdown(f"**Mount:** {mount}")


def _render_pricing_card(
    base_price, discount_percentage, motor_markup, final_price, currency
):
    """Render a bordered card showing the pricing breakdown."""
    discount_multiplier = 1.0 - (discount_percentage / 100.0)
    discounted_price = base_price * discount_multiplier

    with st.container(border=True):
        st.markdown("##### Pricing Summary")
        if discount_percentage > 0:
            cols = st.columns(4)
            with cols[0]:
                st.metric("Base Price", f"{currency} {base_price:,.2f}")
            with cols[1]:
                st.metric(
                    "After Discount",
                    f"{currency} {discounted_price:,.2f}",
                    delta=f"-{discount_percentage:.1f}%",
                )
            with cols[2]:
                margin_pct = (1 - 1/motor_markup) * 100 if motor_markup > 0 else 0.0
                st.metric("Gross Margin", f"{margin_pct:.1f}%")
            with cols[3]:
                st.metric(
                    "Final Price", f"{currency} {final_price:,.2f}"
                )
        else:
            cols = st.columns(3)
            with cols[0]:
                st.metric("Base Price", f"{currency} {base_price:,.2f}")
            with cols[1]:
                margin_pct = (1 - 1/motor_markup) * 100 if motor_markup > 0 else 0.0
                st.metric("Gross Margin", f"{margin_pct:.1f}%")
            with cols[2]:
                st.metric(
                    "Final Price", f"{currency} {final_price:,.2f}"
                )


def render_main_content():
    st.header("2. Motor Selection")

    # Work with v4 schema — use active fan configuration
    qd = st.session_state.quote_data

    from common import get_active_config

    active_cfg = get_active_config(qd)
    if not active_cfg:
        st.warning(
            "No fan configuration available. Please add one from the sidebar."
        )
        return

    spec_section = active_cfg.setdefault("specification", {})
    pricing_section = active_cfg.setdefault("pricing", {})
    calc_section = active_cfg.setdefault("calculations", {})

    # Get dynamic widget key suffix for widget reset support
    widget_reset_counter = st.session_state.get("widget_reset_counter", 0)
    widget_key_suffix = f"_{widget_reset_counter}"

    # Motor specification in v3
    motor_spec = spec_section.setdefault("motor", {})
    # Motor pricing moved to calculations section
    motor_calc = calc_section.setdefault("motor", {})

    fan_config = st.session_state.get("current_fan_config")

    # --- 1. Prerequisite Check: Ensure a fan is selected first. ---
    if not fan_config:
        st.info(
            "Please select a fan on the 'Fan Configuration' tab to see available motors."
        )
        return

    # --- 2. Fetch available motors based on the selected fan's kW ratings ---
    available_kw = fan_config.get('available_motor_kw', [])
    if not available_kw:
        st.warning(
            "The selected fan configuration has no specified motor kW ratings."
        )
        return

    # Derive poles filter from the fan configuration (support either single int or list)
    raw_poles = (
        fan_config.get('available_motor_poles')
        or fan_config.get('motor_poles')
        or fan_config.get('motor_pole')
        or fan_config.get('preferred_motor_poles')
    )
    poles_filter = None
    if isinstance(raw_poles, list):
        poles_filter = raw_poles[0] if raw_poles else None
    elif isinstance(raw_poles, int):
        poles_filter = raw_poles

    motors_list = get_available_motors(available_kw, poles=poles_filter)

    # --- 3. Display motors in a selectable dataframe (initial setup) ---
    if motors_list is None:
        st.error("Could not retrieve motor data from the API.")
        return

    if not motors_list:
        st.info(
            f"No motors found in the database for the available kW ratings: "
            f"{', '.join(map(str, available_kw))}."
        )
        return

    motors_df = pd.DataFrame(motors_list).sort_values(
        'rated_output', ascending=False
    ).reset_index(drop=True)
    st.session_state.available_motors_df = motors_df

    # Check if user has made a new selection from the table
    motor_df_key = f"motor_selection_df{widget_key_suffix}"
    has_new_selection = bool(
        st.session_state.get(motor_df_key, {})
        .get("selection", {})
        .get("rows")
    )

    # --- Handle motor deselection ---
    def _clear_motor_selection():
        """Clear the current motor selection and reset related pricing data."""
        motor_spec.update({"mount_type": None, "motor_details": {}})
        motor_calc.update({"base_price": 0.0, "final_price": 0.0})
        pricing_section['motor_supplier_discount'] = {
            "supplier_name": None,
            "discount_percentage": 0.0,
            "is_override": False,
            "applied_discount": 0.0,
            "notes": "",
        }
        if motor_df_key in st.session_state:
            del st.session_state[motor_df_key]
        if "last_confirmed_motor_supplier" in st.session_state:
            del st.session_state["last_confirmed_motor_supplier"]
        from utils import update_quote_totals

        update_quote_totals(qd)

    # Check if a motor is already selected in quote_data (for loaded quotes)
    # Only show this if there's NO new selection from the table
    existing_motor = motor_spec.get('motor_details')
    if (
        existing_motor
        and isinstance(existing_motor, dict)
        and not has_new_selection
    ):
        # Get motor pricing information
        motor_base_price = motor_calc.get('base_price', 0)
        motor_final_price = motor_calc.get('final_price', 0)
        current_motor_markup = pricing_section.get('motor_markup', 1.0)
        currency = existing_motor.get('currency', 'ZAR')

        # Display motor summary card
        _render_motor_summary_card(existing_motor, motor_spec, currency)

        # Display pricing card
        discount_data = pricing_section.get('motor_supplier_discount', {})
        supplier_discount = discount_data.get('applied_discount', 0.0)

        _render_pricing_card(
            float(motor_base_price),
            supplier_discount,
            float(current_motor_markup),
            float(motor_final_price),
            currency,
        )

        st.caption(
            "Select a different motor from the table below to change the "
            "selection, or keep the current motor."
        )
        if st.button(
            "Clear Motor Selection",
            key=f"clear_motor_existing{widget_key_suffix}",
            help="Remove the current motor selection from this configuration.",
        ):
            _clear_motor_selection()
            st.rerun()
        st.divider()

    # --- Motor selection table ---
    display_df = motors_df.copy()

    display_df['price_flange'] = display_df.apply(
        lambda row: (
            f"{row['currency']} {row['flange_price']:.2f}"
            if pd.notna(row['flange_price'])
            else "N/A"
        ),
        axis=1,
    )
    display_df['price_foot'] = display_df.apply(
        lambda row: (
            f"{row['currency']} {row['foot_price']:.2f}"
            if pd.notna(row['foot_price'])
            else "N/A"
        ),
        axis=1,
    )

    cols_to_display = {
        'supplier_name': 'Supplier',
        'product_range': 'Range',
        'rated_output': 'kW',
        'poles': 'Poles',
        'speed': 'Speed (RPM)',
        'price_flange': 'Price (Flange)',
        'price_foot': 'Price (Foot)',
        'latest_price_date': 'Price Date',
    }

    display_df_final = display_df[list(cols_to_display.keys())].rename(
        columns=cols_to_display
    )

    st.markdown("Select a motor from the list below:")
    st.dataframe(
        display_df_final,
        key=motor_df_key,
        on_select="rerun",
        selection_mode="single-row",
        hide_index=True,
        use_container_width=True,
    )

    # --- 4. Handle the selection and finalize ---
    selection = st.session_state.get(motor_df_key, {}).get("selection", {})

    if selection.get("rows"):
        selected_index = selection["rows"][0]
        selected_motor = st.session_state.available_motors_df.iloc[
            selected_index
        ]
        currency = selected_motor['currency']

        # Track current supplier for change detection
        new_supplier = selected_motor['supplier_name']
        old_supplier = st.session_state.get(
            'last_confirmed_motor_supplier', None
        )

        if old_supplier != new_supplier:
            st.session_state['last_confirmed_motor_supplier'] = new_supplier

        # Store the full motor details — sanitize NaN/Inf from pandas Series
        motor_spec['motor_details'] = sanitize_for_json(selected_motor.to_dict())
        motor_spec['mount_type'] = "Flange"
        raw_flange_price = selected_motor['flange_price']
        motor_calc['base_price'] = None if (isinstance(raw_flange_price, float) and (math.isnan(raw_flange_price) or math.isinf(raw_flange_price))) else raw_flange_price

        # Motor summary card
        _render_motor_summary_card(
            selected_motor.to_dict(), motor_spec, currency
        )
        st.caption("Foot mount option is currently unavailable.")

        # --- Pricing Adjustments card ---
        @st.cache_data(ttl=300)
        def fetch_supplier_discount(supplier: str) -> float:
            """Fetch motor supplier discount from API."""
            try:
                response = requests.get(
                    f"{API_BASE_URL}/motors/supplier-discount/{supplier}",
                    headers=get_api_headers(),
                )
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        return float(data.get('discount_percentage', 0.0))
            except Exception as e:
                st.error(f"Error fetching supplier discount: {e}")
            return 0.0

        default_discount = fetch_supplier_discount(new_supplier)

        discount_data = pricing_section.setdefault(
            'motor_supplier_discount',
            {
                "supplier_name": None,
                "discount_percentage": 0.0,
                "is_override": False,
                "applied_discount": 0.0,
                "notes": "",
            },
        )

        # If supplier changed, reset discount to default for new supplier
        if discount_data.get('supplier_name') != new_supplier:
            discount_data['supplier_name'] = new_supplier
            discount_data['discount_percentage'] = default_discount
            discount_data['is_override'] = False
            discount_data['applied_discount'] = default_discount
            discount_data['notes'] = "Default supplier discount"

        current_discount = discount_data.get(
            'applied_discount', default_discount
        )

        # CRITICAL: Use supplier-specific AND config-specific widget key
        discount_widget_key = (
            f"widget_motor_supplier_discount_{new_supplier}{widget_key_suffix}"
        )

        # Get default motor markup
        default_motor_markup = pricing_section.get("motor_markup", 1.2)

        with st.container(border=True):
            st.markdown("##### Pricing Adjustments")
            col_discount, col_markup = st.columns(2)

            with col_discount:
                discount_percentage = st.number_input(
                    "Supplier Discount (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(current_discount),
                    step=0.5,
                    format="%.2f",
                    key=discount_widget_key,
                    help=(
                        f"Default discount for {new_supplier}: "
                        f"{default_discount:.2f}%. You can override this value."
                    ),
                )
                is_override = abs(discount_percentage - default_discount) > 0.01
                if is_override:
                    st.caption(
                        f"Override (default: {default_discount:.1f}%)"
                    )

            with col_markup:
                current_motor_markup = pricing_section.get("motor_markup")
                try:
                    initial_markup_val = (
                        float(current_motor_markup)
                        if current_motor_markup is not None
                        else float(default_motor_markup)
                    )
                except (TypeError, ValueError):
                    initial_markup_val = float(default_motor_markup)

                default_margin_pct = (
                    (1 - 1/default_motor_markup) * 100
                    if default_motor_markup > 0 else 0.0
                )
                initial_margin_pct = (
                    (1 - 1/initial_markup_val) * 100
                    if initial_markup_val > 0 else 0.0
                )
                motor_margin_pct = st.number_input(
                    "Motor Gross Margin %",
                    min_value=0.0,
                    max_value=99.9,
                    value=initial_margin_pct,
                    step=0.5,
                    format="%.1f",
                    key=f"widget_motor_markup_override{widget_key_suffix}",
                    help=(
                        f"Gross margin % for motor pricing "
                        f"(default: {default_margin_pct:.1f}% from database)."
                    ),
                )
                st.caption(f"Gross Margin: {motor_margin_pct:.1f}%")
                motor_markup = (
                    1 / (1 - motor_margin_pct / 100)
                    if motor_margin_pct < 100 else 1.0
                )

        # Update discount data
        discount_changed = (
            discount_data.get('applied_discount') != discount_percentage
        )

        discount_data['discount_percentage'] = default_discount
        discount_data['is_override'] = is_override
        discount_data['applied_discount'] = discount_percentage
        if is_override:
            discount_data['notes'] = (
                f"User override: {discount_percentage}% "
                f"(default: {default_discount}%)"
            )
        else:
            discount_data['notes'] = "Default supplier discount"

        # Update markup
        markup_changed = pricing_section.get('motor_markup') != motor_markup
        pricing_section['motor_markup'] = motor_markup

        # Calculate and display pricing summary
        if pd.notna(motor_calc.get('base_price')):
            base_price = float(motor_calc['base_price'])

            # Apply supplier discount BEFORE markup
            discount_multiplier = 1.0 - (discount_percentage / 100.0)
            discounted_price = base_price * discount_multiplier

            # Apply markup to discounted price
            final_price = discounted_price * motor_markup
            motor_calc['final_price'] = final_price

            # Update totals immediately when markup or discount changes
            if markup_changed or discount_changed:
                from utils import update_quote_totals

                st.session_state.quote_data = qd
                update_quote_totals(qd)
                st.rerun()

            _render_pricing_card(
                base_price,
                discount_percentage,
                motor_markup,
                final_price,
                currency,
            )
        else:
            st.metric("Final Motor Price", "N/A")

        # Clear button and debug expander
        if st.button(
            "Clear Motor Selection",
            key=f"clear_motor_new{widget_key_suffix}",
            help="Remove the current motor selection from this configuration.",
        ):
            _clear_motor_selection()
            st.rerun()

        with st.expander("Show all selected motor data"):
            st.json(motor_spec['motor_details'])
