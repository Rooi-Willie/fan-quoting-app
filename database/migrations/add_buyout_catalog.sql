-- Migration: Add buyout_catalog table
-- Apply to existing dev and GCP Cloud SQL deployments.
-- Safe to run multiple times (CREATE TABLE IF NOT EXISTS).

CREATE TABLE IF NOT EXISTS buyout_catalog (
    id SERIAL PRIMARY KEY,
    manufacturer VARCHAR(100) NOT NULL,
    category VARCHAR(200) NOT NULL,
    description VARCHAR(255) NOT NULL,
    voltage_v INTEGER,
    unit_price NUMERIC(12, 2),
    is_por BOOLEAN DEFAULT FALSE,
    currency VARCHAR(3) DEFAULT 'ZAR',
    is_active BOOLEAN DEFAULT TRUE
);

-- Insert ELIO Electro Tech CC - DOL Pulse Fan Starter Panel Mining Spec
-- 400V items
INSERT INTO buyout_catalog (manufacturer, category, description, voltage_v, unit_price, is_por, currency) VALUES
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '15-22 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 400, 57083.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '30 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 400, 58196.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '37 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 400, 58890.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '45 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 400, 64727.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '55 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 400, 66418.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '75 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 400, 65877.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '90 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 400, 65877.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '110 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 400, 75708.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '132 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 400, 78003.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '160 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 400, 94590.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '185 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 400, 94590.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '200 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 400, 94464.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '220 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 400, 105811.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '250 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 400, 107153.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '260 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 400, 120684.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '280 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 400, 123004.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '300 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 400, 123944.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '315 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 400, 125891.00, false, 'ZAR'),
-- 525V items
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '15-22 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 525, 55732.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '30 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 525, 56229.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '37 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 525, 57254.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '45 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 525, 58366.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '55 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 525, 58939.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '75 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 525, 60485.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '90 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 525, 60485.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '110 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 525, 59889.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '132 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 525, 65877.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '160 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 525, 75708.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '185 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 525, 85803.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '200 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 525, 85803.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '220 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 525, 94590.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '250 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 525, 94590.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '260 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 525, 94590.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '280 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 525, 101610.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '300 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 525, 107862.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '315 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 525, 109072.00, false, 'ZAR'),
-- 1000V items (priced)
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '15-22 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 1000, 73237.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '30 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 1000, 73237.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '37 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 1000, 73237.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '45 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 1000, 74410.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '55 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 1000, 74410.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '75 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 1000, 74410.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '90 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 1000, 72329.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '110 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 1000, 72329.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '132 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 1000, 76723.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '160 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 1000, 78574.00, false, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '185 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 1000, 84941.00, false, 'ZAR'),
-- 1000V P.O.R. items
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '200 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 1000, NULL, true, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '220 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 1000, NULL, true, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '250 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 1000, NULL, true, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '260 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 1000, NULL, true, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '280 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 1000, NULL, true, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '300 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 1000, NULL, true, 'ZAR'),
('ELIO - Electro Tech CC', 'DOL Pulse Fan Starter Panel Mining Spec', '315 KW DOL PULSE FAN STARTER PANEL MINING SPEC', 1000, NULL, true, 'ZAR')
ON CONFLICT DO NOTHING;
