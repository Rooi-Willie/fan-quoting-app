# Copilot Instructions for Fan Quoting App

## Project Overview
Full-stack auxiliary axial fan quoting application for generating customized fan quotes with automated calculations and pricing. Built for Airblow Fans (South Africa) using a modern 3-tier architecture:

- **Database** (`/database`): PostgreSQL 15 with CSV-loaded master data (components, motors, materials, labour rates)
- **Backend API** (`/api`): FastAPI calculation engine with API key authentication, factory-pattern calculators, and JSONB quote storage
- **Frontend UI** (`/ui`): Streamlit multi-page app with OAuth + database authentication, session-based quote management, and Word export
- **Deployment** (`/deploy`): Google Cloud Run + Cloud SQL with automated deployment scripts

**Tech Stack**: Python 3.8+, FastAPI, Streamlit, PostgreSQL 15, SQLAlchemy, Docker Compose, Google Cloud Platform

## Architecture & Critical Patterns

### 1. Quote Data Schema (v3)
**Single source of truth**: All quote data stored as JSONB in `saved_quotes.quote_data` column with 6 logical sections. See `../Documentation/quote_data_schema_v3.md` for complete reference.

**Critical Patterns**:
- **Dual Component Representation**: Components appear minimally in `specification.components` (id + name only), fully detailed in `calculations.components` (all computed values)
- **Name-Based Override Keys**: `pricing.overrides` uses component **names** as keys, NOT IDs
  ```python
  # ✅ Correct
  overrides = quote_data['pricing']['overrides'].get(component_name, {})
  
  # ❌ Wrong - will fail
  overrides = quote_data['pricing']['overrides'].get(component_id, {})
  ```
- **String Blade Sets**: `specification.fan.blade_sets` is stored as string ("8"), must cast to int for calculations
- **Motor Price Selection**: Use `specification.motor.mount_type` ("Foot" or "Flange") to select correct price from `motor_details`

**Key Functions**:
- `ui/common.py::_new_quote_data()` - Initialize empty quote with current schema
- `api/app/crud.py::_extract_summary_from_quote_data()` - Extract summary fields for database listing (fan_uid, total_price, component_list)
- **Full Schema**: `../Documentation/quote_data_schema_v3.md`

### 2. Calculation Engine (Factory Pattern)
**Location**: `api/app/logic/calculation_engine.py`

Components calculate differently based on `mass_formula_type` from database:
1. `_resolve_formulaic_parameters()` - Converts formula-based dimensions to concrete values (e.g., `HUB_DIAMETER_X_1_35`)
2. `get_calculator(mass_formula_type)` - Factory returns appropriate calculator class:
   - `CylinderSurfaceCalculator` - Simple cylinders (hubs, casings)
   - `ConeSurfaceCalculator` - Tapered components (inlet/outlet cones)
   - `RotorEmpiricalCalculator` - Blade sets using empirical formulas
   - `ScdMassCalculator` - Specialized calculations for specific components

**Call Chain**: 
```
UI calculates → API `/quotes/components/v3-summary` → calculation_engine.calculate_v3_components_summary() → get_calculator() → specific calculator.calculate()
```

### 3. Streamlit State Management
**Critical Pattern**: `st.session_state.quote_data` is the single source of truth across all tabs/pages.

**Initialization**:
```python
# New quote - ui/pages/2_Create_New_Quote.py
if "quote_data" not in st.session_state:
    st.session_state.quote_data = _new_quote_data(username)

# Editing existing - ui/pages/4_View_Quote_Details.py
st.session_state.quote_data = loaded_quote_data
initialize_session_state_from_quote_data(st.session_state.quote_data)
```

**Widget Reset**: Increment `st.session_state.widget_reset_counter` to force all widgets to recreate with new keys (more reliable than `st.rerun()` alone).

### 4. API Authentication
All API endpoints (except `/` and `/health`) require API key authentication via `X-API-Key` header.

**UI Setup**:
```python
# ui/utils.py
API_KEY = os.getenv("API_KEY", "")
headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
```

**API Setup**: 
- `api/app/main.py` applies `dependencies=[Depends(verify_api_key)]` to all routers
- `api/app/auth.py::verify_api_key()` validates header against `API_KEY` environment variable

