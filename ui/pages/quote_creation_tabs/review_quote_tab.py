import streamlit as st
import pandas as pd
import os
import requests
from config import CURRENCY_SYMBOL
from utils import ensure_server_summary_up_to_date, build_summary_dataframe, get_ordered_component_names, build_ordered_component_rows
from common import _new_quote_data
from export_utils import generate_docx, generate_filename

# API_BASE_URL should be configured, e.g., via environment variable
# Fallback is provided for local development.
import streamlit as st
import os
import requests
import pandas as pd
from typing import Dict, List
from common import update_quote_data_top_level_key
from utils import get_api_headers

# API_BASE_URL should be configured, e.g., via environment variable

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

def render_main_content():
    st.header("5. Review & Finalize Quote")

    # Ensure quote_data exists
    if "quote_data" not in st.session_state or not isinstance(st.session_state.quote_data, dict):
        st.session_state.quote_data = _new_quote_data()
    
    qd = st.session_state.quote_data
    
    # Extract sections
    quote_section = qd.get("quote", {})
    spec_section = qd.get("specification", {})
    pricing_section = qd.get("pricing", {})
    calc_section = qd.get("calculations", {})
    
    # Extract sub-sections (updated for new v3 structure)
    fan_section = spec_section.get("fan", {})
    fan_config = fan_section.get("fan_configuration", {})
    motor_spec = spec_section.get("motor", {})
    motor_calc = calc_section.get("motor", {})  # Motor pricing moved to calculations
    components = spec_section.get("components", [])

    # Project Information
    st.subheader("Project Information")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Project Name:** {quote_section.get('project') or 'N/A'}")
        st.markdown(f"**Client Name:** {quote_section.get('client') or 'N/A'}")
        st.markdown(f"**Quote Reference:** {quote_section.get('reference') or 'N/A'}")
    with col2:
        st.markdown(f"**Location:** {quote_section.get('location') or 'N/A'}")
        st.markdown(f"**Fan ID:** {fan_config.get('uid') or 'N/A'}")
    st.divider()
   
    # Motor Information
    st.subheader("Motor Information")
    if motor_spec.get('motor_details') and isinstance(motor_spec['motor_details'], dict):
        motor = motor_spec['motor_details']
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Supplier:** {motor.get('supplier_name', 'N/A')}")
            st.markdown(f"**Product Range:** {motor.get('product_range', 'N/A')}")
            st.markdown(f"**Mount Type:** {motor_spec.get('mount_type', 'N/A')}")
        with col2:
            st.markdown(f"**Power:** {motor.get('rated_output', 0)} {motor.get('rated_output_unit', 'kW')}")
            st.markdown(f"**Poles:** {motor.get('poles', 'N/A')}")
            st.markdown(f"**Speed:** {motor.get('speed', 'N/A')} {motor.get('speed_unit', 'RPM')}")
        with col3:
            base_price = motor_calc.get('base_price') or motor.get('price_total', 0)
            st.markdown(f"**Base Price:** {CURRENCY_SYMBOL} {float(base_price or 0):,.2f}")
            
            # Show supplier discount
            discount_data = pricing_section.get('motor_supplier_discount', {})
            supplier_discount = discount_data.get('applied_discount', 0.0)
            if supplier_discount > 0:
                discount_multiplier = 1.0 - (supplier_discount / 100.0)
                discounted_price = float(base_price or 0) * discount_multiplier
                st.markdown(f"**Supplier Discount:** {supplier_discount:.2f}% ({discount_data.get('notes', '')})")
                st.markdown(f"**After Discount:** {CURRENCY_SYMBOL} {discounted_price:,.2f}")
            
            motor_markup = float(pricing_section.get('motor_markup') or 1.0)
            motor_markup_pct = (motor_markup - 1) * 100
            st.markdown(f"**Markup Applied:** {motor_markup:.2f} ({motor_markup_pct:.1f}%)")
            final_price = motor_calc.get('final_price')
            if final_price is not None:
                st.markdown(f"**Final Price:** {CURRENCY_SYMBOL} {float(final_price):,.2f}")
    else:
        st.info("No motor has been selected. Please go to the 'Motor Selection' tab to choose a motor.")

    st.divider()

    # Auto-refresh authoritative server totals when inputs change
    ensure_server_summary_up_to_date(qd)
    
    # ENHANCED: Ensure local totals are immediately updated to prevent display lag
    from utils import update_quote_totals
    update_quote_totals(qd)

    # Fan Component Cost & Mass Summary (DataFrame only)
    st.subheader("Fan Component Cost & Mass Summary")

    # Get components from v3 calculations structure
    server_summary = st.session_state.get("server_summary", {})
    server_calculations = server_summary.get("calculations", {})
    server_components_dict = server_calculations.get("components", {})
    
    # Determine which components dict to use
    components_dict = server_components_dict if server_components_dict else calc_section.get("components", {})
    
    if not components_dict:
        st.info("No fan components configured yet. Please go to the 'Fan Configuration' tab.")
        return
    
    # Use ordered component names from DB order_by column
    ordered_names = get_ordered_component_names(qd)
    rows = build_ordered_component_rows(components_dict, ordered_names)
    
    # Also build ordered server_components list for use in breakdown section below
    server_components = []
    for comp_name in ordered_names:
        if comp_name in components_dict:
            server_components.append(components_dict[comp_name])

    if not rows:
        st.info("No fan components configured yet. Please go to the 'Fan Configuration' tab.")
        return

    styler = build_summary_dataframe(rows, CURRENCY_SYMBOL)
    st.write(styler)

    # Final Quote Cost Breakdown Section
    st.divider()
    st.subheader("Final Quote Cost Breakdown")

    # Get totals from v3 calculations structure
    component_totals = calc_section.get("component_totals", {})
    totals_section = calc_section.get("totals", {})
    
    # Initialize breakdown data
    breakdown_rows = []
    
    # Add Component section with all components
    if server_components:
        # Add each individual component
        for i, c in enumerate(server_components):
            breakdown_rows.append({
                "Item Type": "Component",
                "Item": c.get("name", f"Component {i+1}"),
                "Cost": c.get("total_cost_after_markup", 0)
            })
        
        # Add Component Subtotal using v3 totals structure
        components_total = totals_section.get("components", 0) or component_totals.get("final_price", 0)
        breakdown_rows.append({
            "Item Type": "Subtotal",
            "Item": "Components Subtotal",
            "Cost": components_total
        })
    else:
        # Fallback: try to get components total even without individual components
        components_total = totals_section.get("components", 0) or component_totals.get("final_price", 0)
        if components_total > 0:
            breakdown_rows.append({
                "Item Type": "Subtotal",
                "Item": "Components Subtotal",
                "Cost": components_total
            })
    
    # Add Motor section if a motor is selected
    if motor_spec.get('motor_details'):
        motor = motor_spec['motor_details']
        motor_price = float(motor_calc.get('final_price', 0) or 0)
        
        # Add motor entry
        motor_name = f"{motor.get('supplier_name', '')} {motor.get('product_range', '')} - {motor.get('rated_output', 0)} {motor.get('rated_output_unit', 'kW')}"
        breakdown_rows.append({
            "Item Type": "Motor",
            "Item": motor_name,
            "Cost": motor_price
        })
        
        # Add Motor Subtotal
        breakdown_rows.append({
            "Item Type": "Subtotal",
            "Item": "Motor Subtotal",
            "Cost": motor_price
        })
    
    # Add Buyout Items section
    # Buy-out items subtotal from v3 specification section (updated location)
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
    else:
        breakdown_rows.append({
            "Item Type": "Subtotal",
            "Item": "Buy-out Items Subtotal",
            "Cost": 0
        })
    
    # Calculate and add Final Total using v3 totals structure
    components_total = totals_section.get("components", 0) or component_totals.get("final_price", 0)
    motor_total = totals_section.get("motor", 0) or float(motor_calc.get('final_price', 0) or 0)
    final_total = totals_section.get("grand_total", 0) or (components_total + motor_total + buyout_total)
    
    # Add Final Total Row
    breakdown_rows.append({
        "Item Type": "Total",
        "Item": "FINAL QUOTE TOTAL",
        "Cost": final_total
    })
    
    # Create DataFrame
    df = pd.DataFrame(breakdown_rows)
    
    # Format the cost column
    df["Formatted Cost"] = df["Cost"].apply(lambda x: f"{CURRENCY_SYMBOL} {float(x):,.2f}")
    
    # Keep only necessary columns for display
    display_df = df[["Item", "Formatted Cost"]]
    
    # Apply styling to the table
    def highlight_rows(row):
        style = ''
        if df.loc[row.name, "Item Type"] == "Subtotal":
            style = 'font-weight: bold; border-top: 1px solid; color: #1E88E5'
        elif df.loc[row.name, "Item Type"] == "Total":
            style = 'font-weight: bold; font-size: 1.1em; border-top: 2px solid; color: #2E7D32'
        return [style, style]  # Return styling for exactly 2 columns
    
    # Apply styling
    styled_df = display_df.style.apply(highlight_rows, axis=1)
    
    # Show the table
    st.table(styled_df)

    st.divider()
    
    # Export and Save buttons
    st.subheader("Export & Save Quote")
    
    export_col1, export_col2, export_col3 = st.columns(3)
    
    with export_col1:
        # Download DOCX button
        try:
            docx_bytes = generate_docx(qd)
            filename = generate_filename(qd, extension="docx")
            
            st.download_button(
                label="📄 Download Word Document",
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
        # PDF placeholder button
        if st.button("📄 Download PDF (Coming Soon)", use_container_width=True, disabled=True):
            st.info("PDF export functionality will be implemented in a future update.")
    
    with export_col3:
        # Save Quote button
        if st.button("💾 Save Quote", use_container_width=True, type="primary"):
            if save_quote():
                st.success("Quote saved successfully!")
                st.session_state["show_view_quotes_button"] = True
                st.rerun()
    
    # Show "View Saved Quotes" button after successful save (persists across reruns)
    if st.session_state.get("show_view_quotes_button", False):
        if st.button("📋 View Saved Quotes", use_container_width=True):
            # Clear the flag and navigate
            st.session_state["show_view_quotes_button"] = False
            st.switch_page("pages/3_View_Existing_Quotes.py")

def save_quote():
    """Save the current quote to the database using v3 schema"""
    try:
        # Get current user ID (use 1 for development until auth is implemented)
        user_id = 1
        qd = st.session_state.quote_data
        
        # Get data from v3 sections - handle v3 schema structure correctly
        quote_section = qd.get("quote", {})

        # Prepare payload using v3 structure
        payload = {
            "quote_ref": quote_section.get("reference") or qd.get("quote_ref", ""),
            "client_name": quote_section.get("client") or qd.get("client_name", ""),
            "project_name": quote_section.get("project") or qd.get("project_name", ""),  # v3: project is a string
            "project_location": quote_section.get("location") or qd.get("project_location", ""),  # v3: location is a string
            "user_id": user_id,
            "quote_data": qd,
        }
        
        # Call v3 API endpoint
        response = requests.post(f"{API_BASE_URL}/saved-quotes/v3", json=payload, headers=get_api_headers())
        response.raise_for_status()
        
        # Store the quote ID in session state for reference
        saved_quote = response.json()
        st.session_state["last_saved_quote_id"] = saved_quote["id"]
        
        return True
    except Exception as e:
        st.error(f"Error saving quote: {str(e)}")
        return False