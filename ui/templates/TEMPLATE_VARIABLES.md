# Template Variable Mapping - Quick Reference

This document provides a quick reference for mapping template variables in the Word document to the quote_data v3 schema.

## Simple Text Variables

| Template Variable | Quote Data Path | Format/Notes |
|------------------|-----------------|--------------|
| `{{ quote_heading }}` | Combination of `quote.client` and `quote.project` | "Client - Project" |
| `{{ client_name }}` | `quote.client` | Text |
| `{{ quote_ref }}` | `quote.reference` | Text |
| `{{ quote_date }}` | Current date | YYYY-MM-DD (UTC+2) |
| `{{ project_location }}` | `quote.location` | Text |
| `{{ fan_uid }}` | `specification.fan.fan_configuration.uid` | Text (e.g., "Ø915-Ø625") |
| `{{ fan_size_mm }}` | `specification.fan.fan_configuration.fan_size_mm` | Number as string |
| `{{ blade_sets }}` | `specification.fan.blade_sets` | Number as string |
| `{{ total_mass_kg }}` | `calculations.component_totals.total_mass_kg` | Formatted number (e.g., "1,138.01") |
| `{{ total_length }}` | `calculations.component_totals.total_length_mm` | Formatted number |
| `{{ motor_output }}` | `specification.motor.motor_details.rated_output` | Number as string |
| `{{ motor_product_range }}` | `specification.motor.motor_details.product_range` | Text |
| `{{ motor_pole }}` | `specification.motor.motor_details.poles` | Number as string |
| `{{ motor_speed }}` | `specification.motor.motor_details.speed` | Number as string |
| `{{ user_name }}` | `meta.created_by_user.full_name` | Text (e.g., "Bernard Viviers") |
| `{{ user_position }}` | `meta.created_by_user.job_title` | Text (e.g., "Sales Engineer") |
| `{{ user_tel_number }}` | `meta.created_by_user.phone` | Text (e.g., "+27 82 345 6789") |
| `{{ user_email }}` | `meta.created_by_user.email` | Text (e.g., "bernard.viviers@airblowfans.co.za") |
| `{{ rotor_assembly_components }}` | Derived from `specification.fan.fan_configuration.auto_selected_components` | Comma-separated names |
| `{{ component_subtotal }}` | `calculations.totals.components` | Formatted currency |
| `{{ motor_unit_price }}` | `calculations.totals.motor` | Formatted currency |
| `{{ motor_qty }}` | N/A | "1" (hardcoded) |
| `{{ motor_total_price }}` | `calculations.totals.motor` | Formatted currency |
| `{{ grand_total_price }}` | `calculations.totals.grand_total` | Formatted currency |

## List Variables

### Components List
Loop through components to create a bullet list or paragraphs:

```
{%p for comp in components %}
{{ comp.name }}
{%p endfor %}
```

Data source: `specification.components` (array of objects with `id` and `name`)

## Table Variables

### Component Pricing Table
Create a table row for each component:

```
{%tr for comp in component_pricing %}
{{ comp.name }} | {{ comp.unit_price }} | {{ comp.qty }} | {{ comp.total_price }}
{%tr endfor %}
```

Fields available:
- `{{ comp.name }}` - Component name
- `{{ comp.unit_price }}` - Unit price (formatted with 2 decimals)
- `{{ comp.qty }}` - Quantity (always "1")
- `{{ comp.total_price }}` - Total price (formatted with 2 decimals)

Data source: `calculations.components` (transformed into table format)

### Buyout Items Table
Create a table row for each buyout item:

```
{%tr for buyout in buyout_items %}
{{ buyout.name }} | {{ buyout.unit_price }} | {{ buyout.qty }} | {{ buyout.total_price }}
{%tr endfor %}
```

Fields available:
- `{{ buyout.name }}` - Item description
- `{{ buyout.unit_price }}` - Unit price (formatted with 2 decimals)
- `{{ buyout.qty }}` - Quantity
- `{{ buyout.total_price }}` - Total price (formatted with 2 decimals)

Data source: `specification.buyouts` (currently empty in most quotes)

## Currency Formatting
All monetary values are pre-formatted with:
- Thousand separators (,)
- Two decimal places
- Currency symbol (R) should be added in the template itself

Example: If `grand_total_price` is "366,932.36", display as "R 366,932.36"

## Docxtpl Syntax Quick Reference

### Variables
```
{{ variable_name }}
```

### Conditional Display
```
{%p if variable_name %}
Text to show if variable exists
{%p endif %}
```

### Lists (Paragraphs)
```
{%p for item in list %}
{{ item.field }}
{%p endfor %}
```

### Tables (Rows)
```
{%tr for item in list %}
{{ item.col1 }} | {{ item.col2 }} | {{ item.col3 }}
{%tr endfor %}
```

### Conditional Lists
```
{%p if list %}
{%p for item in list %}
- {{ item.name }}
{%p endfor %}
{%p else %}
No items available
{%p endif %}
```

## Example Template Structure

```
QUOTATION

Project: {{ quote_heading }}
Date: {{ quote_date }}
Reference: {{ quote_ref }}

CLIENT INFORMATION
Name: {{ client_name }}
Location: {{ project_location }}

FAN SPECIFICATION
Fan Model: {{ fan_uid }}
Fan Size: {{ fan_size_mm }} mm
Blade Sets: {{ blade_sets }}

Components:
{%p for comp in components %}
- {{ comp.name }}
{%p endfor %}

PRICING BREAKDOWN

Components:
| Component | Unit Price | Qty | Total |
{%tr for comp in component_pricing %}
| {{ comp.name }} | R {{ comp.unit_price }} | {{ comp.qty }} | R {{ comp.total_price }} |
{%tr endfor %}

Subtotal: R {{ component_subtotal }}

Motor: R {{ motor_total_price }}

GRAND TOTAL: R {{ grand_total_price }}

Prepared by: {{ user_name }}
Position: {{ user_position }}
Email: {{ user_email }}
Tel: {{ user_tel_number }}
```

## Notes
- All numeric values are pre-formatted as strings with appropriate formatting
- Missing data defaults to "N/A"
- Currency symbols should be added in the template (not in the data)
- Dates are in UTC+2 (South African time)
- All prices exclude VAT unless otherwise specified in the template