### 5. User Authentication & Authorization
**Dual Authentication System** (October 2025):
1. **Streamlit OAuth**: Google OAuth for initial login (limited to `@airblowfans.co.za` domain)
2. **Database Authentication**: Secondary username/password authentication with bcrypt hashing

**User Roles** (role-based access control):
- `admin` - Full access to all features including user management
- `engineer` - Create/edit quotes, access calculations
- `sales` - View/edit quotes, export functionality
- `user` - View-only access to quotes
- `guest` - Limited read-only access

**User Profile Tracking**: Quote metadata includes full user profile:
```python
"created_by_user": {
    "id": 5,
    "username": "bernard",
    "full_name": "Bernard Viviers",
    "email": "bernard@airblowfans.co.za",
    "role": "admin",
    "department": "Engineering",
    "job_title": "Managing Director"
}
```

**Add New User**:
```bash
# Generate password hash
python utils/hash_password.py

# Insert into database (see WORKFLOW_QUICK_REFERENCE.md for SQL)
```

## Development Workflow

### Local Development (Docker - PREFERRED)
```bash
# Start all services (db:5433, api:8080, ui:8501, test-db:5431)
docker-compose up          # Standard start
docker-compose up --build  # Rebuild after schema/dependency changes
docker-compose down -v     # Fresh start (destroys data)

# Access Points:
# - UI: http://localhost:8501
# - API Docs: http://localhost:8080/docs  
# - DB: localhost:5433 (DBeaver/pgAdmin)
# - Test DB: localhost:5431 (pytest only)

# Watch logs (helpful during development)
docker-compose logs -f api   # API server logs
docker-compose logs -f ui    # Streamlit logs
```

**Why Docker?** Mirrors production environment, isolated test database (5431), auto-reload on code changes, no production data risk.

### Testing Strategy
**Dual Database Architecture**: Separate test database ensures test isolation without polluting dev data.

**Data Copy Workflow** (`api/tests/conftest.py`):
1. `db_session` fixture connects to BOTH dev DB (5433) and test DB (5431)
2. Copies master data (materials, motors, components, fan_configurations) into test DB within transaction
3. Yields test session for test execution
4. Rolls back transaction → next test gets fresh data copy

**Run Tests**:
```bash
cd api/
pytest tests/                              # All tests
pytest tests/test_calculation_engine.py -v # Specific file
pytest -k "test_blade_sets"                # Filter by name

# Required environment variables:
# PYTEST_DATABASE_URL=postgresql://...@localhost:5433/fan_quoting_db
# PYTEST_DATABASE_TEST_URL=postgresql://...@localhost:5431/fan_quoting_test
```

### Deployment (Google Cloud)
**3-Step Process** from `deploy/scripts/`:
```bash
# 1. Initialize/update Cloud SQL schema + data
python deploy/scripts/2_init_database.py

# 2. Deploy API to Cloud Run (auto-scales, min 1 instance)
python deploy/scripts/3_deploy_api.py

# 3. Deploy Streamlit UI to Cloud Run
python deploy/scripts/4_deploy_ui.py
```

**Configuration**: Edit `deploy/config.yaml` (copy from `config.yaml.template`). Contains GCP project, database credentials, API key, auto-shutdown schedules.

**Pre-Deployment Testing** (Optional - use with caution):
```bash
# Test with production Cloud SQL using proxy
.\cloud-sql-proxy.exe --port 5432 abf-fan-quoting-app:us-central1:fan-quoting-db

# Then run API/UI locally against Cloud SQL
cd api && uvicorn app.main:app --reload --port 8080
cd ui && streamlit run Login_Page.py
```

### Code Organization
```
api/app/
├── main.py              # FastAPI app with router registration
├── routers/             # Domain-organized endpoints
│   ├── quotes.py        # Calculation endpoints
│   ├── saved_quotes.py  # CRUD for saved quotes
│   ├── fans.py          # Fan configuration data
│   └── motors.py        # Motor data
├── logic/               
│   └── calculation_engine.py  # Calculator factory & classes
├── crud.py              # Database query layer
├── models.py            # SQLAlchemy ORM models
├── schemas.py           # Pydantic request/response schemas
└── auth.py              # API key verification

ui/pages/
├── 2_Create_New_Quote.py       # Main quote creation orchestrator
├── quote_creation_tabs/        # Individual tab implementations
│   ├── fan_config_tab.py       # Component selection & calculations
│   └── review_quote_tab.py     # Final review & export
└── common.py                   # Shared schema functions
```

