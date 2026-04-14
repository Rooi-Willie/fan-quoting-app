"""
Export utilities for generating Word and PDF documents from quote data.

This module provides functions to transform v4 quote_data into Word documents
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
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(current_dir, "templates", template_name)

    if not os.path.exists(template_path):
        raise FileNotFoundError(
            f"Template file not found: {template_path}\n"
            f"Please ensure '{template_name}' exists in the templates/ directory."
        )

    return template_path


def get_rotor_assembly_components(config: Dict[str, Any]) -> str:
    """
    Get a comma-separated list of component names that form the rotor assembly
    for a single fan configuration.

    Parameters:
        config (dict): A single fan configuration entry from fan_configurations[]

    Returns:
        str: Comma-separated list of component names
    """
    try:
        spec = config.get("specification", {})
        fan_config = spec.get("fan", {}).get("fan_configuration", {})
        auto_selected_ids = fan_config.get("auto_selected_components", [])

        if not auto_selected_ids:
            return "N/A"

        components_list = spec.get("components", [])
        component_map = {
            comp.get("id"): comp.get("name")
            for comp in components_list
            if isinstance(comp, dict) and comp.get("id") is not None
        }

        rotor_components = [
            component_map.get(comp_id, f"Component {comp_id}")
            for comp_id in auto_selected_ids
            if comp_id in component_map
        ]

        return ", ".join(rotor_components) if rotor_components else "N/A"

    except Exception as e:
        print(f"Error getting rotor assembly components: {e}")
        return "N/A"


def prepare_component_pricing_table(
    config: Dict[str, Any],
    quantity: int = 1,
) -> List[Dict[str, Any]]:
    """
    Prepare component pricing data for a single fan configuration.

    Parameters:
        config (dict): A single fan configuration entry
        quantity (int): Number of fans in this configuration

    Returns:
        list: List of dicts with keys: name, unit_price, qty, total_price
    """
    component_rows = []

    try:
        components_calc = config.get("calculations", {}).get("components", {})

        if not components_calc:
            return component_rows

        from utils import get_ordered_component_names
        ordered_names = get_ordered_component_names(config)

        for comp_name in ordered_names:
            if comp_name not in components_calc:
                continue

            comp_data = components_calc[comp_name]
            if not isinstance(comp_data, dict):
                continue

            unit_price = float(comp_data.get("total_cost_after_markup", 0))
            total_price = unit_price * quantity

            component_rows.append({
                "name": comp_data.get("name", comp_name),
                "unit_price": f"{unit_price:,.2f}",
                "qty": str(quantity),
                "total_price": f"{total_price:,.2f}",
            })

    except Exception as e:
        print(f"Error preparing component pricing table: {e}")

    return component_rows


def prepare_buyout_items_table(
    config: Dict[str, Any],
    fan_quantity: int = 1,
) -> List[Dict[str, Any]]:
    """
    Prepare buyout items data for a single fan configuration.

    Parameters:
        config (dict): A single fan configuration entry
        fan_quantity (int): Number of fans in this configuration

    Returns:
        list: List of dicts with keys: name, unit_price, qty, total_price
    """
    buyout_rows = []

    try:
        buyout_items = config.get("specification", {}).get("buyouts", [])

        if not buyout_items:
            return buyout_rows

        for item in buyout_items:
            if not isinstance(item, dict):
                continue

            description = item.get("description", "Buyout Item")
            unit_cost = float(item.get("unit_cost", 0))
            item_qty = int(item.get("qty", item.get("quantity", 1)))
            total_qty = item_qty * fan_quantity
            total_cost = unit_cost * total_qty

            buyout_rows.append({
                "name": description,
                "unit_price": f"{unit_cost:,.2f}",
                "qty": str(total_qty),
                "total_price": f"{total_cost:,.2f}",
            })

    except Exception as e:
        print(f"Error preparing buyout items table: {e}")

    return buyout_rows


def _prepare_single_config_context(cfg: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Build template context for a single fan configuration."""
    spec = cfg.get("specification", {})
    pricing = cfg.get("pricing", {})
    calcs = cfg.get("calculations", {})
    fan_section = spec.get("fan", {})
    fan_config = fan_section.get("fan_configuration", {})
    motor_section = spec.get("motor", {})
    motor_details = motor_section.get("motor_details", {})
    component_totals = calcs.get("component_totals", {})
    totals = calcs.get("totals", {})
    quantity = cfg.get("quantity", 1)
    label = cfg.get("label", f"Fan Config {index + 1}")

    component_names = [
        {"name": comp.get("name", f"Component {i+1}")}
        for i, comp in enumerate(spec.get("components", []))
        if isinstance(comp, dict)
    ]

    component_pricing = prepare_component_pricing_table(cfg, quantity)
    buyout_items = prepare_buyout_items_table(cfg, quantity)

    unit_total = calcs.get("unit_total", 0)
    line_total = calcs.get("line_total", 0)

    motor_unit_price = float(
        calcs.get("motor", {}).get("final_price", 0) or 0
    )
    motor_total_price = motor_unit_price * quantity

    component_subtotal = float(totals.get('components', 0)) * quantity

    return {
        "label": label,
        "quantity": quantity,
        "config_number": index + 1,
        "fan_uid": fan_config.get("uid", "N/A"),
        "fan_size_mm": str(fan_config.get("fan_size_mm", "N/A")),
        "blade_sets": str(fan_section.get("blade_sets", "N/A")),
        "components": component_names,
        "total_mass_kg": f"{float(component_totals.get('total_mass_kg', 0)):,.2f}",
        "total_length": f"{float(component_totals.get('total_length_mm', 0)):,.2f}",
        "motor_output": str(motor_details.get("rated_output", "N/A")),
        "motor_product_range": motor_details.get("product_range", "N/A"),
        "motor_pole": str(motor_details.get("poles", "N/A")),
        "motor_speed": str(motor_details.get("speed", "N/A")),
        "rotor_assembly_components": get_rotor_assembly_components(cfg),
        "component_pricing": component_pricing,
        "component_subtotal": f"{component_subtotal:,.2f}",
        "motor_unit_price": f"{motor_unit_price:,.2f}",
        "motor_qty": str(quantity),
        "motor_total_price": f"{motor_total_price:,.2f}",
        "buyout_items": buyout_items,
        "unit_total": f"{float(unit_total):,.2f}",
        "line_total": f"{float(line_total):,.2f}",
    }


