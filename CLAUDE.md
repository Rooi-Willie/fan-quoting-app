# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack auxiliary axial fan quoting application for Airblow Fans (South Africa). Generates customized fan quotes with automated component calculations, motor pricing, and Word document exports.

**Tech Stack**: Python 3.8+, FastAPI, Streamlit, PostgreSQL 15, SQLAlchemy, Docker Compose, GCP (Cloud Run + Cloud SQL)

## Common Commands

### Local Development (Docker)
```bash
docker-compose up                # Start all services
docker-compose up --build        # Rebuild after code/dependency/schema changes
docker-compose down -v           # Fresh database (destroys all data)
docker-compose logs -f api       # Watch API logs
docker-compose logs -f ui        # Watch UI logs
```

### Access Points
- **UI**: http://localhost:8501
- **API Docs (Swagger)**: http://localhost:8080/docs
- **Database**: localhost:5433 (dev), localhost:5431 (test)

### Testing
```bash
cd api/
pytest tests/                              # All tests
pytest tests/test_calculation_engine.py -v # Specific file
pytest -k "test_blade_sets"                # Filter by name
pytest --cov=app tests/                    # With coverage
```

Tests use a **dual database architecture** (`api/tests/conftest.py`): master data is copied from the dev DB (5433) into a separate test DB (5431) per session, and each test runs inside a transaction that rolls back after completion.

### Deployment (Google Cloud)
```bash
python deploy/scripts/2_init_database.py   # Update Cloud SQL schema
python deploy/scripts/3_deploy_api.py      # Deploy API to Cloud Run
python deploy/scripts/4_deploy_ui.py       # Deploy UI
```

## Architecture

### 3-Tier Design
```
Streamlit UI (8501) → FastAPI API (8080) → PostgreSQL (5432/5433)
```

- **`api/`**: FastAPI backend — routers, calculation engine, ORM models, Pydantic schemas, CRUD layer
- **`ui/`**: Streamlit multi-page app — quote creation (5 tabs), quote listing, quote detail/edit/delete, Word export, user management (admin)
- **`database/`**: PostgreSQL init scripts and CSV master data files
- **`deploy/`**: GCP deployment automation scripts

### Quote Data Flow
1. User builds quote in UI → `st.session_state.quote_data` is single source of truth
2. UI calls `POST /quotes/components/v3-summary` for server-side calculations
3. API runs factory-pattern calculators against database parameters
4. UI merges server results into local state via `ensure_server_summary_up_to_date()`
5. User saves via `POST /saved-quotes/v3` → stored as JSONB in `saved_quotes.quote_data`

### Calculation Engine (Factory Pattern)
**File**: `api/app/logic/calculation_engine.py`

Components use different calculator classes based on `mass_formula_type` from the `component_parameters` table:
- `CylinderSurfaceCalculator` — hubs, casings
- `ConeSurfaceCalculator` — inlet/outlet cones
- `RotorEmpiricalCalculator` — blade sets (empirical formulas)
- `ScdMassCalculator` — specialized components

Entry point: `calculate_v3_components_summary()` → `get_calculator(mass_formula_type)` → calculator class

### Quote Data Schema (v4 — Multi-Fan Configuration)
Complete JSONB structure in `saved_quotes.quote_data`:
```
quote_data
├── meta                    # Version (4), timestamps, user tracking, source_quote_ids
├── quote                   # SHARED: project & client info, reference number
├── fan_configurations[]    # Array of per-fan config entries:
│   ├── config_index        #   Position index
│   ├── quantity            #   Fan quantity multiplier (≥1)
│   ├── label               #   User-facing label ("Fan Config 1")
│   ├── specification       #   Technical inputs (fan, motor, components, buyouts)
│   ├── pricing             #   Markups, overrides (keyed by component NAME)
│   └── calculations        #   Computed results, unit_total, line_total
├── grand_totals            # Aggregated: components, motors, buyouts, grand_total
└── context                 # SHARED: runtime settings & rates snapshot
```

Each fan configuration is independent — different fan sizes, motors, components, and pricing.
`unit_total` = single-fan price (components + motor + buyouts).
`line_total` = `unit_total × quantity`.
`grand_total` = sum of all configs' `line_total`.

Full schema docs: `../Documentation/quote_data_schema_v3.md`

### Authentication
- **API**: All endpoints (except `/`, `/health`) require `X-API-Key` header. Verified in `api/app/auth.py`.
- **UI**: Dual auth — Google OAuth (restricted to `@airblowfans.co.za`) + database username/password (bcrypt)
- **Roles**: admin, engineer, sales, user, guest

### Role-Based Access Control

| Action | admin | engineer | sales | user | guest |
|--------|-------|----------|-------|------|-------|
| Delete any quote | ✅ | ❌ | ❌ | ❌ | ❌ |
| Delete own quotes | ✅ | ✅ | ✅ | ❌ | ❌ |
| User management | ✅ | ❌ | ❌ | ❌ | ❌ |

### Quote Soft Delete
Quotes use soft delete (`is_deleted`, `deleted_at`, `deleted_by_user_id` columns on the `quotes` table). Deleted quotes are filtered out of all list/get queries via `is_deleted == False`. Deleting a specific revision does **not** cascade to other revisions of the same `quote_ref`.

