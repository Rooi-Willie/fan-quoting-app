# This file defines Pydantic schemas that determine the shape of data for API
# requests and responses. They provide data validation, serialization, and
# documentation for the API endpoints.

from typing import List
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