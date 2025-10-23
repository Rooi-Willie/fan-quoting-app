# Copilot Instructions for Fan Quoting App

## Project Overview
Full-stack auxiliary axial fan quoting application with 3-tier architecture:
- **Database** (`/database`): PostgreSQL with CSV-loaded master data (components, motors, materials)
- **Backend API** (`/api`): FastAPI calculation engine with API key authentication
- **Frontend UI** (`/ui`): Streamlit multi-page app for quote creation and management

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

**API Setup**: `api/app/main.py` uses `dependencies=[Depends(verify_api_key)]` on all routers.

## Development Workflow

### Local Development
```bash
# Start all services (db on :5433, api on :8000, ui on :8501)
docker-compose up -d

# Watch logs
docker-compose logs -f api
docker-compose logs -f ui

# Connect to dev database (DBeaver, pgAdmin, etc.)
# Host: localhost, Port: 5433, Database: fan_quoting_db
```

### Testing Strategy
**Dual Database Approach**: Tests use separate test database (port 5431) with data copied from dev database.

**Workflow** (`api/tests/conftest.py`):
1. Connect to both dev DB (5433) and test DB (5431)
2. Copy all master data (materials, motors, components, fan configs) into test DB within transaction
3. Run test
4. Rollback transaction for next test (fresh data every time)

**Run Tests**:
```bash
# From api/ directory
pytest tests/

# Specific test file
pytest tests/test_calculation_engine.py -v

# Requires: PYTEST_DATABASE_URL and PYTEST_DATABASE_TEST_URL in environment
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
Required in `.env` file at project root:
```bash
# Database
POSTGRES_USER=fanquoting_app
POSTGRES_PASSWORD=<secure_password>
POSTGRES_DB=fan_quoting_db
DATABASE_URL=postgresql://fanquoting_app:<password>@db:5432/fan_quoting_db

# API Authentication
API_KEY=<secure_api_key>

# Testing (separate database)
PYTEST_DATABASE_URL=postgresql://...@localhost:5433/fan_quoting_db
PYTEST_DATABASE_TEST_URL=postgresql://...@localhost:5431/<test_db>
```

### 5. Word Export Feature
Uses `docxtpl` library for branded quote exports. Template at `ui/templates/quote_template.docx`.
- Buttons in: `ui/pages/quote_creation_tabs/review_quote_tab.py` and `ui/pages/4_View_Quote_Details.py`
- Export logic: `ui/export_utils.py`
- See `EXPORT_IMPLEMENTATION.md` for template variable reference

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

### Essential References
- **Schema Documentation**: `../Documentation/quote_data_schema_v3.md` - Complete v3 schema reference with examples
- **Deployment Guide**: `deploy/docs/QUICK_START.md` - Step-by-step deployment instructions

### Key Functions
- **Schema initialization**: `ui/common.py::_new_quote_data()`
- **Calculation dispatcher**: `api/app/logic/calculation_engine.py::get_calculator()`
- **Summary extraction**: `api/app/crud.py::_extract_summary_from_quote_data()`
- **Session state sync**: `ui/common.py::initialize_session_state_from_quote_data()`
- **Test setup**: `api/tests/conftest.py::db_session()` fixture

### Common Tasks
- **Add new component type**: Update `component_parameters` table with calculation parameters, ensure calculator class exists
- **Modify calculations**: Edit calculator classes in `api/app/logic/calculation_engine.py`
- **Change UI flow**: Update tab files in `ui/pages/quote_creation_tabs/`
- **Add API endpoint**: Create in `api/app/routers/`, add to `main.py` with auth dependency