# fan-quoting-app
Auxiliary axial fan quoting application.

## Overview
This repository contains a Streamlit UI and FastAPI backend for creating and managing axial fan quotations. Quote state is persisted as JSON (`quote_data`) alongside relational summary columns for efficient listing.

## Quote Data Schema
The application uses a modern, versioned schema (version = 3) for all quotes. Key characteristics:

### Schema Features
* **Logical Organization**: Structured into `meta`, `quote`, `specification`, `pricing`, `calculations`, and `context` sections
* **Separation of Concerns**: Clear distinction between technical specifications, pricing data, and computed results
* **Version Tracking**: `meta.version = 3` enables proper schema evolution

### Schema Sections
* **meta**: Version tracking, timestamps, and metadata
* **quote**: Basic quote identification and project information
* **specification**: Technical specifications (fan, components, motor, buyouts)
* **pricing**: All pricing data including overrides and final prices
* **calculations**: Server-computed results and aggregated totals
* **context**: Rates, settings, and audit information used in calculations

See full specification, examples, and API documentation:
* **Schema Documentation**: `../Documentation/quote_data_schema_v3.md`

## Architecture

### Frontend (Streamlit UI)
* **Multi-tab workflow**: Project info, fan configuration, motor selection, buyout items, review & save
* **Real-time calculations**: Component and pricing updates with immediate UI feedback
* **Session state management**: Schema-aware state handling with proper synchronization
* **Quote management**: Create, view, edit, and manage quote revisions

### Backend (FastAPI)
* **CRUD operations**: Complete quote lifecycle management
* **API endpoints**: Quote creation, schema validation, summary extraction
* **Summary extraction**: `_extract_summary_from_quote_data()` for database summary fields

### Database (PostgreSQL)
* **JSONB storage**: Efficient storage and querying of quote_data JSON
* **Summary columns**: Extracted fields for fast listing and filtering
* **Version tracking**: Schema version stored for proper handling
* **Revision management**: Complete quote history with immutable revisions

## Development Setup

### Prerequisites
* Python 3.8+
* PostgreSQL database
* Required Python packages (see requirements.txt)

### Running the Application
1. **Database**: Ensure PostgreSQL is running with schema initialized
2. **Backend**: Start FastAPI server (`uvicorn app.main:app --reload`)  
3. **Frontend**: Launch Streamlit UI (`streamlit run app.py`)
4. **Access**: Navigate to Streamlit URL (typically http://localhost:8501)

### Testing
* **Unit Tests**: Schema validation, calculations, and business logic
* **Integration Tests**: End-to-end quote workflow testing
* **Test Data**: Schema examples in `tests/test_data/`

## Recent Updates

### Core Features
* ✅ **Modern Schema**: Complete implementation with logical section organization
* ✅ **UI Updates**: All components updated for proper schema paths
* ✅ **Testing**: Comprehensive test coverage for functionality
* ✅ **Documentation**: Complete schema specification

### Technical Improvements  
* ✅ **Session State Sync**: Fixed widget lag issues with proper state synchronization
* ✅ **Component Calculations**: Real-time updates with cache clearing and state management
* ✅ **Data Paths**: Clean schema paths throughout application
* ✅ **Error Handling**: Improved validation and error reporting

### Implementation Status
* ✅ **Core Implementation**: Schema fully implemented and tested
* ✅ **UI Updates**: All pages and components support current schema
* ✅ **API Support**: Backend handles quote operations transparently  
* ✅ **Testing**: Test suite covers all functionality
* ✅ **Documentation**: Complete documentation for usage

## Future Enhancements

### Planned Features
* **Enhanced Audit Trail**: Extended context tracking and calculation history
* **Advanced Pricing Models**: Additional markup strategies and pricing rules
* **Workflow Management**: Status tracking and approval workflows  
* **Performance Optimization**: Caching improvements and calculation efficiency
* **Export Features**: PDF generation and data export capabilities

## License
Internal use (license details TBD).
