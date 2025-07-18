# This file contains SQLAlchemy ORM models, which are Python classes that map
# directly to your database tables. Each class represents a table, and instances
# of that class represent rows in that table.

from sqlalchemy import ARRAY, Column, Integer, Numeric, String
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