import streamlit as st
import requests
import datetime
import json
import os
from config import APP_TITLE

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
quote_data = quote["quote_data"]

# Fan configuration section
st.header("Fan Configuration")
fan_cols = st.columns(4)
with fan_cols[0]:
    st.metric("Fan Type", quote_data.get("fan_uid", "N/A"))
with fan_cols[1]:
    st.metric("Fan Size", f"{quote_data.get('fan_size_mm', 'N/A')}mm")
with fan_cols[2]:
    st.metric("Blade Sets", str(quote_data.get("blade_sets", "N/A")))
with fan_cols[3]:
    st.metric("Markup", f"{float(quote_data.get('markup_override', 1.0)):.2f}x")

# Motor details
if "selected_motor_details" in quote_data and quote_data["selected_motor_details"]:
    motor = quote_data["selected_motor_details"]
    st.header("Motor Information")
    motor_cols = st.columns(4)
    with motor_cols[0]:
        st.metric("Supplier", motor.get("supplier_name", "N/A"))
    with motor_cols[1]:
        st.metric("Rated Output", f"{motor.get('rated_output', 'N/A')} {motor.get('rated_output_unit', '')}")
    with motor_cols[2]:
        st.metric("Speed", f"{motor.get('speed', 'N/A')} {motor.get('speed_unit', '')}")
    with motor_cols[3]:
        st.metric("Price", f"R {quote_data.get('motor_price_after_markup', 0):,.2f}")

# Components section
if "selected_components_unordered" in quote_data and quote_data["selected_components_unordered"]:
    st.header("Components")
    
    # Create a table of selected components
    component_data = []
    for comp_name in quote_data["selected_components_unordered"]:
        comp_details = quote_data.get("component_details", {}).get(comp_name, {})
        component_data.append({
            "Component": comp_name,
            "Thickness": comp_details.get("Material Thickness", "Default"),
            "Waste Factor": comp_details.get("Fabrication Waste", "Default")
        })
    
    st.table(component_data)

# Buy-out items section
if "buy_out_items_list" in quote_data and quote_data["buy_out_items_list"]:
    st.header("Buy-out Items")
    
    buyout_data = []
    for item in quote_data["buy_out_items_list"]:
        buyout_data.append({
            "Description": item.get("description", ""),
            "Quantity": item.get("quantity", 1),
            "Unit Price": f"R {float(item.get('unit_price', 0)):,.2f}",
            "Total": f"R {float(item.get('unit_price', 0)) * float(item.get('quantity', 1)):,.2f}"
        })
    
    st.table(buyout_data)

# Pricing summary
st.header("Pricing Summary")
price_cols = st.columns(4)

with price_cols[0]:
    st.metric("Total Mass", f"{quote.get('total_mass_kg', 0):.2f} kg")

with price_cols[1]:
    material_cost = 0
    labour_cost = 0
    
    # Extract from server summary if available
    if "server_summary" in quote_data:
        summary = quote_data["server_summary"]
        material_cost = summary.get("total_material_cost", 0)
        labour_cost = summary.get("total_labour_cost", 0)
    
    st.metric("Material Cost", f"R {material_cost:,.2f}")

with price_cols[2]:
    st.metric("Labour Cost", f"R {labour_cost:,.2f}")

with price_cols[3]:
    st.metric("Final Price", f"R {quote.get('total_price', 0):,.2f}", delta="Including Markup")

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
        # Load this quote for editing
        st.session_state.quote_data = quote["quote_data"]
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