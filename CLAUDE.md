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
- **`ui/`**: Streamlit multi-page app — quote creation (5 tabs), quote listing, quote detail/edit, Word export
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

### Quote Data Schema (v3)
Complete JSONB structure in `saved_quotes.quote_data`:
```
quote_data
├── meta              # Version, timestamps, user tracking
├── quote             # Project & client info, reference number
├── specification     # Technical inputs (fan, motor, components, buyouts)
├── pricing           # Markups, overrides (keyed by component NAME, not ID)
├── calculations      # Computed results & server summary
└── context           # Runtime settings & rates snapshot
```

Full schema docs: `../Documentation/quote_data_schema_v3.md`

### Authentication
- **API**: All endpoints (except `/`, `/health`) require `X-API-Key` header. Verified in `api/app/auth.py`.
- **UI**: Dual auth — Google OAuth (restricted to `@airblowfans.co.za`) + database username/password (bcrypt)
- **Roles**: admin, engineer, sales, user, guest

## Critical Patterns & Gotchas

### Pricing Overrides Use Component Names, Not IDs
```python
# ✅ Correct
overrides = quote_data['pricing']['overrides'].get(component_name, {})
# ❌ Wrong
overrides = quote_data['pricing']['overrides'].get(component_id, {})
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
st.session_state.quote_data["specification"]["components"] = selected_components
update_quote_totals(st.session_state.quote_data)          # Client-side
ensure_server_summary_up_to_date(st.session_state.quote_data)  # Server
st.rerun()
```

### Widget State Reset
Increment `st.session_state.widget_reset_counter` to force all widgets to recreate with new keys.

### API Client Wrapper
Use `api_get()` / `api_post()` from `ui/utils.py` instead of raw `requests` calls — handles auth headers and error logging.

### Timezone
All timestamps use SAST (UTC+2). Database and Docker containers configured for `Africa/Johannesburg`.

## Key Files

| File | Purpose |
|------|---------|
| `api/app/logic/calculation_engine.py` | Factory-pattern component calculators |
| `api/app/crud.py` | Database operations, quote saving, summary extraction |
| `api/app/models.py` | SQLAlchemy ORM models |
| `api/app/schemas.py` | Pydantic request/response schemas |
| `api/app/validation.py` | Quote data validation before saving |
| `ui/common.py` | Schema v3 initialization (`_new_quote_data()`), state management |
| `ui/utils.py` | API client wrapper, calculation helpers, totals aggregation |
| `ui/export_utils.py` | Word document export via `docxtpl` |
| `ui/pages/2_Create_New_Quote.py` | Main quote creation orchestrator |
| `ui/pages/4_View_Quote_Details.py` | View/edit saved quotes |
| `api/tests/conftest.py` | Dual-database test fixtures |

## Coding Standards

Follow PEP 8. Use type hints (`typing` module). Include docstrings (PEP 257) with description, parameters, and return values. 4-space indentation, 79-char line limit. See `.github/instructions/python_conventions.instructions.md` for full conventions.

## Adding New Features

**New component type**: Add to `database/data/components.csv` and `component_parameters.csv` → implement calculator class if needed in `calculation_engine.py` → update `get_calculator()` factory.

**Schema changes**: Update `ui/common.py::_new_quote_data()` → update `api/app/validation.py` → increment `NEW_SCHEMA_VERSION` if breaking → update `../Documentation/quote_data_schema_v3.md`.

**New API endpoint**: Define Pydantic schemas in `schemas.py` → add CRUD function in `crud.py` → create router in `api/app/routers/` → register in `main.py` with `dependencies=[Depends(verify_api_key)]`.

**New UI tab**: Create module in `ui/pages/quote_creation_tabs/` → import in `ui/pages/2_Create_New_Quote.py` → use `st.session_state.quote_data` for state.