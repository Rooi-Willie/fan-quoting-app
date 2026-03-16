import streamlit as st
import pandas as pd
import os
import requests
from config import CURRENCY_SYMBOL
from utils import ensure_server_summary_up_to_date, build_summary_dataframe, get_ordered_component_names, build_ordered_component_rows, get_api_headers
from common import _new_quote_data
from export_utils import generate_docx, generate_filename

# API_BASE_URL should be configured, e.g., via environment variable

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8080")


def _render_config_section(cfg, cfg_index):
    """Render the review section for a single fan configuration."""
    spec_section = cfg.get("specification", {})
    pricing_section = cfg.get("pricing", {})
    calc_section = cfg.get("calculations", {})
    quantity = cfg.get("quantity", 1)
    label = cfg.get("label", f"Fan Config {cfg_index + 1}")

    fan_section = spec_section.get("fan", {})
    fan_config = fan_section.get("fan_configuration", {})
    motor_spec = spec_section.get("motor", {})
    motor_calc = calc_section.get("motor", {})

    # Fan spec summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Fan ID:** {fan_config.get('uid') or 'N/A'}")
        st.markdown(f"**Fan Size:** {fan_config.get('fan_size_mm') or 'N/A'} mm")
    with col2:
        st.markdown(f"**Blade Sets:** {fan_section.get('blade_sets') or 'N/A'}")
        st.markdown(f"**Quantity:** {quantity}")
    with col3:
        comp_markup = pricing_section.get("component_markup", 1.0)
        comp_markup_pct = (float(comp_markup) - 1) * 100
        st.markdown(f"**Component Markup:** {comp_markup_pct:.1f}%")

    # Motor Information
    if motor_spec.get('motor_details') and isinstance(motor_spec['motor_details'], dict):
        motor = motor_spec['motor_details']
        st.markdown("---")
        st.markdown("**Motor**")
        mcol1, mcol2, mcol3 = st.columns(3)
        with mcol1:
            st.markdown(f"{motor.get('supplier_name', 'N/A')} — {motor.get('product_range', 'N/A')}")
            st.markdown(f"Mount: {motor_spec.get('mount_type', 'N/A')}")
        with mcol2:
            st.markdown(f"{motor.get('rated_output', 0)} {motor.get('rated_output_unit', 'kW')}, {motor.get('poles', 'N/A')} poles")
        with mcol3:
            base_price = motor_calc.get('base_price') or motor.get('price_total', 0)
            st.markdown(f"Base: {CURRENCY_SYMBOL} {float(base_price or 0):,.2f}")

            discount_data = pricing_section.get('motor_supplier_discount', {})
            supplier_discount = discount_data.get('applied_discount', 0.0)
            if supplier_discount > 0:
                st.markdown(f"Discount: {supplier_discount:.2f}%")

            motor_markup = float(pricing_section.get('motor_markup') or 1.0)
            motor_markup_pct = (motor_markup - 1) * 100
            st.markdown(f"Markup: {motor_markup_pct:.1f}%")
            final_price = motor_calc.get('final_price')
            if final_price is not None:
                st.markdown(f"**Final: {CURRENCY_SYMBOL} {float(final_price):,.2f}**")

    # Component summary table
    components_dict = calc_section.get("components", {})
    if components_dict:
        ordered_names = get_ordered_component_names(cfg)
        rows = build_ordered_component_rows(components_dict, ordered_names)
        if rows:
            styler = build_summary_dataframe(rows, CURRENCY_SYMBOL)
            st.write(styler)

    # Per-config cost breakdown
    component_totals = calc_section.get("component_totals", {})
    totals_section = calc_section.get("totals", {})
    unit_total = calc_section.get("unit_total", 0.0)
    line_total = calc_section.get("line_total", 0.0)

    # Build ordered components list for breakdown
    server_components = []
    if components_dict:
        ordered_names = get_ordered_component_names(cfg)
        for comp_name in ordered_names:
            if comp_name in components_dict:
                server_components.append(components_dict[comp_name])

    breakdown_rows = []

    # Components
    if server_components:
        for i, c in enumerate(server_components):
            breakdown_rows.append({
                "Item Type": "Component",
                "Item": c.get("name", f"Component {i+1}"),
                "Cost": c.get("total_cost_after_markup", 0)
            })
        components_total = totals_section.get("components", 0) or component_totals.get("final_price", 0)
        breakdown_rows.append({
            "Item Type": "Subtotal",
            "Item": "Components Subtotal",
            "Cost": components_total
        })

    # Motor
    if motor_spec.get('motor_details'):
        motor_price = float(motor_calc.get('final_price', 0) or 0)
        motor = motor_spec['motor_details']
        motor_name = f"{motor.get('supplier_name', '')} {motor.get('product_range', '')} - {motor.get('rated_output', 0)} {motor.get('rated_output_unit', 'kW')}"
        breakdown_rows.append({
            "Item Type": "Motor",
            "Item": motor_name,
            "Cost": motor_price
        })

    # Buyouts
    buyout_items = spec_section.get("buyouts", [])
    buyout_total = 0.0
    if isinstance(buyout_items, list) and buyout_items:
        for bi in buyout_items:
            buyout_total += float(bi.get("subtotal") or (bi.get("unit_cost", 0) * bi.get("qty", 0)))
        breakdown_rows.append({
            "Item Type": "Subtotal",
            "Item": "Buy-out Items Subtotal",
            "Cost": buyout_total
        })

    # Unit total and line total
    if unit_total:
        breakdown_rows.append({
            "Item Type": "Subtotal",
            "Item": "Unit Total (1 fan)",
            "Cost": unit_total
        })
    if quantity > 1 and line_total:
        breakdown_rows.append({
            "Item Type": "Total",
            "Item": f"Line Total ({quantity} x fans)",
            "Cost": line_total
        })

    if breakdown_rows:
        df = pd.DataFrame(breakdown_rows)
        df["Formatted Cost"] = df["Cost"].apply(lambda x: f"{CURRENCY_SYMBOL} {float(x):,.2f}")
        display_df = df[["Item", "Formatted Cost"]]

        def highlight_rows(row):
            style = ''
            if df.loc[row.name, "Item Type"] == "Subtotal":
                style = 'font-weight: bold; border-top: 1px solid; color: #1E88E5'
            elif df.loc[row.name, "Item Type"] == "Total":
                style = 'font-weight: bold; font-size: 1.1em; border-top: 2px solid; color: #2E7D32'
            return [style, style]

        styled_df = display_df.style.apply(highlight_rows, axis=1)
        st.table(styled_df)


