# Copilot Instructions for Fan Quoting App

## Project Overview
This is a full-stack application for creating quotes for auxiliary axial fans, consisting of:
- **Backend API** (`/api`): FastAPI service with calculation engine for fan components
- **Frontend UI** (`/ui`): Streamlit interface for quote creation and management
- **Database** (`/database`): PostgreSQL with initialization scripts and CSV data

## Architecture

### Key Components
1. **Database Layer**: PostgreSQL stores configurations, components, and materials
2. **API Layer**: FastAPI service with endpoints for fan configurations, quotes, and calculations
3. **UI Layer**: Streamlit interface with multi-tab workflow for quote creation
4. **Docker**: Each component runs in a containerized environment

### Data Flow
1. User creates quote in UI → API performs calculations → Quote saved to database
2. Fan configurations define available components → Components have calculation formulas → Quotes include calculated components

## Development Workflow

### Local Setup
```bash
# Clone and start the application with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f api  # For API logs
docker-compose logs -f ui   # For UI logs
```

### Testing
```bash
# Run API tests
cd api
pytest tests/

# Note: The test database runs on port 5431 separate from dev database on 5433
```

## Project-Specific Patterns

### Calculation Engine
- Each component type uses a specific calculator based on `mass_formula_type` in database
- Calculators are implemented in `api/app/logic/calculation_engine.py`
- Component costs are calculated based on material, labor, and markup formulas

### Database Models
- SQLAlchemy models in `api/app/models.py` map to database tables
- Pydantic schemas in `api/app/schemas.py` define API request/response structures
- Many-to-many relationships between fan configurations and components

### API Structure
- Router files in `api/app/routers/` organize endpoints by domain (fans, motors, quotes)
- CRUD operations in `api/app/crud.py` handle database interactions
- Main entry point in `api/app/main.py` configures FastAPI and registers routers

### UI Structure
- Main app in `ui/app.py` with Streamlit pages in `ui/pages/`
- Multi-tab quote creation process in `ui/pages/quote_creation_tabs/`
- Session state maintains quote data across page navigation

## Key Integrations
- API → Database: SQLAlchemy ORM with PostgreSQL
- UI → API: HTTP requests to API endpoints
- Authentication: Basic login page with session state

## Environment Configuration
- `.env` file needed at project root with database credentials
- Docker network connects API, UI, and database containers

## Common Gotchas
- Fan component calculations require specific parameters based on formula type
- Quote calculations depend on global settings from database
- Session state in Streamlit must be properly managed to maintain data across tabs
