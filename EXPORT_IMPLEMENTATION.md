# Word Document Export Implementation

## Overview
This implementation adds functionality to export fan quotes as branded Word documents using the `docxtpl` package. The export feature is available in two locations:
1. **Review & Finalize tab** - When creating/editing a quote
2. **View Quote Details page** - When viewing saved quotes

## Files Modified/Created

### New Files
- `fan-quoting-app/ui/export_utils.py` - Core export functionality
- `fan-quoting-app/ui/templates/` - Directory for template storage
- `fan-quoting-app/ui/templates/README.md` - Template documentation

### Modified Files
- `fan-quoting-app/ui/requirements.txt` - Added `docxtpl` and `python-docx` dependencies
- `fan-quoting-app/ui/pages/quote_creation_tabs/review_quote_tab.py` - Added export buttons
- `fan-quoting-app/ui/pages/4_View_Quote_Details.py` - Added export buttons

## Installation & Setup

### 1. Install Dependencies
The UI container needs to rebuild with the new dependencies:

```bash
# Rebuild the UI container
docker-compose build ui

# Or restart the stack
docker-compose down
docker-compose up -d
```

### 2. Add Template File
Place your branded Word template file at:
```
fan-quoting-app/ui/templates/quote_template.docx
```

The template should include all the variables from the mapping table using docxtpl syntax.

## Template Variables Reference

### Simple Variables (use `{{ variable_name }}`)
- `{{ quote_heading }}` - Client - Project
- `{{ client_name }}` - Client name
- `{{ quote_ref }}` - Quote reference
- `{{ quote_date }}` - Current date (UTC+2)
- `{{ project_location }}` - Project location
- `{{ fan_uid }}` - Fan UID
- `{{ fan_size_mm }}` - Fan size in mm
- `{{ blade_sets }}` - Number of blade sets
- `{{ total_mass_kg }}` - Total mass in kg
- `{{ total_length }}` - Total length in mm
- `{{ motor_output }}` - Motor rated output
- `{{ motor_product_range }}` - Motor product range
- `{{ motor_pole }}` - Motor poles
- `{{ motor_speed }}` - Motor speed
- `{{ user_name }}` - Created by username
- `{{ user_position }}` - "Sales Engineer" (dummy)
- `{{ user_tel_number }}` - "+27 XX XXX XXXX" (dummy)
- `{{ user_email }}` - username@airblowfans.co.za
- `{{ rotor_assembly_components }}` - Comma-separated list of rotor components
- `{{ component_subtotal }}` - Component subtotal price
- `{{ motor_unit_price }}` - Motor unit price
- `{{ motor_qty }}` - "1" (hardcoded)
- `{{ motor_total_price }}` - Motor total price
- `{{ grand_total_price }}` - Grand total price

### List Variables (use `{%p for item in list %}...{%p endfor %}`)
For component names list:
```
{%p for comp in components %}
{{ comp.name }}
{%p endfor %}
```

### Table Rows (use `{%tr for item in list %}...{%tr endfor %}`)

For component pricing table:
```
{%tr for comp in component_pricing %}
{{ comp.name }} | {{ comp.unit_price }} | {{ comp.qty }} | {{ comp.total_price }}
{%tr endfor %}
```

For buyout items table:
```
{%tr for buyout in buyout_items %}
{{ buyout.name }} | {{ buyout.unit_price }} | {{ buyout.qty }} | {{ buyout.total_price }}
{%tr endfor %}
```

## Usage

### From Review & Finalize Tab
1. Complete all quote information in the tabs
2. Navigate to "Review & Finalize" tab
3. Click "📄 Download Word Document" button
4. File will download with name: `Quote_{ref}_{client}_{project}_{date}.docx`

### From View Quote Details Page
1. Navigate to "View Existing Quotes"
2. Select and view a quote
3. In the "Actions" section, click "📄 Download Word Document"
4. File will download with the same naming convention

## File Naming Convention
Generated files follow this format:
```
Quote_{reference}_{client}_{project_name}_{date}.docx
```

Example: `Quote_QD001_Piet_Jan_20251002.docx`

## Error Handling
- If template file is missing, user sees error message with instructions
- If docxtpl is not installed, clear error message is displayed
- Missing data in quote_data is handled gracefully with "N/A" fallbacks

## Future Enhancements (PDF)
PDF export functionality is prepared but not yet implemented. Placeholder buttons are in place.

To implement PDF export later:
1. Choose a PDF generation method (docx2pdf, reportlab, etc.)
2. Update `generate_pdf()` function in `export_utils.py`
3. Enable the PDF download buttons
4. Update requirements.txt with PDF library

## Data Flow

```
quote_data (v3 schema)
    ↓
prepare_quote_context() - Extract and format all variables
    ↓
DocxTemplate.render() - Populate template
    ↓
BytesIO - In-memory document
    ↓
st.download_button() - Browser download
```

## Testing Checklist
- [ ] Install dependencies (rebuild UI container)
- [ ] Place template file in ui/templates/
- [ ] Test export from Review & Finalize tab
- [ ] Test export from View Quote Details page
- [ ] Verify all template variables are populated correctly
- [ ] Check dynamic tables (components, buyouts) render properly
- [ ] Verify filename format is correct
- [ ] Test with missing/incomplete quote data
- [ ] Test error handling (missing template)

## Troubleshooting

### Template Not Found Error
- Ensure `quote_template.docx` exists in `fan-quoting-app/ui/templates/`
- Check file permissions

### Import Error
- Rebuild the UI Docker container to install new dependencies
- Verify requirements.txt was updated correctly

### Template Rendering Issues
- Check template syntax matches docxtpl format
- Verify all variables are spelled correctly
- Test template with small dataset first

## Support
For issues or questions about the export functionality, refer to:
- docxtpl documentation: https://docxtpl.readthedocs.io/en/latest/
- export_utils.py for implementation details
- Template variables mapping in this document