## Critical Patterns & Gotchas

### 1. Component Calculation Parameters
Each component type requires specific parameters from `component_parameters` table. Missing parameters cause `ValueError`. Check database for:
- `mass_formula_type` (required) - Determines calculator class
- `diameter_formula_type` (e.g., `HUB_DIAMETER_X_1_35`) - Resolved before calculation
- `length_formula_type` (e.g., `CONICAL_15_DEG`) - Computed from fan size if NULL
- `default_thickness_mm`, `default_fabrication_waste_factor` - Can be overridden in UI

### 2. Server vs. Client Calculations
**Pattern**: UI displays client-side estimates, server validates and returns authoritative calculations.

- **Client**: `ui/utils.py::update_quote_totals()` - Quick aggregation for display
- **Server**: POST to `/quotes/components/v3-summary` - Full calculation with database parameters
- **Sync**: `ui/utils.py::ensure_server_summary_up_to_date()` - Merges server results into `st.session_state.quote_data['calculations']`

### 3. Quote Saving
**Important**: Use `POST /saved-quotes/v3` endpoint which:
1. Validates schema with `validation.validate_quote_data()`
2. Extracts summary fields with `_extract_summary_from_quote_data()`
3. Stores full JSONB in `quote_data` column
4. Populates denormalized summary columns for efficient listing

### 4. Environment Variables
**Required in `.env` file** at project root (Docker Compose reads this):
```bash
# Database
POSTGRES_USER=fanquoting_app
POSTGRES_PASSWORD=<secure_password>
POSTGRES_DB=fan_quoting_db
DATABASE_URL=postgresql://fanquoting_app:<password>@db:5432/fan_quoting_db

# API Authentication
API_KEY=<secure_api_key>

# Testing (separate test database)
POSTGRES_TEST_USER=test_user
POSTGRES_TEST_PASSWORD=<test_password>
POSTGRES_TEST_DB=fan_quoting_test
PYTEST_DATABASE_URL=postgresql://...@localhost:5433/fan_quoting_db
PYTEST_DATABASE_TEST_URL=postgresql://...@localhost:5431/fan_quoting_test

# Google OAuth (UI authentication)
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>

# Streamlit (production only)
STREAMLIT_EMAIL_DOMAIN=airblowfans.co.za
```

**Note**: `docker-compose.yml` maps container port 5432 → host port 5433 for dev DB, 5432 → 5431 for test DB.

### 5. Word Export Feature
Uses `python-docx-template` (`docxtpl`) for branded quote exports.

**Template**: `ui/templates/quote_template.docx` - Microsoft Word document with Jinja2-style placeholders
**Logic**: `ui/export_utils.py` - Populates template with quote data
**Buttons**: 
- `ui/pages/quote_creation_tabs/review_quote_tab.py` - Export from quote creation flow
- `ui/pages/4_View_Quote_Details.py` - Export from saved quote view

**Data Mapping**: Template variables map to `quote_data` schema paths (e.g., `{{ quote.reference }}`, `{{ specification.fan.fan_size_mm }}`).

### 6. South Africa Timezone (SAST)
**Critical Pattern**: All timestamps use South Africa Standard Time (UTC+2).

```python
# api/app/models.py
SAST_TZ = datetime.timezone(datetime.timedelta(hours=2))

def get_sast_now():
    """Return current datetime in SAST (UTC+2)"""
    return datetime.datetime.now(SAST_TZ)
```

**Database Configuration**:
```yaml
# docker-compose.yml
environment:
  - TZ=Africa/Johannesburg
  - PGTZ=Africa/Johannesburg
```

### 6. Data Validation & Error Handling
**Validation Points**:
- **API Input**: Pydantic schemas in `api/app/schemas.py` validate all API requests
- **Quote Save**: `api/app/validation.py::validate_quote_data()` validates complete quote structure before saving
- **Component Parameters**: Missing required parameters (e.g., `mass_formula_type`, `default_thickness_mm`) raise `ValueError` in calculation engine

**Error Propagation**:
```python
# API → Client pattern
try:
    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()  # Raises HTTPError for 4xx/5xx
    data = response.json()
except requests.exceptions.RequestException as e:
    st.error(f"API Error: {e}")  # Display to user in UI
```

