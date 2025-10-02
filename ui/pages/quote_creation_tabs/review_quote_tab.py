import streamlit as st
import pandas as pd
import os
import requests
from config import CURRENCY_SYMBOL
from utils import ensure_server_summary_up_to_date, build_summary_dataframe
from common import _new_v3_quote_data
from export_utils import generate_docx, generate_filename

# API_BASE_URL should be configured, e.g., via environment variable
# Fallback is provided for local development.
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

def render_main_content():
    st.header("5. Review & Finalize Quote")

    # Ensure v3 schema
    if "quote_data" not in st.session_state or not isinstance(st.session_state.quote_data, dict):
        st.session_state.quote_data = _new_v3_quote_data()
    
    qd = st.session_state.quote_data
    
    # Extract v3 sections
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
    
    # Convert components dict to list for compatibility, with fallback to quote data
    server_components = []
    if server_components_dict:
        server_components = list(server_components_dict.values())
    elif calc_section.get("components"):
        # Fallback to quote data calculations section
        calc_components = calc_section.get("components", {})
        server_components = list(calc_components.values())
    
    rows = []
    if server_components:
        for c in server_components:
            rows.append({
                "Component": c.get("name"),
                "Length (mm)": c.get("total_length_mm"),
                "Real Mass (kg)": c.get("real_mass_kg"),
                "Material Cost": c.get("material_cost"),
                "Labour Cost": c.get("labour_cost"),
                "Cost Before Markup": c.get("total_cost_before_markup"),
                "Cost After Markup": c.get("total_cost_after_markup"),
            })
    else:
        # Last fallback: try to extract from any available components data
        all_components = calc_section.get("components", {})
        for name, calc in all_components.items():
            rows.append({
                "Component": name,
                "Length (mm)": calc.get("total_length_mm"),
                "Real Mass (kg)": calc.get("real_mass_kg"),
                "Material Cost": calc.get("material_cost"),
                "Labour Cost": calc.get("labour_cost"),
                "Cost Before Markup": calc.get("total_cost_before_markup"),
                "Cost After Markup": calc.get("total_cost_after_markup"),
            })

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
                # Add option to view the quote or continue editing
                if st.button("View Saved Quotes"):
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
        response = requests.post(f"{API_BASE_URL}/saved-quotes/v3", json=payload)
        response.raise_for_status()
        
        # Store the quote ID in session state for reference
        saved_quote = response.json()
        st.session_state["last_saved_quote_id"] = saved_quote["id"]
        
        return True
    except Exception as e:
        st.error(f"Error saving quote: {str(e)}")
        return False