### User Management
Admin-only page (`ui/pages/6_User_Management.py`). Create users, edit profiles, reset passwords, activate/deactivate accounts. Users are soft-deactivated (`is_active = False`), never hard-deleted. Admins cannot change their own role or deactivate themselves.

## Critical Patterns & Gotchas

### v4 Multi-Config: Always Use Active Config
```python
# ✅ Correct — read/write per-config data via active config
from common import get_active_config
active_cfg = get_active_config(qd)
spec = active_cfg["specification"]
pricing = active_cfg["pricing"]
calc = active_cfg["calculations"]

# ❌ Wrong — top-level specification/pricing/calculations no longer exist
spec = qd["specification"]  # KeyError in v4
```

### Pricing Overrides Use Component Names, Not IDs
```python
# ✅ Correct
overrides = active_cfg['pricing']['overrides'].get(component_name, {})
# ❌ Wrong
overrides = active_cfg['pricing']['overrides'].get(component_id, {})
```

### Blade Sets Stored as String
`specification.fan.blade_sets` is a string (e.g., `"8"`). Cast to `int` before calculations.

### Motor Price Selection
Use `specification.motor.mount_type` (`"Foot"` or `"Flange"`) to pick the correct price from `motor_details`.

### Server vs Client Calculations
- **Client-side** (fast display): `ui/utils.py::update_quote_totals()`
- **Server-side** (authoritative): `POST /quotes/components/v3-summary`
- **Sync**: `ui/utils.py::ensure_server_summary_up_to_date()` merges server results into state

Always follow this sequence when components change:
```python
active_cfg["specification"]["components"] = selected_components
update_quote_totals(st.session_state.quote_data)          # Client-side (all configs)
ensure_server_summary_up_to_date(st.session_state.quote_data)  # Server (active config)
st.rerun()
```

### Widget State Reset
Increment `st.session_state.widget_reset_counter` to force all widgets to recreate with new keys. See `ui/CLAUDE.md` for detailed Streamlit widget patterns including deferred sidebar placeholders, callback guards, `format_func` caching gotchas, and selectbox type safety.

### API Client Wrapper
Use `api_get()` / `api_post()` / `api_patch()` / `api_delete()` from `ui/utils.py` instead of raw `requests` calls — handles auth headers and error logging.

### Timezone
All timestamps use SAST (UTC+2). Database and Docker containers configured for `Africa/Johannesburg`.

### `quote` Section Fields
`quote_data.quote` holds shared project info: `reference`, `client`, `attention_to`, `project`, `location`, `delivery_time`, `notes`. To add a new field: initialize it in `ui/common.py::_new_quote_data()`, add a widget in `ui/pages/quote_creation_tabs/project_info_tab.py`, and expose it in `ui/export_utils.py::prepare_quote_context()`. No DB migration needed — stored in JSONB.

### Word Template (`ui/templates/quote_template.docx`)
Uses `docxtpl` (Jinja2). Paragraph-level loops require `{%p for x in list %}` / `{%p endfor %}` — not inline `{% %}`. Per-config context (e.g. `fan_config.buyout_items`, `fan_config.component_pricing`) is built in `_prepare_single_config_context()` in `export_utils.py`. Edit the `.docx` directly in Word — insert `{{ variable_name }}` tags wherever needed.

## Key Files

| File | Purpose |
|------|---------|
| `api/app/logic/calculation_engine.py` | Factory-pattern component calculators |
| `api/app/crud.py` | Database operations, quote saving, summary extraction |
| `api/app/models.py` | SQLAlchemy ORM models |
| `api/app/schemas.py` | Pydantic request/response schemas |
| `api/app/validation.py` | Quote data validation before saving |
| `ui/common.py` | Schema v4 initialization, config switching, sidebar |
| `ui/utils.py` | API client wrapper, calculation helpers, totals aggregation |
| `ui/export_utils.py` | Word document export via `docxtpl` |
| `ui/pages/2_Create_New_Quote.py` | Main quote creation orchestrator |
| `ui/pages/4_View_Quote_Details.py` | View/edit saved quotes, delete quotes |
| `ui/pages/6_User_Management.py` | Admin-only user CRUD, password reset |
| `api/app/routers/users.py` | User API endpoints (CRUD, password reset) |
| `api/tests/conftest.py` | Dual-database test fixtures |

## Coding Standards

Follow PEP 8. Use type hints (`typing` module). Include docstrings (PEP 257) with description, parameters, and return values. 4-space indentation, 79-char line limit. See `.github/instructions/python_conventions.instructions.md` for full conventions.

## Adding New Features

**New component type**: Add to `database/data/components.csv` and `component_parameters.csv` → implement calculator class if needed in `calculation_engine.py` → update `get_calculator()` factory.

**Schema changes**: Update `ui/common.py::_new_quote_data()` and `_new_fan_config_entry()` → update `api/app/validation.py` → increment `NEW_SCHEMA_VERSION` if breaking.

**New API endpoint**: Define Pydantic schemas in `schemas.py` → add CRUD function in `crud.py` → create router in `api/app/routers/` → register in `main.py` with `dependencies=[Depends(verify_api_key)]`.

**New UI tab**: Create module in `ui/pages/quote_creation_tabs/` → import in `ui/pages/2_Create_New_Quote.py` → use `st.session_state.quote_data` for state.