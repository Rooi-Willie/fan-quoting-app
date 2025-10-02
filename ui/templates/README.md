# Templates Directory

This directory contains Word document templates for quote generation.

## Files

- `quote_template.docx` - Main quote template with docxtpl placeholders

## Template Variables

The template uses docxtpl syntax for variable substitution:
- Simple variables: `{{ variable_name }}`
- For loops: `{%p for item in items %}...{%p endfor %}`
- Table rows: `{%tr for item in items %}...{%tr endfor %}`

Place your branded Word template file here as `quote_template.docx`.