**Common Error Sources**:
1. **Missing component parameters** - Check `component_parameters` table for required fields
2. **Schema version mismatch** - `quote_data.meta.version != 3` will reset quote
3. **Name-based override key errors** - Using component ID instead of name in `pricing.overrides`
4. **Type conversion errors** - `specification.fan.blade_sets` is string, must cast to int

### 7. UI State & Cache Management
**State Keys in `st.session_state`**:
- `quote_data` - Complete quote document (primary state)
- `current_fan_config` - Selected fan configuration details
- `logged_in`, `username` - Authentication state (preserved across resets)
- `widget_reset_counter` - Incremented to force widget recreation

**Cache Invalidation Pattern**:
```python
# After component changes, recalculate totals
from utils import update_quote_totals
update_quote_totals(st.session_state.quote_data)

# Then sync with server for authoritative results
from utils import ensure_server_summary_up_to_date
ensure_server_summary_up_to_date(st.session_state.quote_data)
st.rerun()  # Update UI with new calculations
```

**When to Sync with Server**:
- After component selection changes
- After override value changes (thickness, waste factor)
- After markup value changes
- Before saving quote (ensure server validates calculations)

## Quick Navigation

### Essential Documentation
- **🌟 Quick Reference**: `WORKFLOW_QUICK_REFERENCE.md` - Common commands, git workflow, deployment checklist
- **Schema v3**: `../Documentation/quote_data_schema_v3.md` - Complete schema specification with examples
- **Deployment**: `deploy/docs/README.md` - Complete deployment guides and troubleshooting
- **Python Conventions**: `.github/instructions/python_conventions.instructions.md` - Python coding standards (PEP 8, docstrings, type hints)

### Key Functions & Patterns
**Schema Management**:
- `ui/common.py::_new_quote_data()` - Initialize empty quote with v3 schema structure
- `ui/common.py::initialize_session_state_from_quote_data()` - Sync session state from loaded quote
- `api/app/validation.py::validate_quote_data()` - Validate complete quote before saving
- `api/app/crud.py::_extract_summary_from_quote_data()` - Extract searchable summary fields

**Calculation Engine**:
- `api/app/logic/calculation_engine.py::get_calculator()` - Factory pattern dispatcher
- `api/app/logic/calculation_engine.py::_resolve_formulaic_parameters()` - Convert formulas to concrete values
- Calculator classes: `CylinderSurfaceCalculator`, `ConeSurfaceCalculator`, `RotorEmpiricalCalculator`, `ScdMassCalculator`

**State Management**:
- `utils.py::update_quote_totals()` - Client-side totals aggregation
- `utils.py::ensure_server_summary_up_to_date()` - Sync with server calculations
- `ui/pages/2_Create_New_Quote.py` - Main quote orchestrator with tab management

**Testing**:
- `api/tests/conftest.py::db_session()` - Test database fixture with data copy
- `api/tests/conftest.py::setup_test_database()` - Session-level schema setup

### Common Development Tasks

**Add New Component Type**:
1. Add component to `database/data/components.csv`
2. Add parameters to `database/data/component_parameters.csv` (must include `mass_formula_type`)
3. If new calculator needed, add class to `api/app/logic/calculation_engine.py`
4. Update `get_calculator()` factory to handle new `mass_formula_type`
5. Test with `pytest tests/test_calculation_engine.py -v`

**Modify Quote Schema**:
1. Update `ui/common.py::_new_quote_data()` with new structure
2. Update schema documentation in `../Documentation/quote_data_schema_v3.md`
3. Increment `NEW_SCHEMA_VERSION` constant if breaking change
4. Update `api/app/validation.py::validate_quote_data()` for new fields
5. Update UI components that read/write affected paths

**Add New API Endpoint**:
1. Define Pydantic schemas in `api/app/schemas.py`
2. Create CRUD function in `api/app/crud.py` if database access needed
3. Add router endpoint in appropriate file (`api/app/routers/`)
4. Register router in `api/app/main.py` with `dependencies=[Depends(verify_api_key)]`
5. Test endpoint at http://localhost:8080/docs (Swagger UI)

