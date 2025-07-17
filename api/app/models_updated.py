# This file will contain Python classes that map directly to your database tables.

from sqlalchemy import Column, Integer, String, Numeric, INT, Text, ARRAY
from .database import Base

class FanConfiguration(Base):
    __tablename__ = "fan_configurations"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, unique=True, index=True)
    fan_size_mm = Column(Integer, nullable=False)
    hub_size_mm = Column(Integer, nullable=False)
    available_blade_qtys = Column(ARRAY(Integer), nullable=False)
    stator_blade_qty = Column(Integer, nullable=False)
    blade_name = Column(String)
    blade_material = Column(String)
    mass_per_blade_kg = Column(Numeric, nullable=False)
    available_motor_kw = Column(ARRAY(Integer), nullable=False)
    motor_pole = Column(Integer, nullable=False)
    available_components = Column(ARRAY(Integer))
    auto_selected_components = Column(ARRAY(Integer))

class Component(Base):
    __tablename__ = "components"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    code = Column(String, unique=True, nullable=False)
    order_by = Column(String)