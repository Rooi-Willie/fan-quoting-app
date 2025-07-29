# This file contains SQLAlchemy ORM models, which are Python classes that map
# directly to your database tables. Each class represents a table, and instances
# of that class represent rows in that table.
import enum
from sqlalchemy import (ARRAY, Column, Date, ForeignKey, Integer, Numeric,
                        SmallInteger, String, Enum as SQLAlchemyEnum)
from sqlalchemy.orm import relationship
from .database import Base


class FanConfiguration(Base):
    """
    Represents a specific configuration of a fan.

    Each record defines a unique fan setup with its physical and performance
    characteristics, mapping to the 'fan_configurations' table in the database.
    """
    __tablename__ = "fan_configurations"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, unique=True, index=True, comment="A unique identifier for the fan configuration.")
    fan_size_mm = Column(Integer, nullable=False, comment="The diameter of the fan in millimeters.")
    hub_size_mm = Column(Integer, nullable=False, comment="The diameter of the fan hub in millimeters.")
    available_blade_qtys = Column(ARRAY(Integer), nullable=False, comment="A list of possible blade quantities for this fan configuration.")
    stator_blade_qty = Column(Integer, nullable=False, comment="The number of stator blades.")
    blade_name = Column(String, comment="The name or model of the blade.")
    blade_material = Column(String, comment="The material the blades are made of (e.g., 'Aluminum', 'Steel').")
    mass_per_blade_kg = Column(Numeric, nullable=False, comment="The mass of a single blade in kilograms.")
    available_motor_kw = Column(ARRAY(Integer), nullable=False, comment="A list of available motor power ratings in kilowatts.")
    motor_pole = Column(Integer, nullable=False, comment="The number of poles in the motor (e.g., 2, 4, 6).")
    available_components = Column(ARRAY(Integer), comment="A list of foreign key IDs to the 'components' table for parts that can be used with this fan.")
    auto_selected_components = Column(ARRAY(Integer), comment="A list of component IDs that are automatically selected for this configuration.")

    # Relationship for fan-specific component parameter overrides
    fan_specific_parameters = relationship("FanComponentParameter", back_populates="fan_configuration", cascade="all, delete-orphan")


class Component(Base):
    """
    Represents a single component that can be part of a fan assembly.

    This model maps to the 'components' table in the database.
    """
    __tablename__ = "components"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, comment="The human-readable name of the component (e.g., 'Inlet Cone').")
    code = Column(String, unique=True, nullable=False, comment="A unique code for identifying the component.")
    order_by = Column(String, comment="A field to specify the sorting order for display purposes in the UI.")

    # Relationship to its default parameters (one-to-one)
    parameters = relationship("ComponentParameter", uselist=False, back_populates="component", cascade="all, delete-orphan")
    fan_specific_parameters = relationship("FanComponentParameter", back_populates="component")


class Motor(Base):
    """
    Represents a motor's core specifications, mapping to the 'motors' table.
    """
    __tablename__ = "motors"

    id = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String(100), nullable=False)
    product_range = Column(String(100), nullable=False)
    part_number = Column(String(50))
    poles = Column(SmallInteger, nullable=False)
    rated_output = Column(Numeric(7, 2), nullable=False)
    rated_output_unit = Column(String(10))
    speed = Column(Integer, nullable=False)
    speed_unit = Column(String(10))
    frame_size = Column(String(20))
    shaft_diameter = Column(Numeric(5, 1))
    shaft_diameter_unit = Column(String(10))

    # Relationship to link a motor to its various prices over time
    prices = relationship("MotorPrice", back_populates="motor", cascade="all, delete-orphan")


class MotorPrice(Base):
    """
    Represents a price record for a motor at a specific point in time.
    Maps to the 'motor_prices' table.
    """
    __tablename__ = "motor_prices"

    id = Column(Integer, primary_key=True, index=True)
    motor_id = Column(Integer, ForeignKey("motors.id"), nullable=False)
    date_effective = Column(Date, nullable=False)
    foot_price = Column(Numeric(12, 2))
    flange_price = Column(Numeric(12, 2))
    currency = Column(String(3), default="ZAR")

    motor = relationship("Motor", back_populates="prices")


# --- Models for Calculation Engine ---

