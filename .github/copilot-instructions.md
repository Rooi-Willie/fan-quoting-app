# Copilot Instructions for Fan Quoting App

## Project Overview
Full-stack application for creating and managing quotes for auxiliary axial fans, consisting of:
- **Backend API** (`/api`): FastAPI service with calculation engine for fan components
- **Frontend UI** (`/ui`): Streamlit interface for quote creation and management
- **Database** (`/database`): PostgreSQL with initialization scripts and CSV data

## Architecture & Data Flow

### Key Components
1. **Database Layer**: PostgreSQL stores configurations, components, materials and quote data
2. **API Layer**: FastAPI service for calculations and CRUD operations
3. **UI Layer**: Streamlit with multi-tab workflow for quote creation and management
4. **Docker**: Each component runs in a containerized environment (see `docker-compose.yml`)

### Critical Data Model Concepts
- **Quote Data Schema**: Modern structured JSON with logical sections (`quote_data` column)
  - Organized sections: `meta`, `quote`, `specification`, `pricing`, `calculations`, `context`
  - Clear separation between technical specs, pricing data, and computed results
  - Full schema defined in `Documentation/quote_data_schema_v3.md`
- **Fan configurations**: Define available components and technical specifications
- **Components**: Each has calculation parameters and formula types

### Calculation Engine
- Core logic in `api/app/logic/calculation_engine.py`
- Each component uses specific calculator based on `mass_formula_type` from database
- Formula types include: cylinder, cone, blade, empirical formulas
- Component costs calculated based on material, labor, and markup formulas

## Development Workflow

### Local Setup
```bash
# Clone and start the application with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f api  # API logs
docker-compose logs -f ui   # UI logs
```

### Testing
- Tests are in `api/tests/` directory
- Test data in JSON files: `api/tests/test_data/`
- Run tests: `cd api && pytest tests/`
- Test database runs on port 5431 (separate from dev database on 5433)

### Code Structure Patterns
- **API Routes**: Organized by domain in `/api/app/routers/`
- **Models**: SQLAlchemy models in `/api/app/models.py` map to DB tables
- **Schemas**: Pydantic schemas in `/api/app/schemas.py` for API request/response
- **UI Pages**: Streamlit multi-page app with numbered files in `/ui/pages/`
- **Quote Creation Flow**: Tab-based workflow in `/ui/pages/quote_creation_tabs/`

### Python Conventions
- Follow PEP 8 style guide (4 spaces for indentation)
- Use type hints for all function signatures
- Include docstrings for all functions and classes
- Handle edge cases with clear exception handling

## Common Gotchas
1. **Quote Data Schema**: Must use structured sections (`specification`, `pricing`, `calculations`)
2. **Component Calculations**: Each requires specific parameters based on formula type
3. **Session State**: Streamlit requires careful management across tabs/pages
4. **Docker Network**: API, UI, and DB containers communicate via internal network
5. **Environment**: `.env` file required at project root with database credentials
6. **Schema Functions**: Use `_new_quote_data()` for new quotes

## Real-World Examples
- Fan component calculation: `api/app/logic/calculation_engine.py` has specialized classes for each formula type
- Quote creation workflow: `ui/pages/2_Create_New_Quote.py` orchestrates multi-tab UI flow
- Schema structure: `ui/pages/common.py` contains `_new_quote_data()` function

### UI State Management (Streamlit)
- **Primary Mechanism**: The app uses `st.session_state` extensively to maintain state across user interactions and page reruns.
- **Central State Object**: `st.session_state.quote_data` holds the entire quote document being created or edited. It's the single source of truth for the UI.
- **Initialization**: On the `2_Create_New_Quote.py` page, `st.session_state.quote_data` is initialized with a clean schema structure using `_new_quote_data()` from `ui/pages/common.py`.
- **Authentication**: `st.session_state.logged_in` and `st.session_state.username` track user login status. Pages are protected by checking `st.session_state.logged_in`.
- **Data Binding**: UI widgets in the quote creation tabs bind to schema paths within `st.session_state.quote_data`. For example, project info uses `st.session_state.quote_data['quote']['client_name']`.
- **State Reset**: The "Start New Quote" button uses `st.session_state.clear()` and then immediately restores auth state, providing a controlled reset of the form.
