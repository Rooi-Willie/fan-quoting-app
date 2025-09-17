import streamlit as st
import requests
import datetime
import json
import os
from config import APP_TITLE
from pages.common import _new_v3_quote_data

# API_BASE_URL should be configured, e.g., via environment variable
# Fallback is provided for local development.
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

# Page configuration
st.set_page_config(page_title=f"Quote Details - {APP_TITLE}", layout="wide")

if not st.session_state.get("logged_in"):
    st.warning("Please log in first through the main Login page.")
    if st.button("Go to Login"):
        st.switch_page("login_page.py")
    st.stop()

# Check if we have a quote ID to view
if "viewing_quote_id" not in st.session_state:
    st.error("No quote selected for viewing.")
    if st.button("Go to Quotes List"):
        st.switch_page("pages/3_View_Existing_Quotes.py")
    st.stop()

quote_id = st.session_state.viewing_quote_id

# Function to handle v2/v3 quote data compatibility
def ensure_v3_compatibility(quote_data):
    """Convert v2 quote data to v3 structure for display, or return v3 as-is."""
    if not isinstance(quote_data, dict):
        return _new_v3_quote_data()
    
    # Check if it's already v3
    if quote_data.get("meta", {}).get("version") == 3:
        return quote_data
    
    # If it's v2 or unversioned, create v3 structure with available data
    # This is a simplified conversion for display purposes only
    v3_data = _new_v3_quote_data()
    
    # Map v2 fields to v3 structure
    if "fan" in quote_data:
        v3_data["specification"]["fan"] = quote_data["fan"]
    if "motor" in quote_data and "selection" in quote_data["motor"]:
        v3_data["specification"]["motor"] = quote_data["motor"]["selection"]
        if "final_price" in quote_data["motor"]:
            v3_data["pricing"]["motor"]["final_price"] = quote_data["motor"]["final_price"]
    if "components" in quote_data and "selected" in quote_data["components"]:
        v3_data["specification"]["components"] = quote_data["components"]["selected"]
    if "buy_out_items" in quote_data:
        v3_data["specification"]["buyouts"] = quote_data["buy_out_items"]
    if "calculation" in quote_data:
        v3_data["calculations"] = quote_data["calculation"]
    
    return v3_data

# Function to load quote details
def load_quote_details(quote_id):
    try:
        response = requests.get(f"{API_BASE_URL}/saved-quotes/{quote_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error loading quote details: {str(e)}")
        return None

# Load quote
quote = load_quote_details(quote_id)
if not quote:
    st.error("Failed to load quote details.")
    if st.button("Go Back"):
        st.switch_page("pages/3_View_Existing_Quotes.py")
    st.stop()

# Display quote details
st.title(f"Quote Details: {quote['quote_ref']} (Rev {quote['revision_number']})")

# Status indicator and buttons
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    status_color = {
        "draft": "🟠",
        "sent": "🔵",
        "approved": "🟢",
        "rejected": "🔴"
    }
    st.subheader(f"{status_color.get(quote['status'].lower(), '⚪')} {quote['status'].capitalize()}")

with col3:
    # Create button column
    if st.button("Back to List", use_container_width=True):
        st.switch_page("pages/3_View_Existing_Quotes.py")

# Project information section
st.header("Project Information")
project_cols = st.columns(3)
with project_cols[0]:
    st.metric("Client", quote["client_name"] or "N/A")
with project_cols[1]:
    st.metric("Project", quote["project_name"] or "N/A")
with project_cols[2]:
    st.metric("Location", quote["project_location"] or "N/A")

# Quote details from the saved JSON
quote_data = ensure_v3_compatibility(quote.get("quote_data") or {})

# Extract v3 schema data paths
fan_node = quote_data.get("specification", {}).get("fan", {})
calc_node = quote_data.get("calculations", {})
components_node = quote_data.get("specification", {}).get("components", {})
motor_node = quote_data.get("specification", {}).get("motor", {})

# Fan configuration section
st.header("Fan Configuration")
fan_cols = st.columns(4)
with fan_cols[0]:
    st.metric("Fan ID", fan_node.get("uid") or "N/A")
with fan_cols[1]:
    st.metric("Fan Config ID", fan_node.get("config_id") or "N/A")
with fan_cols[2]:
    st.metric("Blade Sets", str(fan_node.get("blade_sets") or "N/A"))
with fan_cols[3]:
    st.metric("Markup", f"{float(calc_node.get('markup_override', 1.4)):.2f}x")

if motor_node.get("selection"):
    motor = motor_node["selection"]
    st.header("Motor Information")
    motor_cols = st.columns(4)
    with motor_cols[0]:
        st.metric("Supplier", motor.get("supplier_name", "N/A"))
    with motor_cols[1]:
        st.metric("Rated Output", f"{motor.get('rated_output', 'N/A')} {motor.get('rated_output_unit', '')}")
    with motor_cols[2]:
        st.metric("Speed", f"{motor.get('speed', 'N/A')} {motor.get('speed_unit', '')}")
    with motor_cols[3]:
        motor_final_price = quote_data.get("pricing", {}).get("motor", {}).get("final_price", 0)
        st.metric("Final Price", f"R {float(motor_final_price):,.2f}")