class GlobalSetting(Base):
    """
    Stores global key-value settings for the application, such as default
    markup, steel density, etc.
    """
    __tablename__ = "global_settings"
    id = Column(Integer, primary_key=True, index=True)
    setting_name = Column(String, unique=True, nullable=False, index=True, comment="The unique key for the setting (e.g., 'default_markup').")
    setting_value = Column(String, nullable=False, comment="The value of the setting, stored as a string.")
    value_type = Column(String(20), nullable=False, comment="The data type for casting (e.g., 'float', 'int', 'str').")
    description = Column(String, comment="A description of what the setting is for.")


class Material(Base):
    """
    Stores cost rates for various materials used in manufacturing.
    """
    __tablename__ = "materials"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True, comment="The name of the material (e.g., 'Steel S355JR').")
    cost_per_unit = Column(Numeric(10, 4), nullable=False, comment="The cost for one unit of this material.")
    unit = Column(String(10), nullable=False, comment="The unit of measurement (e.g., 'kg', 'l', 'item').")


class LabourRate(Base):
    """
    Stores cost rates for different types of labour.
    """
    __tablename__ = "labour_rates"
    id = Column(Integer, primary_key=True, index=True)
    rate_name = Column(String, unique=True, nullable=False, index=True, comment="The name of the labour rate (e.g., 'Default Labour Per Kg').")
    rate_per_unit = Column(Numeric(10, 4), nullable=False, comment="The cost for one unit of this labour type.")
    unit = Column(String(20), nullable=False, comment="The unit of measurement (e.g., 'per_kg', 'per_hour').")


# --- Enums for Formula Types ---
# These provide controlled vocabularies for the formula types in the database.

class MassFormulaType(str, enum.Enum):
    CYLINDER_SURFACE = "CYLINDER_SURFACE"
    SCD_MASS = "SCD_MASS"
    ROTOR_EMPIRICAL = "ROTOR_EMPIRICAL"
    CONE_SURFACE = "CONE_SURFACE"

class DiameterFormulaType(str, enum.Enum):
    HUB_DIAMETER = "HUB_DIAMETER"
    HUB_DIAMETER_X_1_35 = "HUB_DIAMETER_X_1_35"
    HUB_DIAMETER_X_1_25 = "HUB_DIAMETER_X_1_25"
    CONICAL_60_DEG = "CONICAL_60_DEG"
    HUB_PLUS_CONSTANT = "HUB_PLUS_CONSTANT"

class LengthFormulaType(str, enum.Enum):
    FIXED = "FIXED"
    CONICAL_15_DEG = "CONICAL_15_DEG"
    CONICAL_3_5_DEG = "CONICAL_3_5_DEG"
    LENGTH_D_X_MULTIPLIER = "LENGTH_D_X_MULTIPLIER"

class StiffeningFormulaType(str, enum.Enum):
    FIXED = "FIXED"
    LINEAR_HUB_SCALING_A = "LINEAR_HUB_SCALING_A"


class ComponentParameter(Base):
    """
    Stores the default calculation parameters for a specific component.
    This table has a one-to-one relationship with the 'components' table.
    """
    __tablename__ = "component_parameters"
    id = Column(Integer, primary_key=True, index=True)
    component_id = Column(Integer, ForeignKey("components.id"), unique=True, nullable=False)

    mass_formula_type = Column(SQLAlchemyEnum(MassFormulaType), nullable=False)
    diameter_formula_type = Column(SQLAlchemyEnum(DiameterFormulaType), nullable=True)
    length_formula_type = Column(SQLAlchemyEnum(LengthFormulaType), nullable=True)
    stiffening_formula_type = Column(SQLAlchemyEnum(StiffeningFormulaType), nullable=True)

    default_thickness_mm = Column(Numeric(6, 2), nullable=False)
    default_fabrication_waste_factor = Column(Numeric(5, 3), nullable=False)
    length_multiplier = Column(Numeric(8, 4), nullable=True)

    component = relationship("Component", back_populates="parameters")


class FanComponentParameter(Base):
    """
    Stores fan-specific overrides for component parameters. This acts as a
    join table between fan_configurations and components for parameter overrides.
    """
    __tablename__ = "fan_component_parameters"
    id = Column(Integer, primary_key=True, index=True)
    fan_config_id = Column(Integer, ForeignKey("fan_configurations.id"), nullable=False, index=True)
    component_id = Column(Integer, ForeignKey("components.id"), nullable=False, index=True)

    # Overrideable values (nullable because they are optional)
    length_mm = Column(Numeric(10, 2), nullable=True)
    stiffening_factor = Column(Numeric(8, 4), nullable=True)

    fan_configuration = relationship("FanConfiguration", back_populates="fan_specific_parameters")
    component = relationship("Component", back_populates="fan_specific_parameters")