**Add New UI Tab**:
1. Create tab module in `ui/pages/quote_creation_tabs/`
2. Import and add to tab list in `ui/pages/2_Create_New_Quote.py`
3. Access `st.session_state.quote_data` for state, update paths as needed
4. Call `update_quote_totals()` and `st.rerun()` after state changes

### Project Structure Quick Reference
```
fan-quoting-app/
├── .github/
│   ├── copilot-instructions.md          # This file - AI agent guidance
│   └── instructions/
│       └── python_conventions.instructions.md  # Python coding standards
├── api/                                  # FastAPI backend
│   ├── app/
│   │   ├── main.py                      # App entry, router registration
│   │   ├── auth.py                      # API key verification
│   │   ├── crud.py                      # Database queries
│   │   ├── models.py                    # SQLAlchemy ORM models
│   │   ├── schemas.py                   # Pydantic request/response schemas
│   │   ├── validation.py                # Quote data validation
│   │   ├── logic/
│   │   │   └── calculation_engine.py   # Factory pattern calculators
│   │   └── routers/                     # Domain-organized endpoints
│   │       ├── quotes.py                # Calculation endpoints
│   │       ├── saved_quotes.py          # Quote CRUD operations
│   │       ├── fans.py, motors.py       # Master data endpoints
│   │       ├── settings.py              # Global settings & rates
│   │       └── users.py                 # User management
│   └── tests/                           # Pytest test suite
│       ├── conftest.py                  # Dual-database test fixtures
│       └── test_*.py                    # Test modules
├── ui/                                   # Streamlit frontend
│   ├── Login_Page.py                    # Entry point (OAuth + DB auth)
│   ├── pages/
│   │   ├── 2_Create_New_Quote.py       # Main quote orchestrator
│   │   ├── 3_View_All_Quotes.py        # Quote listing & search
│   │   ├── 4_View_Quote_Details.py     # View/edit saved quotes
│   │   └── quote_creation_tabs/        # Individual tab implementations
│   │       ├── project_info_tab.py
│   │       ├── motor_selection_tab.py
│   │       ├── fan_config_tab.py       # Component selection & calcs
│   │       ├── buyout_items_tab.py
│   │       └── review_quote_tab.py     # Final review & export
│   ├── common.py                        # Schema helpers, shared functions
│   ├── utils.py                         # API client, calculations
│   ├── export_utils.py                  # Word export logic
│   └── templates/
│       └── quote_template.docx          # Export template
├── database/
│   ├── init-scripts/                    # SQL schema initialization
│   └── data/                            # CSV master data files
├── deploy/
│   ├── config.yaml                      # Deployment configuration (gitignored)
│   └── scripts/                         # GCP deployment automation
│       ├── 2_init_database.py          # Update Cloud SQL schema
│       ├── 3_deploy_api.py             # Deploy API to Cloud Run
│       └── 4_deploy_ui.py              # Deploy UI to Cloud Run
├── Documentation/
│   └── quote_data_schema_v3.md         # Complete schema documentation
├── docker-compose.yml                   # Local dev environment
├── WORKFLOW_QUICK_REFERENCE.md          # Command cheatsheet
└── README.md                            # Project overview
```

## Python Coding Standards

**Follow `.github/instructions/python_conventions.instructions.md`** for all Python code:
- PEP 8 style guide, 79 character line limit, 4-space indentation
- Type hints using `typing` module: `def calculate(radius: float) -> dict:`
- Docstrings (PEP 257): Include description, parameters, return values
- Clear, descriptive function names with explanatory comments
- Edge case handling with explicit exception messages

**Example**:
```python
def calculate_component_cost(
    mass_kg: float,
    material_price: float,
    markup: float = 1.0
) -> Dict[str, float]:
    """
    Calculate total component cost including markup.
    
    Args:
        mass_kg: Component mass in kilograms
        material_price: Price per kilogram of material
        markup: Markup multiplier (default 1.0 = no markup)
    
    Returns:
        Dict with 'base_cost' and 'total_cost' keys
    
    Raises:
        ValueError: If mass_kg or material_price is negative
    """
    if mass_kg < 0 or material_price < 0:
        raise ValueError("Mass and price must be non-negative")
    
    base_cost = mass_kg * material_price
    total_cost = base_cost * markup
    
    return {
        "base_cost": round(base_cost, 2),
        "total_cost": round(total_cost, 2)
    }
```

