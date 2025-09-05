# fan-quoting-app
Auxiliary axial fan quoting application.

## Overview
This repository contains a Streamlit UI and FastAPI backend for creating and managing axial fan quotations. Quote state is persisted as JSON (`quote_data`) alongside relational summary columns for efficient listing.

## Quote Data Schema (v2)
The application now uses a nested, versioned schema (version = 2) for all new and edited quotes. Key characteristics:
* `meta.version` indicates schema version (currently 2).
* Structured domains: `project`, `fan`, `components`, `motor`, `buy_out_items`, `calculation`, and optional `settings_snapshot`.
* Clear separation of user inputs (`overrides`) vs system outputs (`calculated`) within `components.by_name[component]`.
* Backend derives consolidated pricing totals in `calculation.derived_totals` (components, motor, buy-out, grand total).

Legacy flat quotes are migrated on load. The UI writes only nested keys; migration code is idempotent.

See full specification, migration details, sample JSON, and extension guidelines here:
`../Documentation/quote_data_schema_v2.md`

## Development Notes
* UI: Streamlit multi-tab workflow (project info, motor selection, fan config, buy-out items, review & save).
* Backend: FastAPI with CRUD operations; summary extraction centralised in `crud._extract_summary_from_quote_data`.
* Database: PostgreSQL (JSONB for `quote_data`).

## Next Steps (Planned)
* Add automated tests for migration idempotency & derived totals.
* Introduce labour/logistics cost domains.
* Endpoint to recalculate derived totals for historical quotes.

## License
Internal use (license details TBD).