def render_main_content():
    st.header("5. Review & Finalize Quote")

    # Ensure quote_data exists
    if "quote_data" not in st.session_state or not isinstance(st.session_state.quote_data, dict):
        st.session_state.quote_data = _new_quote_data()

    qd = st.session_state.quote_data

    # Auto-refresh authoritative server totals
    ensure_server_summary_up_to_date(qd)

    # Ensure local totals are up to date
    from utils import update_quote_totals
    update_quote_totals(qd)

    # --- Project Information (shared across all configs) ---
    quote_section = qd.get("quote", {})
    st.subheader("Project Information")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Project Name:** {quote_section.get('project') or 'N/A'}")
        st.markdown(f"**Client Name:** {quote_section.get('client') or 'N/A'}")
        st.markdown(f"**Quote Reference:** {quote_section.get('reference') or 'N/A'}")
    with col2:
        st.markdown(f"**Location:** {quote_section.get('location') or 'N/A'}")
    st.divider()

    # --- Per-config sections ---
    fan_configs = qd.get("fan_configurations", [])
    is_multi = len(fan_configs) > 1

    for cfg_idx, cfg in enumerate(fan_configs):
        label = cfg.get("label", f"Fan Config {cfg_idx + 1}")
        quantity = cfg.get("quantity", 1)
        qty_badge = f" (x{quantity})" if quantity > 1 else ""

        if is_multi:
            st.subheader(f"{label}{qty_badge}")
        else:
            st.subheader(f"Fan Configuration{qty_badge}")

        _render_config_section(cfg, cfg_idx)

        if cfg_idx < len(fan_configs) - 1:
            st.divider()

    # --- Grand Totals ---
    st.divider()
    st.subheader("Grand Total")

    grand_totals = qd.get("grand_totals", {})
    gt_components = grand_totals.get("components", 0)
    gt_motors = grand_totals.get("motors", 0)
    gt_buyouts = grand_totals.get("buyouts", 0)
    gt_grand_total = grand_totals.get("grand_total", 0)

    grand_rows = []
    if gt_components:
        grand_rows.append({"Item": "Components (all configs)", "Cost": gt_components})
    if gt_motors:
        grand_rows.append({"Item": "Motors (all configs)", "Cost": gt_motors})
    if gt_buyouts:
        grand_rows.append({"Item": "Buy-out Items (all configs)", "Cost": gt_buyouts})
    grand_rows.append({"Item": "GRAND TOTAL", "Cost": gt_grand_total})

    gt_df = pd.DataFrame(grand_rows)
    gt_df["Formatted Cost"] = gt_df["Cost"].apply(lambda x: f"{CURRENCY_SYMBOL} {float(x):,.2f}")
    gt_display = gt_df[["Item", "Formatted Cost"]]

    def highlight_grand(row):
        if gt_df.loc[row.name, "Item"] == "GRAND TOTAL":
            style = 'font-weight: bold; font-size: 1.2em; border-top: 2px solid; color: #2E7D32'
        else:
            style = 'font-weight: bold; color: #1E88E5'
        return [style, style]

    gt_styled = gt_display.style.apply(highlight_grand, axis=1)
    st.table(gt_styled)

    st.divider()

    # --- Export and Save buttons ---
    st.subheader("Export & Save Quote")

    export_col1, export_col2, export_col3 = st.columns(3)

    with export_col1:
        try:
            docx_bytes = generate_docx(qd)
            filename = generate_filename(qd, extension="docx")

            st.download_button(
                label="Download Word Document",
                data=docx_bytes,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        except FileNotFoundError as e:
            st.error(f"Template not found: {str(e)}")
            st.info("Please ensure quote_template.docx is in the ui/templates/ directory.")
        except Exception as e:
            st.error(f"Error generating Word document: {str(e)}")

    with export_col2:
        if st.button("Download PDF (Coming Soon)", use_container_width=True, disabled=True):
            st.info("PDF export functionality will be implemented in a future update.")

    with export_col3:
        if st.button("Save Quote", use_container_width=True, type="primary"):
            if save_quote():
                st.success("Quote saved successfully!")
                st.session_state["show_view_quotes_button"] = True
                st.rerun()

    # Show "View Saved Quotes" button after successful save
    if st.session_state.get("show_view_quotes_button", False):
        if st.button("View Saved Quotes", use_container_width=True):
            st.session_state["show_view_quotes_button"] = False
            st.switch_page("pages/3_View_Existing_Quotes.py")


def save_quote():
    """Save the current quote to the database using v4 schema."""
    try:
        import datetime as _dt

        user_id = st.session_state.get("user_id", 1)
        qd = st.session_state.quote_data

        # Use South Africa timezone (UTC+2 / SAST)
        sast_tz = _dt.timezone(_dt.timedelta(hours=2))
        now_sast = _dt.datetime.now(sast_tz)

        qd["meta"]["updated_at"] = now_sast.isoformat()

        if st.session_state.get("logged_in"):
            qd["meta"]["last_modified_by_user"] = {
                "id": st.session_state.get("user_id"),
                "username": st.session_state.get("username"),
                "full_name": st.session_state.get("full_name"),
                "email": st.session_state.get("email"),
                "phone": st.session_state.get("phone", ""),
                "department": st.session_state.get("department", ""),
                "job_title": st.session_state.get("job_title", ""),
                "role": st.session_state.get("user_role", "user"),
            }

        quote_section = qd.get("quote", {})

        editing_quote_id = st.session_state.get("editing_quote_id")

        if editing_quote_id:
            # UPDATE existing quote
            payload = {
                "quote_data": qd,
                "user_id": user_id,
            }
            response = requests.put(
                f"{API_BASE_URL}/saved-quotes/{editing_quote_id}",
                json=payload,
                headers=get_api_headers()
            )
            response.raise_for_status()
            saved_quote = response.json()
            st.session_state["last_saved_quote_id"] = saved_quote["id"]

        else:
            # CREATE new quote
            quote_ref = quote_section.get("reference") or qd.get("quote_ref", "")

            # Validate quote reference uniqueness
            try:
                validation_response = requests.get(
                    f"{API_BASE_URL}/saved-quotes/validate-reference/{quote_ref}",
                    headers=get_api_headers()
                )
                if validation_response.ok:
                    validation_data = validation_response.json()

                    if not validation_data.get("is_available", True):
                        original_ref = quote_ref
                        suggested_ref = validation_data.get("suggestion", quote_ref + "-A")

                        suffix_counter = 0
                        suffix_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                        while suffix_counter < len(suffix_chars):
                            test_ref = f"{original_ref}-{suffix_chars[suffix_counter]}"
                            test_validation = requests.get(
                                f"{API_BASE_URL}/saved-quotes/validate-reference/{test_ref}",
                                headers=get_api_headers()
                            )
                            if test_validation.ok and test_validation.json().get("is_available", False):
                                quote_ref = test_ref
                                quote_section["reference"] = quote_ref
                                st.warning(f"Quote reference '{original_ref}' already exists. Auto-adjusted to '{quote_ref}'")
                                break
                            suffix_counter += 1

                        if suffix_counter >= len(suffix_chars):
                            quote_ref = suggested_ref
                            quote_section["reference"] = quote_ref
                            st.warning(f"Quote reference '{original_ref}' already exists. Auto-adjusted to '{quote_ref}'")
            except Exception as validation_error:
                st.warning(f"Could not validate quote reference: {str(validation_error)}")

            payload = {
                "quote_ref": quote_ref,
                "client_name": quote_section.get("client") or qd.get("client_name", ""),
                "project_name": quote_section.get("project") or qd.get("project_name", ""),
                "project_location": quote_section.get("location") or qd.get("project_location", ""),
                "user_id": user_id,
                "quote_data": qd,
            }

            response = requests.post(f"{API_BASE_URL}/saved-quotes/v3", json=payload, headers=get_api_headers())
            response.raise_for_status()
            saved_quote = response.json()
            st.session_state["last_saved_quote_id"] = saved_quote["id"]

        return True
    except Exception as e:
        st.error(f"Error saving quote: {str(e)}")
        return False