## Critical Implementation Patterns

### API Client Wrapper (UI → API Communication)
**Use helper functions** in `ui/utils.py` instead of raw `requests`:
```python
# ✅ Preferred - handles auth, error logging, consistent headers
from utils import api_get, api_post

data = api_get("/fans/configurations")  # Automatic API_KEY header
result = api_post("/quotes/components/v3-summary", payload)

# ❌ Avoid - manual header management, no error handling
response = requests.get(f"{API_BASE_URL}/endpoint", headers={"X-API-Key": API_KEY})
```

### Streamlit Secrets vs Environment Variables
**Pattern**: Try `st.secrets` first (production), fall back to `os.getenv` (local dev):
```python
try:
    API_BASE_URL = st.secrets["API_BASE_URL"] if "API_BASE_URL" in st.secrets else os.getenv("API_BASE_URL", "http://api:8080")
except (KeyError, AttributeError):
    API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8080")
```

### Widget State Reset Pattern
**Use widget keys with counter** to force complete widget reset:
```python
# Increment counter to force all widgets to recreate with new keys
current_counter = st.session_state.get("widget_reset_counter", 0)
st.session_state.widget_reset_counter = current_counter + 1

# Use counter in widget keys
st.selectbox(
    "Component",
    options=components,
    key=f"component_select_{st.session_state.widget_reset_counter}"
)
```

### Database Query Optimization
**JSONB querying** for quote_data:
```python
# Efficient JSONB path queries
from sqlalchemy import func

# Query by nested path
quotes = db.query(SavedQuote).filter(
    SavedQuote.quote_data["specification"]["fan"]["fan_size_mm"].astext == "762"
).all()

# Extract specific JSONB field
fan_sizes = db.query(
    func.jsonb_extract_path_text(SavedQuote.quote_data, "specification", "fan", "fan_size_mm")
).all()
```

### Calculation Chain Pattern
**Always follow this sequence** when components change:
```python
# 1. Update quote_data structure
st.session_state.quote_data["specification"]["components"] = selected_components

# 2. Client-side totals (fast, immediate feedback)
from utils import update_quote_totals
update_quote_totals(st.session_state.quote_data)

# 3. Server validation (authoritative, database-backed)
from utils import ensure_server_summary_up_to_date
ensure_server_summary_up_to_date(st.session_state.quote_data)

# 4. Refresh UI
st.rerun()
```

## Troubleshooting Guide

### "Component parameters missing" errors
**Check `component_parameters` table** - every component needs:
- `mass_formula_type` (required) - Determines calculator class
- `default_thickness_mm` (required for most calculators)
- `default_fabrication_waste_factor` (required)
- Formulaic fields: `diameter_formula_type`, `length_formula_type` (if length_mm is NULL)

### "Override not applied" errors
**Verify override key is component NAME, not ID**:
```python
# quote_data["pricing"]["overrides"]
{
    "Inlet Cone": {"thickness_mm_override": 2.5},  # ✅ Name
    "123": {"thickness_mm_override": 2.5}          # ❌ ID
}
```

### Test failures with "no data in test database"
**Check environment variables** are set correctly:
```bash
# Should be localhost:5433 (dev) and localhost:5431 (test)
PYTEST_DATABASE_URL=postgresql://user:pass@localhost:5433/fan_quoting_db
PYTEST_DATABASE_TEST_URL=postgresql://user:pass@localhost:5431/fan_quoting_test

# Verify test database is running
docker-compose ps  # Should show database-test container
```

### Streamlit session state not persisting
**Check initialization order**:
1. Initialize `quote_data` FIRST (before any widgets)
2. Use `initialize_session_state_from_quote_data()` when loading existing quotes
3. Access `st.session_state.quote_data` directly (don't create local copies)

### Docker container won't start
```bash
# Check logs for specific service
docker-compose logs api
docker-compose logs ui
docker-compose logs db

# Common fixes:
docker-compose down -v      # Remove volumes, fresh start
docker-compose up --build   # Rebuild images
docker system prune -a      # Clean all Docker resources (caution!)
```

---

**For detailed workflows, see**: `WORKFLOW_QUICK_REFERENCE.md`
**For complete schema reference, see**: `../Documentation/quote_data_schema_v3.md`
**For deployment guides, see**: `deploy/docs/README.md`
