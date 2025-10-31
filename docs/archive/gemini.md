# Gemini Project Helper: Fan Quoting App

## 1. Overview

The primary goal of this project is to create a modern web application that replaces a complex, multi-sheet Excel workbook for generating industrial axial fan quotes. The application will centralize all data and calculation logic, providing a robust, maintainable, and user-friendly workflow.

A critical requirement is the support for **live, intermediate calculations**. As a user selects components or modifies parameters in the UI, the API must calculate and return a detailed cost and mass breakdown for that specific component in real-time, not just a final total at the end.

### Current Status

The application uses a modern **quote data schema** with structured sections:

- **Quote Schema**: Quotes use structured sections (`meta`, `quote`, `specification`, `pricing`, `calculations`, `context`)
- **Documentation**: Complete schema specification in `../Documentation/quote_data_schema_v3.md`

## 2. System Architecture

-   **Backend**: A Python FastAPI application serves as the core logic layer. It connects to the database and exposes a RESTful API.
-   **Frontend**: A Python Streamlit application provides the user interface. It is a pure client that communicates with the FastAPI backend via HTTP requests.
-   **Database**: A PostgreSQL database stores all persistent data, including configurations, parameters, and cost rates.
-   **Containerization**: The entire application stack (UI, API, DB) is managed and run via Docker and Docker Compose.

## 3. Development Workflow

-   **Run the application**: `docker-compose up`
-   **Run tests**: `pytest`

## 4. Core Functionality

### 4.1. Fan Configuration & Selection

The user workflow begins with selecting a base **Fan Configuration**, which is defined by a `fan_size_mm` and `hub_size_mm` (e.g., "Ø762-Ø472"). This primary selection dictates all subsequent available options, such as:

-   A filtered list of available blade quantities (e.g., `{8, 10, 12}`).
-   A filtered list of compatible motor power ratings (e.g., `{22, 30, 37, 45}` kW).
-   A filtered list of available components for the fan assembly.

### 4.2. Quote Calculation Engine

The engine is the heart of the application, responsible for translating user selections into concrete numbers. It is located in `api/app/logic/calculation_engine.py` and supports two distinct modes of calculation:

-   **Live, Per-Component Calculation**: 
    -   **Purpose**: To provide immediate feedback in the UI's configuration table.
    -   **Trigger**: Called every time a user selects a new component or modifies a parameter (e.g., thickness).
    -   **Functionality**: Calculates the complete, detailed breakdown for a **single component**. This includes all intermediate steps: Overall Diameter, Total Length, Stiffening Factor, Ideal Mass, Real Mass, Feedstock Mass, Material Cost, and Labour Cost.

-   **Full Quote Aggregation**:
    -   **Purpose**: To calculate the final grand total for the entire quote.
    -   **Trigger**: Called from the "Review & Finalize" tab in the UI.
    -   **Functionality**: Aggregates the Total Cost from all selected components, adds costs from buy-out items and the selected motor, and applies the final markup.

## 5. Project Structure

```
.
├───api/                    # FastAPI Backend
│   ├───app/
│   │   ├───logic/            # Core business logic
│   │   │   └───calculation_engine.py
│   │   ├───routers/        # API endpoint definitions
│   │   ├───models.py       # SQLAlchemy ORM models
│   │   └───schemas.py      # Pydantic data validation models
│   └───tests/              # Backend tests
├───database/
│   ├───data/               # CSV files for initial DB seeding
│   └───init-scripts/       # SQL scripts for schema creation
└───ui/                     # Streamlit Frontend
    ├───app.py              # Main UI application entry point
    └───pages/              # Individual UI pages
```

## 6. Database Architecture

The PostgreSQL schema is defined in `api/app/models.py`. Key tables include:

-   `fan_configurations`: The primary table defining fan models and their available options.
-   `components`: A master list of all possible components. The `order_by` column is critical for UI display logic.
-   **Parameter Hierarchy**:
    -   `component_parameters`: Stores **default** parameters and formula identifiers (e.g., `mass_formula_type = 'CONE_SURFACE'`) for a generic component type.
    -   `fan_component_parameters`: An **override** table that stores fixed values (e.g., `length_mm`) for a component when used with a specific fan configuration. This value takes precedence over any formula.
-   `materials` & `labor_rates`: Lookup tables for all cost data.
-   `motors` & `motor_prices`: Stores motor specifications and pricing history.

## 7. API Backend

The API, defined in `api/app/routers/`, exposes the application's functionality.

-   **/fans & /motors Endpoints**: Provide read-only access to configurations, components, and motor lists to populate UI dropdowns.
-   **/quotes & /components Calculation Endpoints**:
    -   `POST /components/calculate-details`: The workhorse endpoint for the UI. It receives the `fan_config_id`, `component_id`, and any user overrides. It returns a detailed JSON object with the full calculation breakdown for that **single component** (diameter, mass, cost, etc.).
    -   `POST /quotes/calculate`: The endpoint for the final review. It receives the complete set of selections for the entire quote and returns an aggregated summary including the grand total.

## 8. API Schemas

The API schemas are defined in `api/app/schemas.py`. The key models for the calculation endpoints are:

-   **`ComponentQuoteRequest`**: The input for the `POST /components/calculate-details` endpoint.
-   **`QuoteRequest`**: The input for the `POST /quotes/calculate` endpoint.
-   **`CalculatedComponent`**: The response from the `POST /components/calculate-details` endpoint.
-   **`QuoteResponse`**: The response from the `POST /quotes/calculate` endpoint.

## 9. Configuration & Environment

The application is configured using environment variables defined in the `.env` file and loaded by the services in the `docker-compose.yml` file. The key variables are:

-   `POSTGRES_USER`: The username for the PostgreSQL database.
-   `POSTGRES_PASSWORD`: The password for the PostgreSQL database.
-   `POSTGRES_DB`: The name of the PostgreSQL database.
-   `DATABASE_URL`: The connection string for the PostgreSQL database.
-   `API_BASE_URL`: The base URL for the API, used by the UI to connect to the backend.

## 10. Dependencies

-   **API Dependencies (`api/requirements.txt`)**: `fastapi`, `uvicorn`, `sqlalchemy`, `psycopg2-binary`, `python-dotenv`, `requests`, `pandas`, `scipy`, `pytest`
-   **UI Dependencies (`ui/requirements.txt`)**: `streamlit`, `requests`, `pandas`, `python-dotenv`
