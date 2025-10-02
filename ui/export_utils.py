"""
Export utilities for generating Word and PDF documents from quote data.

This module provides functions to transform v3 quote_data into Word documents
using docxtpl templates with company branding.
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from io import BytesIO
import pytz

try:
    from docxtpl import DocxTemplate
except ImportError:
    DocxTemplate = None


def get_template_path(template_name: str = "quote_template.docx") -> str:
    """
    Get the absolute path to the Word template file.
    
    Parameters:
        template_name (str): Name of the template file
        
    Returns:
        str: Absolute path to the template file
        
    Raises:
        FileNotFoundError: If template file does not exist
    """
    # Get the directory where this file is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(current_dir, "templates", template_name)
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(
            f"Template file not found: {template_path}\n"
            f"Please ensure '{template_name}' exists in the templates/ directory."
        )
    
    return template_path


def get_rotor_assembly_components(quote_data: Dict[str, Any]) -> str:
    """
    Get a comma-separated list of component names that form the rotor assembly.
    
    The rotor assembly components are identified by the auto_selected_components
    list in the fan configuration.
    
    Parameters:
        quote_data (dict): The v3 quote data structure
        
    Returns:
        str: Comma-separated list of component names (e.g., "Rotor, Motor Barrel")
    """
    try:
        # Get auto-selected component IDs from fan configuration
        fan_config = (
            quote_data.get("specification", {})
            .get("fan", {})
            .get("fan_configuration", {})
        )
        auto_selected_ids = fan_config.get("auto_selected_components", [])
        
        if not auto_selected_ids:
            return "N/A"
        
        # Get component names from specification.components
        # This list has objects with 'id' and 'name' fields
        components_list = quote_data.get("specification", {}).get("components", [])
        
        # Build a mapping of id -> name
        component_map = {
            comp.get("id"): comp.get("name")
            for comp in components_list
            if isinstance(comp, dict) and comp.get("id") is not None
        }
        
        # Get names for auto-selected components
        rotor_components = [
            component_map.get(comp_id, f"Component {comp_id}")
            for comp_id in auto_selected_ids
            if comp_id in component_map
        ]
        
        return ", ".join(rotor_components) if rotor_components else "N/A"
        
    except Exception as e:
        print(f"Error getting rotor assembly components: {e}")
        return "N/A"


def prepare_component_pricing_table(quote_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Prepare component pricing data for the dynamic table in the Word template.
    
    Parameters:
        quote_data (dict): The v3 quote data structure
        
    Returns:
        list: List of dicts with keys: name, unit_price, qty, total_price
    """
    component_rows = []
    
    try:
        # Get components from calculations section
        components_calc = quote_data.get("calculations", {}).get("components", {})
        
        if not components_calc:
            return component_rows
        
        # Iterate through each component
        for comp_name, comp_data in components_calc.items():
            if not isinstance(comp_data, dict):
                continue
            
            unit_price = comp_data.get("total_cost_after_markup", 0)
            qty = 1  # Hardcoded as per requirements
            total_price = unit_price  # Same as unit price since qty is 1
            
            component_rows.append({
                "name": comp_data.get("name", comp_name),
                "unit_price": f"{float(unit_price):,.2f}",
                "qty": str(qty),
                "total_price": f"{float(total_price):,.2f}",
            })
    
    except Exception as e:
        print(f"Error preparing component pricing table: {e}")
    
    return component_rows