def prepare_quote_context(quote_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform v4 quote_data into a context dictionary for the Word template.

    Supports multiple fan configurations. Each config is rendered as a separate
    section in the template via the `fan_configs` list variable.

    Parameters:
        quote_data (dict): The v4 quote data structure

    Returns:
        dict: Context dictionary with all template variables
    """
    meta_section = quote_data.get("meta", {})
    quote_section = quote_data.get("quote", {})
    fan_configurations = quote_data.get("fan_configurations", [])
    grand_totals = quote_data.get("grand_totals", {})

    # Get current date in UTC+2 (South African time)
    sa_timezone = pytz.timezone("Africa/Johannesburg")
    current_date = datetime.now(sa_timezone).strftime("%Y-%m-%d")

    client_name = quote_section.get("client", "")
    project_name = quote_section.get("project", "")
    attention_to = quote_section.get("attention_to", "")
    delivery_time = quote_section.get("delivery_time", "4 - 6 weeks")
    quote_heading = f"{client_name} - {project_name}" if client_name and project_name else (client_name or project_name or "Quote")

    created_by_user = meta_section.get("created_by_user", {})
    user_name = created_by_user.get("full_name", "N/A")
    user_position = created_by_user.get("job_title", "N/A")
    user_email = created_by_user.get("email", "N/A")
    user_tel_number = created_by_user.get("phone", "N/A")

    # Build per-config contexts
    fan_configs = [
        _prepare_single_config_context(cfg, idx)
        for idx, cfg in enumerate(fan_configurations)
    ]
    is_multi_config = len(fan_configs) > 1

    # Build subject line fan sizes string (e.g. "915mm ×4, 762mm ×2")
    subject_parts = []
    for fc in fan_configs:
        size_str = f"{fc['fan_size_mm']}mm"
        qty = fc.get("quantity", 1)
        if qty > 1:
            size_str += f" \u00d7{qty}"
        subject_parts.append(size_str)
    subject_fan_sizes = ", ".join(subject_parts) if subject_parts else "N/A"

    # For single-config quotes, also expose flat variables for backwards-compatible templates
    primary = fan_configs[0] if fan_configs else {}

    context = {
        # Header and project information
        "quote_heading": quote_heading,
        "client_name": client_name or "N/A",
        "attention_to": attention_to or "N/A",
        "delivery_time": delivery_time or "4 - 6 weeks",
        "quote_ref": quote_section.get("reference", "N/A"),
        "quote_date": current_date,
        "project_location": quote_section.get("location", "N/A"),

        # User information
        "user_name": user_name,
        "user_position": user_position,
        "user_tel_number": user_tel_number,
        "user_email": user_email,

        # Multi-config support
        "fan_configs": fan_configs,
        "is_multi_config": is_multi_config,
        "subject_fan_sizes": subject_fan_sizes,

        # Grand totals
        "grand_total_components": f"{float(grand_totals.get('components', 0)):,.2f}",
        "grand_total_motors": f"{float(grand_totals.get('motors', 0)):,.2f}",
        "grand_total_buyouts": f"{float(grand_totals.get('buyouts', 0)):,.2f}",
        "grand_total_price": f"{float(grand_totals.get('grand_total', 0)):,.2f}",
    }

    # Expose primary config fields at top level for single-config templates
    if primary:
        context.update({
            "fan_uid": primary.get("fan_uid", "N/A"),
            "fan_size_mm": primary.get("fan_size_mm", "N/A"),
            "blade_sets": primary.get("blade_sets", "N/A"),
            "components": primary.get("components", []),
            "total_mass_kg": primary.get("total_mass_kg", "0.00"),
            "total_length": primary.get("total_length", "0.00"),
            "motor_output": primary.get("motor_output", "N/A"),
            "motor_product_range": primary.get("motor_product_range", "N/A"),
            "motor_pole": primary.get("motor_pole", "N/A"),
            "motor_speed": primary.get("motor_speed", "N/A"),
            "rotor_assembly_components": primary.get("rotor_assembly_components", "N/A"),
            "component_pricing": primary.get("component_pricing", []),
            "component_subtotal": primary.get("component_subtotal", "0.00"),
            "motor_unit_price": primary.get("motor_unit_price", "0.00"),
            "motor_qty": "1",
            "motor_total_price": primary.get("motor_total_price", "0.00"),
            "buyout_items": primary.get("buyout_items", []),
        })

    return context


def generate_docx(
    quote_data: Dict[str, Any],
    template_name: str = "quote_template.docx"
) -> BytesIO:
    """
    Generate a Word document from quote data using a docxtpl template.

    Parameters:
        quote_data (dict): The v4 quote data structure
        template_name (str): Name of the template file to use

    Returns:
        BytesIO: In-memory byte stream of the generated Word document

    Raises:
        ImportError: If docxtpl is not installed
        FileNotFoundError: If template file does not exist
    """
    if DocxTemplate is None:
        raise ImportError(
            "docxtpl is not installed. Please install it with: pip install docxtpl"
        )

    try:
        template_path = get_template_path(template_name)
        doc = DocxTemplate(template_path)
        context = prepare_quote_context(quote_data)
        doc.render(context)

        output = BytesIO()
        doc.save(output)
        output.seek(0)

        return output

    except Exception as e:
        raise Exception(f"Error generating Word document: {str(e)}")


def generate_filename(quote_data: Dict[str, Any], extension: str = "docx") -> str:
    """
    Generate a filename for the exported document.

    Format: Quote_{reference}_{client}_{project_name}_{date}.{extension}

    Parameters:
        quote_data (dict): The v4 quote data structure
        extension (str): File extension (default: "docx")

    Returns:
        str: Sanitized filename
    """
    quote_section = quote_data.get("quote", {})

    reference = quote_section.get("reference", "UNKNOWN")
    client = quote_section.get("client", "Client")
    project = quote_section.get("project", "Project")

    sa_timezone = pytz.timezone("Africa/Johannesburg")
    date_str = datetime.now(sa_timezone).strftime("%Y%m%d")

    def sanitize(s: str) -> str:
        """Remove characters that are invalid in filenames."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            s = s.replace(char, "_")
        return s.strip()

    reference = sanitize(reference)
    client = sanitize(client)
    project = sanitize(project)

    filename = f"Quote_{reference}_{client}_{project}_{date_str}.{extension}"

    return filename


def generate_pdf(
    quote_data: Dict[str, Any],
    template_name: str = "quote_template.docx"
) -> BytesIO:
    """
    Generate a PDF document from quote data.

    PLACEHOLDER FUNCTION - To be implemented later.
    """
    raise NotImplementedError(
        "PDF generation is not yet implemented. "
        "Use generate_docx() to create Word documents for now."
    )