if components_node.get("selected"):
    st.header("Components")
    component_data = []
    for comp_name in components_node.get("selected", []):
        node = components_node.get("by_name", {}).get(comp_name, {})
        overrides = node.get("overrides", {})
        component_data.append({
            "Component": comp_name,
            "Thickness (mm)": overrides.get("material_thickness_mm", "Default"),
            "Waste %": overrides.get("fabrication_waste_pct", "Default")
        })
    st.table(component_data)

buyout_items = quote_data.get("specification", {}).get("buyouts", [])
if buyout_items:
    st.header("Buy-out Items")
    buyout_data = []
    for item in buyout_items:
        subtotal = item.get("subtotal")
        if subtotal is None:
            subtotal = float(item.get("unit_cost", 0)) * float(item.get("qty", 0))
        buyout_data.append({
            "Description": item.get("description", ""),
            "Qty": item.get("qty") or item.get("quantity", 0),
            "Unit Cost": f"R {float(item.get('unit_cost', item.get('cost', 0))):,.2f}",
            "Subtotal": f"R {float(subtotal):,.2f}"
        })
    st.table(buyout_data)

# Pricing summary
st.header("Pricing Summary")
price_cols = st.columns(4)

with price_cols[0]:
    total_mass = 0.0
    server_summary = calc_node.get("server_summary", {})
    if server_summary:
        total_mass = server_summary.get("total_real_mass_kg") or server_summary.get("total_mass_kg") or 0.0
    st.metric("Total Mass", f"{float(total_mass):.2f} kg")

with price_cols[1]:
    material_cost = 0
    labour_cost = 0
    
    # Extract from server summary if available
    if server_summary:
        material_cost = server_summary.get("total_material_cost", 0)
        labour_cost = server_summary.get("total_labour_cost", 0)
    
    st.metric("Material Cost", f"R {material_cost:,.2f}")

with price_cols[2]:
    st.metric("Labour Cost", f"R {labour_cost:,.2f}")

with price_cols[3]:
    # Final price attempt: prefer quote.total_price, fallback to server summary final_price, else sum components + motor + buyouts
    final_price = quote.get('total_price')
    if final_price in (None, 0):
        final_price = server_summary.get("final_price") if server_summary else 0
    if not final_price:
        comp_total = server_summary.get("final_price", 0) if server_summary else 0
        motor_total = quote_data.get("pricing", {}).get("motor", {}).get("final_price", 0)
        buyout_total = sum([float(it.get("subtotal") or 0) for it in buyout_items])
        final_price = comp_total + motor_total + buyout_total
    st.metric("Final Price", f"R {float(final_price):,.2f}", delta="Including Markup")

# Revision history
st.header("Revision History")

try:
    response = requests.get(f"{API_BASE_URL}/saved-quotes/{quote['quote_ref']}/revisions")
    if response.status_code == 200:
        revisions = response.json()
        
        # Format revision data for display
        revision_data = []
        for rev in revisions:
            creation_date = datetime.datetime.fromisoformat(rev["creation_date"].replace("Z", "+00:00"))
            formatted_date = creation_date.strftime("%Y-%m-%d %H:%M")
            
            revision_data.append({
                "Revision": rev["revision_number"],
                "Date": formatted_date,
                "Status": rev["status"].capitalize(),
                "Price": f"R {rev.get('total_price', 0):,.2f}"
            })
        
        st.table(revision_data)
except Exception as e:
    st.error(f"Error loading revision history: {str(e)}")

# Add actions at the bottom
st.divider()
action_cols = st.columns(4)

with action_cols[0]:
    if st.button("Edit This Quote", use_container_width=True):
        # Load this quote for editing (migrated)
        st.session_state.quote_data = quote_data
        st.switch_page("pages/2_Create_New_Quote.py")

with action_cols[1]:
    if st.button("Generate PDF", use_container_width=True):
        st.info("PDF generation functionality will be implemented")

with action_cols[2]:
    # Update status button with dropdown
    new_status = st.selectbox(
        "Change Status",
        ["draft", "sent", "approved", "rejected"],
        index=["draft", "sent", "approved", "rejected"].index(quote["status"]) if quote["status"] in ["draft", "sent", "approved", "rejected"] else 0
    )
    
    if st.button("Update Status", use_container_width=True):
        try:
            response = requests.patch(
                f"{API_BASE_URL}/saved-quotes/{quote_id}/status", 
                json={"status": new_status}
            )
            response.raise_for_status()
            st.success(f"Status updated to {new_status.capitalize()}")
            st.rerun()  # Refresh the page
        except Exception as e:
            st.error(f"Error updating status: {str(e)}")

with action_cols[3]:
    if st.button("Create New Revision", use_container_width=True):
        try:
            # Using user_id 1 for development
            response = requests.post(
                f"{API_BASE_URL}/saved-quotes/{quote_id}/revise", 
                json={"user_id": 1}
            )
            response.raise_for_status()
            new_revision = response.json()
            
            # View the new revision
            st.session_state.viewing_quote_id = new_revision["id"]
            st.rerun()
        except Exception as e:
            st.error(f"Error creating revision: {str(e)}")