def prepare_buyout_items_table(quote_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Prepare buyout items data for the dynamic table in the Word template.
    
    Parameters:
        quote_data (dict): The v3 quote data structure
        
    Returns:
        list: List of dicts with keys: name, unit_price, qty, total_price
    """
    buyout_rows = []
    
    try:
        # Get buyout items from specification section
        buyout_items = quote_data.get("specification", {}).get("buyouts", [])
        
        if not buyout_items:
            return buyout_rows
        
        # Iterate through each buyout item
        for item in buyout_items:
            if not isinstance(item, dict):
                continue
            
            description = item.get("description", "Buyout Item")
            unit_cost = item.get("unit_cost", 0)
            quantity = item.get("quantity", 1)
            total_cost = float(unit_cost) * float(quantity)
            
            buyout_rows.append({
                "name": description,
                "unit_price": f"{float(unit_cost):,.2f}",
                "qty": str(quantity),
                "total_price": f"{float(total_cost):,.2f}",
            })
    
    except Exception as e:
        print(f"Error preparing buyout items table: {e}")
    
    return buyout_rows


def prepare_quote_context(quote_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform v3 quote_data into a context dictionary for the Word template.
    
    This function maps all the template variables from the quote_data structure
    to the format expected by the docxtpl template.
    
    Parameters:
        quote_data (dict): The v3 quote data structure
        
    Returns:
        dict: Context dictionary with all template variables
    """
    # Extract main sections from v3 schema
    meta_section = quote_data.get("meta", {})
    quote_section = quote_data.get("quote", {})
    spec_section = quote_data.get("specification", {})
    calc_section = quote_data.get("calculations", {})
    
    # Extract sub-sections
    fan_section = spec_section.get("fan", {})
    fan_config = fan_section.get("fan_configuration", {})
    motor_section = spec_section.get("motor", {})
    motor_details = motor_section.get("motor_details", {})
    components_list = spec_section.get("components", [])
    
    component_totals = calc_section.get("component_totals", {})
    totals_section = calc_section.get("totals", {})
    
    # Get current date in UTC+2 (South African time)
    sa_timezone = pytz.timezone("Africa/Johannesburg")
    current_date = datetime.now(sa_timezone).strftime("%Y-%m-%d")
    
    # Get client and project for quote heading
    client_name = quote_section.get("client", "")
    project_name = quote_section.get("project", "")
    quote_heading = f"{client_name} - {project_name}" if client_name and project_name else (client_name or project_name or "Quote")
    
    # Get user information
    created_by = meta_section.get("created_by", "User")
    user_email = f"{created_by}@airblowfans.co.za"
    
    # Get component names as a list for the components list
    component_names = [
        {"name": comp.get("name", f"Component {i+1}")}
        for i, comp in enumerate(components_list)
        if isinstance(comp, dict)
    ]
    
    # Prepare dynamic tables
    component_pricing = prepare_component_pricing_table(quote_data)
    buyout_items = prepare_buyout_items_table(quote_data)
    
    # Build the context dictionary
    context = {
        # Header and project information
        "quote_heading": quote_heading,
        "client_name": client_name or "N/A",
        "quote_ref": quote_section.get("reference", "N/A"),
        "quote_date": current_date,
        "project_location": quote_section.get("location", "N/A"),
        
        # Fan specifications
        "fan_uid": fan_config.get("uid", "N/A"),
        "fan_size_mm": str(fan_config.get("fan_size_mm", "N/A")),
        "blade_sets": str(fan_section.get("blade_sets", "N/A")),
        
        # Components
        "components": component_names,
        "total_mass_kg": f"{float(component_totals.get('total_mass_kg', 0)):,.2f}",
        "total_length": f"{float(component_totals.get('total_length_mm', 0)):,.2f}",
        
        # Motor information
        "motor_output": str(motor_details.get("rated_output", "N/A")),
        "motor_product_range": motor_details.get("product_range", "N/A"),
        "motor_pole": str(motor_details.get("poles", "N/A")),
        "motor_speed": str(motor_details.get("speed", "N/A")),
        
        # User information (with dummy values as requested)
        "user_name": created_by,
        "user_position": "Sales Engineer",  # Dummy value
        "user_tel_number": "+27 XX XXX XXXX",  # Dummy value
        "user_email": user_email,
        
        # Rotor assembly components
        "rotor_assembly_components": get_rotor_assembly_components(quote_data),
        
        # Dynamic pricing tables
        "component_pricing": component_pricing,
        "component_subtotal": f"{float(totals_section.get('components', 0)):,.2f}",
        
        # Motor pricing
        "motor_unit_price": f"{float(totals_section.get('motor', 0)):,.2f}",
        "motor_qty": "1",  # Hardcoded as per requirements
        "motor_total_price": f"{float(totals_section.get('motor', 0)):,.2f}",
        
        # Buyout items (empty for now as per requirements)
        "buyout_items": buyout_items,
        
        # Grand total
        "grand_total_price": f"{float(totals_section.get('grand_total', 0)):,.2f}",
    }
    
    return context


def generate_docx(
    quote_data: Dict[str, Any],
    template_name: str = "quote_template.docx"
) -> BytesIO:
    """
    Generate a Word document from quote data using a docxtpl template.
    
    Parameters:
        quote_data (dict): The v3 quote data structure
        template_name (str): Name of the template file to use
        
    Returns:
        BytesIO: In-memory byte stream of the generated Word document
        
    Raises:
        ImportError: If docxtpl is not installed
        FileNotFoundError: If template file does not exist
        Exception: For other errors during document generation
    """
    if DocxTemplate is None:
        raise ImportError(
            "docxtpl is not installed. Please install it with: pip install docxtpl"
        )
    
    try:
        # Get template path
        template_path = get_template_path(template_name)
        
        # Load the template
        doc = DocxTemplate(template_path)
        
        # Prepare context from quote data
        context = prepare_quote_context(quote_data)
        
        # Render the template with context
        doc.render(context)
        
        # Save to BytesIO object
        output = BytesIO()
        doc.save(output)
        output.seek(0)  # Reset pointer to beginning
        
        return output
        
    except Exception as e:
        raise Exception(f"Error generating Word document: {str(e)}")


def generate_filename(quote_data: Dict[str, Any], extension: str = "docx") -> str:
    """
    Generate a filename for the exported document.
    
    Format: Quote_{reference}_{client}_{project_name}_{date}.{extension}
    
    Parameters:
        quote_data (dict): The v3 quote data structure
        extension (str): File extension (default: "docx")
        
    Returns:
        str: Sanitized filename
    """
    quote_section = quote_data.get("quote", {})
    
    # Get values
    reference = quote_section.get("reference", "UNKNOWN")
    client = quote_section.get("client", "Client")
    project = quote_section.get("project", "Project")
    
    # Get current date
    sa_timezone = pytz.timezone("Africa/Johannesburg")
    date_str = datetime.now(sa_timezone).strftime("%Y%m%d")
    
    # Sanitize strings (remove special characters that are invalid in filenames)
    def sanitize(s: str) -> str:
        """Remove characters that are invalid in filenames."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            s = s.replace(char, "_")
        return s.strip()
    
    reference = sanitize(reference)
    client = sanitize(client)
    project = sanitize(project)
    
    # Build filename
    filename = f"Quote_{reference}_{client}_{project}_{date_str}.{extension}"
    
    return filename


def generate_pdf(
    quote_data: Dict[str, Any],
    template_name: str = "quote_template.docx"
) -> BytesIO:
    """
    Generate a PDF document from quote data.
    
    PLACEHOLDER FUNCTION - To be implemented later.
    Will convert the generated DOCX to PDF using a suitable library.
    
    Parameters:
        quote_data (dict): The v3 quote data structure
        template_name (str): Name of the template file to use
        
    Returns:
        BytesIO: In-memory byte stream of the generated PDF document
        
    Raises:
        NotImplementedError: This function is not yet implemented
    """
    raise NotImplementedError(
        "PDF generation is not yet implemented. "
        "Use generate_docx() to create Word documents for now."
    )
    
    # Future implementation options:
    # 1. Use docx2pdf library (requires MS Word or LibreOffice)
    # 2. Use reportlab to generate PDF directly
    # 3. Use python-docx + pdfkit
    # 4. Use cloud service for conversion
