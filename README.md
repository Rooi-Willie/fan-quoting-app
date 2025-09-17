# fan-quoting-app
Auxiliary axial fan quoting application.

## Overview
This repository contains a Streamlit UI and FastAPI backend for creating and managing axial fan quotations. Quote state is persisted as JSON (`quote_data`) alongside relational summary columns for efficient listing.

## Quote Data Schema (v3)
The application uses a modern, versioned schema (version = 3) for all new quotes with full backward compatibility for legacy quotes. Key characteristics:

### v3 Schema Features
* **Logical Organization**: Structured into `meta`, `quote`, `specification`, `pricing`, `calculations`, and `context` sections
* **Separation of Concerns**: Clear distinction between technical specifications, pricing data, and computed results
* **Version Tracking**: `meta.version = 3` enables proper schema evolution and migration support
* **Backward Compatibility**: Legacy v2 quotes continue to work through compatibility layer

### Schema Sections
* **meta**: Version tracking, timestamps, and metadata
* **quote**: Basic quote identification and project information
* **specification**: Technical specifications (fan, components, motor, buyouts)
* **pricing**: All pricing data including overrides and final prices
* **calculations**: Server-computed results and aggregated totals
* **context**: Rates, settings, and audit information used in calculations

### Migration & Compatibility
* **Automatic Detection**: System detects schema version and handles appropriately
* **Compatibility Functions**: `ensure_v3_compatibility()` converts v2 data for display
* **Graceful Transition**: No forced migration - v2 quotes work seamlessly
* **New Quotes**: All new quotes created with v3 schema structure

See full specification, examples, migration details, and API documentation:
* **v3 Schema**: `../Documentation/quote_data_schema_v3.md`
* **Legacy v2**: `../Documentation/quote_data_schema_v2.md` (maintained for reference)

## Architecture

### Frontend (Streamlit UI)
* **Multi-tab workflow**: Project info, fan configuration, motor selection, buyout items, review & save
* **Real-time calculations**: Component and pricing updates with immediate UI feedback
* **Session state management**: v3 schema-aware state handling with proper synchronization
* **Quote management**: Create, view, edit, and manage quote revisions

### Backend (FastAPI)
* **CRUD operations**: Complete quote lifecycle management
* **v3 API endpoints**: `create_v3_quote()`, schema validation, summary extraction
* **Dual schema support**: Handles both v2 and v3 quotes transparently
* **Summary extraction**: `_extract_summary_from_v3_quote_data()` for database summary fields

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
* **Unit Tests**: v3 schema validation, compatibility functions, calculations
* **Integration Tests**: End-to-end quote workflow testing
* **Regression Tests**: v2 compatibility and migration testing
* **Test Data**: v3 schema examples in `tests/test_data/`

## Recent Updates (v3 Implementation)

### Core Features
* ✅ **v3 Schema**: Complete implementation with logical section organization
* ✅ **Backward Compatibility**: Seamless handling of legacy v2 quotes
* ✅ **UI Updates**: All components updated for v3 schema paths
* ✅ **Testing**: Comprehensive test coverage for v3 functionality
* ✅ **Documentation**: Complete v3 schema specification and migration guide

### Technical Improvements  
* ✅ **Session State Sync**: Fixed widget lag issues with proper state synchronization
* ✅ **Component Calculations**: Real-time updates with cache clearing and state management
* ✅ **Data Paths**: Clean v3 schema paths throughout application
* ✅ **Error Handling**: Improved validation and error reporting

### Migration Status
* ✅ **Core Implementation**: v3 schema fully implemented and tested
* ✅ **UI Compatibility**: All pages and components support v3
* ✅ **API Support**: Backend handles both v2 and v3 transparently  
* ✅ **Testing**: Test suite covers both schema versions
* ✅ **Documentation**: Complete documentation for v3 usage

## Future Enhancements

### Planned Features
* **Enhanced Audit Trail**: Extended context tracking and calculation history
* **Advanced Pricing Models**: Additional markup strategies and pricing rules
* **Workflow Management**: Status tracking and approval workflows  
* **Performance Optimization**: Caching improvements and calculation efficiency
* **Export Features**: PDF generation and data export capabilities

### Schema Evolution
* **Version 4 Planning**: Future structural enhancements and new domains
* **Incremental Updates**: Minor enhancements within v3 framework
* **Migration Tools**: Automated migration utilities for future versions

## License
Internal use (license details TBD).
