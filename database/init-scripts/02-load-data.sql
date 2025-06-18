-- This script populates all tables from CSV files.

-- Load core data
COPY materials(name, description, cost_per_unit, min_cost_per_unit, max_cost_per_unit, cost_unit, currency) FROM '/csv_data/materials.csv' WITH (FORMAT csv, HEADER true);
COPY labor_rates(rate_name, rate_per_hour, currency) FROM '/csv_data/labour_rates.csv' WITH (FORMAT csv, HEADER true);

-- Motor data workflow
COPY motors_staging FROM '/csv_data/motors_master.csv' WITH (FORMAT csv, HEADER true);
INSERT INTO motors ( supplier_name, product_range, part_number, poles, rated_output, rated_output_unit, speed, speed_unit, frame_size, shaft_diameter, shaft_diameter_unit ) SELECT DISTINCT ON (supplier_name, product_range, poles, rated_output, speed, frame_size) supplier_name, product_range, part_number, poles, rated_output, 'kW', speed, 'RPM', frame_size, shaft_diameter, 'mm' FROM motors_staging;
INSERT INTO motor_prices ( motor_id, date_effective, foot_price, flange_price, currency ) SELECT m.id, s.date_effective, s.foot_price, s.flange_price, s.currency FROM motors_staging s JOIN motors m ON s.supplier_name = m.supplier_name AND s.product_range = m.product_range AND s.poles = m.poles AND s.rated_output = m.rated_output AND s.speed = m.speed AND (s.frame_size = m.frame_size OR (s.frame_size IS NULL AND m.frame_size IS NULL));
DROP TABLE motors_staging;

-- Load quoting logic data
COPY fan_configurations (
    uid,
    fan_size_mm,
    hub_size_mm,
    available_blade_qtys,
    stator_blade_qty,
    blade_name,
    blade_material,
    mass_per_blade_kg,
    available_motor_kw,
    motor_pole,
    available_components,
    auto_selected_components
) FROM '/csv_data/fan_configurations.csv' WITH (FORMAT csv, HEADER true);

COPY components(id, name, code, order_by) FROM '/csv_data/components.csv' WITH (FORMAT csv, HEADER true);
COPY global_settings FROM '/csv_data/global_settings.csv' WITH (FORMAT csv, HEADER true);

-- Added the new length_multiplier column to the explicit list
COPY component_parameters(
    component_id, 
    default_thickness_mm, 
    default_fabrication_waste_factor, 
    diameter_formula_type, 
    length_formula_type, 
    stiffening_formula_type, 
    mass_formula_type, 
    cost_formula_type,
    length_multiplier
) 
FROM '/csv_data/component_parameters.csv' WITH (FORMAT csv, HEADER true, NULL '');

COPY fan_component_parameters(fan_configuration_id, component_id, length_mm, stiffening_factor) FROM '/csv_data/fan_component_parameters.csv' WITH (FORMAT csv, HEADER true, NULL '');