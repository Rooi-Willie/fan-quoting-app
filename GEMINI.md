# Gemini Project Helper

This document provides context for the Gemini AI assistant to understand the project and provide more effective assistance.

## Project Overview

The Fan Quoting App is a web-based application designed to streamline the process of generating quotes for industrial axial fans. It replaces a legacy Excel-based system, providing a more user-friendly and efficient workflow. The application calculates the cost of a fan based on a selected configuration and a set of components, taking into account material costs, labor rates, and other variables.

## Key Features

- **Fan Configuration:** Users can select a fan configuration based on fan size and hub size.
- **Component Selection:** Users can select which components to include in the quote (e.g., screen inlet, inlet cone, diffuser).
- **Motor Selection:** Users can select a motor from a list of available options, with pricing information stored in the database.
- **Quote Generation:** The application calculates the total cost of the fan and generates a quote.
- **Database-driven:** All data, including fan configurations, components, materials, labor rates, and motor prices, is stored in a PostgreSQL database.

## Technical Stack

- **Backend:** Python with FastAPI
- **Frontend:** Python with Streamlit
- **Database:** PostgreSQL

## Development Workflow

- **Run the application:** `docker-compose up`
- **Run tests:** `pytest`

## Project Structure

```
.
├───api/
│   ├───app/
│   │   ├───logic/
│   │   │   └───calculation_engine.py   # Core calculation logic
│   │   ├───routers/                    # API endpoints
│   │   └───models.py                     # Database models
│   └───tests/                          # Backend tests
├───database/
│   ├───data/                           # CSV files with initial data
│   └───init-scripts/                   # Database initialization scripts
└───ui/
    ├───app.py                          # Main UI application
    └───pages/                          # UI pages for different sections
```

## Database Schema

The database schema is defined in `api/app/models.py` and the initial data is located in the `database/data` directory as CSV files. The main tables are:

- `fan_configurations`: Stores the different fan configurations.
- `components`: Stores the available fan components.
- `motors_master`: Stores the available motors and their specifications.
- `materials`: Stores the cost of different materials.
- `labour_rates`: Stores the cost of different types of labor.
- `global_settings`: Stores global settings for the application.
- `component_parameters`: Stores the default calculation parameters for each component.
- `fan_component_parameters`: Stores fan-specific overrides for component parameters.

## API Endpoints

The API endpoints are defined in the `api/app/routers/` directory. The main endpoints are:

- `/fans`: For managing fan configurations and components.
- `/motors`: For managing motors.
- `/quotes`: For generating quotes.
