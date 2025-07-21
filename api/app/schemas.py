# This file defines Pydantic schemas that determine the shape of data for API
# requests and responses. They provide data validation, serialization, and
# documentation for the API endpoints.
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class Component(BaseModel):
    """
    Schema for representing a component in API responses.

    This schema is used for reading component data and ensures that the
    response from endpoints like `/components/{component_id}` is correctly typed.
    """
    id: int  # The unique identifier for the component.
    name: str  # The human-readable name of the component.
    code: str  # A unique code for identifying the component.
    order_by: str | None = None  # A field to specify the sorting order for display purposes.

    # This tells Pydantic to read data from ORM model attributes.
    model_config = ConfigDict(from_attributes=True)


class MotorWithLatestPrice(BaseModel):
    """
    Schema for representing a motor with its most recent price information.
    This is a flattened structure, ideal for API responses.
    """
    id: int
    supplier_name: str
    product_range: str
    part_number: Optional[str] = None
    poles: int
    rated_output: float  # Pydantic handles conversion from Decimal
    speed: int
    frame_size: Optional[str] = None
    shaft_diameter: Optional[float] = None

    # Fields from the latest price record
    latest_price_date: Optional[date] = None
    foot_price: Optional[float] = None
    flange_price: Optional[float] = None
    currency: Optional[str] = None

    # Enable ORM mode to allow creating this schema from model instances
    model_config = ConfigDict(from_attributes=True)


class FanConfiguration(BaseModel):
    """
    Schema for representing a fan configuration in API responses.

    Used for reading fan configuration data from the database and returning it
    through the API.
    """
    id: int  # The unique identifier for the fan configuration.
    uid: str  # A unique string identifier for the fan configuration.
    fan_size_mm: int  # The diameter of the fan in millimeters.
    hub_size_mm: int  # The diameter of the fan hub in millimeters.
    available_blade_qtys: List[int]  # A list of possible blade quantities for this configuration.
    available_motor_kw: List[int]  # A list of available motor power ratings in kilowatts.
    available_components: List[int] | None = None  # A list of component IDs that can be used with this fan.
    auto_selected_components: List[int] | None = None  # A list of component IDs that are automatically selected.

    # This tells Pydantic to read data from ORM model attributes.
    model_config = ConfigDict(from_attributes=True)