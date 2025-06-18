-- This script creates all tables.

-- Drop existing tables in reverse order of dependency to avoid errors
DROP TABLE IF EXISTS fan_component_parameters;
DROP TABLE IF EXISTS component_parameters;
DROP TABLE IF EXISTS global_settings;
DROP TABLE IF EXISTS components;
DROP TABLE IF EXISTS fan_configurations;
DROP TABLE IF EXISTS motor_prices;
DROP TABLE IF EXISTS motors_staging;
DROP TABLE IF EXISTS motors;
DROP TABLE IF EXISTS labor_rates;
DROP TABLE IF EXISTS materials;


-- ================================= CORE DATA TABLES ==============================

CREATE TABLE materials ( 
    id SERIAL PRIMARY KEY, 
    name VARCHAR(255) NOT NULL, 
    description TEXT, 
    cost_per_unit NUMERIC(12, 2) NOT NULL, 
    min_cost_per_unit NUMERIC(12, 2), 
    max_cost_per_unit NUMERIC(12, 2), 
    cost_unit VARCHAR(10), 
    currency VARCHAR(3) DEFAULT 'ZAR' 
);
CREATE TABLE labor_rates ( 
    id SERIAL PRIMARY KEY, 
    rate_name VARCHAR(100) NOT NULL UNIQUE, 
    rate_per_hour NUMERIC(10, 2) NOT NULL, 
    currency VARCHAR(3) DEFAULT 'ZAR' 
);
CREATE TABLE motors ( 
    id SERIAL PRIMARY KEY, 
    supplier_name VARCHAR(100) NOT NULL, 
    product_range VARCHAR(100) NOT NULL, 
    part_number VARCHAR(50), 
    poles SMALLINT NOT NULL, 
    rated_output NUMERIC(7, 2) NOT NULL, 
    rated_output_unit VARCHAR(10), 
    speed INTEGER NOT NULL, 
    speed_unit VARCHAR(10), 
    frame_size VARCHAR(20), 
    shaft_diameter NUMERIC(5, 1), 
    shaft_diameter_unit VARCHAR(10), 
    UNIQUE(supplier_name, product_range, poles, rated_output, speed, frame_size) 
);
CREATE TABLE motor_prices ( 
    id SERIAL PRIMARY KEY, 
    motor_id INTEGER NOT NULL REFERENCES motors(id) ON DELETE CASCADE, 
    date_effective DATE NOT NULL, 
    foot_price NUMERIC(12, 2), 
    flange_price NUMERIC(12, 2), 
    currency VARCHAR(3) DEFAULT 'ZAR', 
    UNIQUE(motor_id, date_effective) 
);
CREATE TABLE motors_staging ( 
    supplier_name VARCHAR(100), 
    product_range VARCHAR(100), 
    part_number VARCHAR(50), 
    poles SMALLINT, 
    rated_output NUMERIC(7, 2), 
    speed INTEGER, 
    frame_size VARCHAR(20), 
    shaft_diameter NUMERIC(5, 1), 
    foot_price NUMERIC(12, 2), 
    flange_price NUMERIC(12, 2), 
    currency VARCHAR(3), 
    date_effective DATE 
);

-- ======================= QUOTING LOGIC TABLES =============================

CREATE TABLE fan_configurations (
    id SERIAL PRIMARY KEY,
    uid VARCHAR(50) UNIQUE NOT NULL,
    fan_size_mm INT NOT NULL,
    hub_size_mm INT NOT NULL,
    available_blade_qtys INT[] NOT NULL,
    stator_blade_qty INT NOT NULL,
    blade_name VARCHAR(50),
    blade_material VARCHAR(50),
    mass_per_blade_kg NUMERIC(10, 2) NOT NULL,
    available_motor_kw INT[] NOT NULL,
    motor_pole INT NOT NULL,
    available_components INT[],
    auto_selected_components INT[]
);

CREATE TABLE components (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    order_by VARCHAR(10)
);

CREATE TABLE component_parameters (
    id SERIAL PRIMARY KEY,
    component_id INT UNIQUE NOT NULL REFERENCES components(id),
    default_thickness_mm NUMERIC(10, 2),
    default_fabrication_waste_factor NUMERIC(10, 4),
    diameter_formula_type VARCHAR(50),
    length_formula_type VARCHAR(50),
    stiffening_formula_type VARCHAR(50),
    mass_formula_type VARCHAR(50) NOT NULL,
    cost_formula_type VARCHAR(50) NOT NULL
);

CREATE TABLE fan_component_parameters (
    id SERIAL PRIMARY KEY,
    fan_configuration_id INT NOT NULL REFERENCES fan_configurations(id),
    component_id INT NOT NULL REFERENCES components(id),
    length_mm NUMERIC(10, 2),
    stiffening_factor NUMERIC(10, 4),
    UNIQUE(fan_configuration_id, component_id)
);

CREATE TABLE global_settings (
    setting_name VARCHAR(50) PRIMARY KEY,
    setting_value VARCHAR(255) NOT NULL
);