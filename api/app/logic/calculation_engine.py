import math
from sqlalchemy.orm import Session
from .. import crud, schemas, models

"""
1.) A BaseCalculator Class: A simple parent class to hold any shared helper methods.
2.) Specific Calculator Classes: A separate class for each unique mass_formula_type from your database 
    (e.g., CylinderSurfaceCalculator, RotorEmpiricalCalculator). Each class will know how to perform 
    one specific set of calculations.
3.) A get_calculator() Factory Function: A simple dispatcher that takes a mass_formula_type 
    string and returns an instance of the correct calculator class.
4.) An Orchestrator Function calculate_full_quote(): The main public function that the API 
    endpoint will call. It fetches all the data, loops through the requested components, uses 
    the factory to get the right calculator for each, and aggregates the results."""

# ==============================================================================
# PART 0: THE "PRE-CALCULATION" HELPER FUNCTION
# ==============================================================================

def _resolve_formulaic_parameters(hub_size: float, fan_size: float, params: dict) -> dict:
    """
    Takes raw parameters and resolves any formula-based values into concrete numbers.
    This function modifies the 'params' dictionary in place.
    """
    # --- Resolve Diameter ---
    # The 'start_diameter_mm' is a new key we add for clarity in cone calculations.
    # The 'diameter_mm' is the primary diameter used for cylindrical calculations.
    if params.get('diameter_formula_type') == 'HUB_DIAMETER_X_1_35':
        params['diameter_mm'] = hub_size * 1.35
        params['start_diameter_mm'] = hub_size # For cones, start is hub
        params['end_diameter_mm'] = hub_size * 1.35
    elif params.get('diameter_formula_type') == 'HUB_DIAMETER_X_1_25':
        params['diameter_mm'] = hub_size * 1.25 # This is the larger diameter of the cone
        params['start_diameter_mm'] = hub_size
        params['end_diameter_mm'] = hub_size * 1.25
    elif params.get('diameter_formula_type') == 'CONICAL_60_DEG':
        # Excel: =2*(TAN((60/2)*PI()/180)*0.25*$B$2)+$B$2
        # This is the larger diameter of the inlet cone.
        # radial_expansion = math.tan(math.radians(30)) * (0.25 * hub_size)
        # params['end_diameter_mm'] = hub_size + 2 * radial_expansion
        # The Excel formula seems complex. Let's use a simpler interpretation from the other spreadsheets.
        # For the Ø762 fan, the conical inlet goes from 762 to 982. Let's model that relationship.
        # It's usually based on the length, which is also calculated.
        # This indicates a dependency we need to resolve first.
        params['start_diameter_mm'] = hub_size
        params['end_diameter_mm'] = hub_size * 1.288 # Approximated ratio from Ø762 data (982/762)
        params['diameter_mm'] = (params['start_diameter_mm'] + params['end_diameter_mm']) / 2
    elif params.get('diameter_formula_type') == 'HUB_PLUS_CONSTANT': # For Silencers
        params['diameter_mm'] = fan_size + 75 * 2 # Silencer OD is fan size + 75mm wall * 2
    else: # Default is HUB_DIAMETER
        params['diameter_mm'] = hub_size
        params['start_diameter_mm'] = hub_size
        params['end_diameter_mm'] = hub_size

    # --- Resolve Length (if it's a formula) ---
    # Note: 'length_mm' can be NULL from the db if it's formulaic
    if params.get('length_mm') is None:
        if params.get('length_formula_type') == 'CONICAL_15_DEG':
            # Excel: =(0.16*$B$2/2)/(TAN(15*PI()/180))
            params['length_mm'] = (0.08 * hub_size) / math.tan(math.radians(15))
        elif params.get('length_formula_type') == 'CONICAL_3_5_DEG':
            # Excel: =(0.25*$B$2/2)/(TAN(3.5*PI()/180))
            params['length_mm'] = (0.125 * hub_size) / math.tan(math.radians(3.5))
        elif params.get('length_formula_type') == 'LENGTH_D_X_MULTIPLIER':
            # The length is the Fan Size (not hub) times a multiplier
            params['length_mm'] = fan_size * params['length_multiplier']

    # --- Resolve Stiffening Factor (if it's a formula) ---
    if params.get('stiffening_factor') is None:
        if params.get('stiffening_formula_type') == 'LINEAR_HUB_SCALING_A':
            # Excel: =(0.115*$B$2-124)/100
            params['stiffening_factor'] = (0.115 * hub_size - 124) / 100
    
    return params

# ==============================================================================
# PART 1: THE CALCULATOR CLASSES
# ==============================================================================

class BaseCalculator:
    """A base class for common helper methods."""
    def get_value(self, default, override):
        """Helper to use an override if provided, otherwise use the default."""
        return override if override is not None else default

class CylinderSurfaceCalculator(BaseCalculator):
    def calculate(self, request_params: dict, component_params: dict, rates_settings: dict) -> dict:
        """
        Calculates properties for a simple cylindrical component.
        """
        # --- 1. Gather Inputs ---
        # hub_size = request_params['hub_size_mm']
        steel_density = rates_settings['steel_density_kg_m3']
        thickness = self.get_value(component_params['default_thickness_mm'], request_params['overrides'].get('thickness_mm_override'))
        waste_factor = self.get_value(component_params['default_fabrication_waste_factor'], request_params['overrides'].get('fabrication_waste_factor_override'))
        
        # Get fixed or formula-driven values
        length = component_params['length_mm']
        stiffening_factor = component_params['stiffening_factor']
        diameter = component_params['diameter_mm']
        
        # --- 2. Perform Calculations (from Excel) ---
        # Diameter: (e.g., for Screen Inlet Inside) Excel: = $B$2
        # diameter = hub_size
        
        # Ideal Mass: Excel: = PI() * Diameter * Thickness * Length * SteelDensity / 10^9
        ideal_mass = (math.pi * diameter * length * thickness * steel_density) / 1e9
        
        # Real Mass: Excel: = IdealMass * (1 + StiffeningFactor)
        real_mass = ideal_mass * (1 + stiffening_factor)
        
        # Feedstock & Cost
        feedstock_mass = real_mass * (1 + waste_factor)
        material_cost = feedstock_mass * rates_settings['steel_s355jr_cost_per_kg']
        labour_cost = real_mass * rates_settings['labour_per_kg']
        total_cost_before_markup = material_cost + labour_cost

        return {
            "name": component_params['name'],
            "material_thickness_mm": thickness,
            "fabrication_waste_percentage": waste_factor * 100,
            "overall_diameter_mm": diameter,
            "total_length_mm": length,
            "ideal_mass_kg": ideal_mass,
            "real_mass_kg": real_mass,
            "feedstock_mass_kg": feedstock_mass,
            "material_cost": material_cost,
            "labour_cost": labour_cost,
            "total_cost_before_markup": total_cost_before_markup,
            "stiffening_factor": stiffening_factor,
        }

class ScdMassCalculator(BaseCalculator):
    def calculate(self, request_params: dict, component_params: dict, rates_settings: dict) -> dict:
        """
        Calculates properties for the Self Closing Door, which has a unique mass formula.
        """
        # --- 1. Gather Inputs ---
        hub_size = request_params['hub_size_mm']
        steel_density = rates_settings['steel_density_kg_m3']
        thickness = self.get_value(component_params['default_thickness_mm'], request_params['overrides'].get('thickness_mm_override'))
        waste_factor = self.get_value(component_params['default_fabrication_waste_factor'], request_params['overrides'].get('fabrication_waste_factor_override'))
        length = component_params['length_mm']
        stiffening_factor = component_params['stiffening_factor']
        
        # --- 2. Perform Calculations (from Excel) ---
        diameter = hub_size
        
        # Ideal Mass: Excel: =(PI()*$B$2*J11*J10 + ((PI()/4)*$B$2^2)*$J$11) * $B$4/10^9
        # This is the surface area of the cylinder PLUS the area of one end plate, all times thickness.
        cylinder_area = math.pi * diameter * length
        end_plate_area = (math.pi / 4) * (diameter ** 2)
        ideal_mass = ((cylinder_area + end_plate_area) * thickness * steel_density) / 1e9
        real_mass = ideal_mass * (1 + stiffening_factor)
        feedstock_mass = real_mass * (1 + waste_factor)
        material_cost = feedstock_mass * rates_settings['steel_s355jr_cost_per_kg']
        labour_cost = real_mass * rates_settings['labour_per_kg']
        total_cost_before_markup = material_cost + labour_cost

        return {
            "name": component_params['name'],
            "material_thickness_mm": thickness,
            "fabrication_waste_percentage": waste_factor * 100,
            "overall_diameter_mm": diameter,
            "total_length_mm": length,
            "ideal_mass_kg": ideal_mass,
            "real_mass_kg": real_mass,
            "feedstock_mass_kg": feedstock_mass,
            "material_cost": material_cost,
            "labour_cost": labour_cost,
            "total_cost_before_markup": total_cost_before_markup,
            "stiffening_factor": stiffening_factor,
        }

class RotorEmpiricalCalculator(BaseCalculator):
    def calculate(self, request_params: dict, component_params: dict, rates_settings: dict) -> dict:
        """
        Calculates properties for the Rotor using its unique empirical formulas.
        This calculator needs extra parameters from the fan configuration.
        """
        # --- 1. Gather Inputs ---
        hub_size = request_params['hub_size_mm']
        blade_qty = request_params['blade_quantity']
        mass_per_blade = request_params['mass_per_blade_kg']
        
        # --- 2. Perform Calculations (from Excel) ---
        # Real Mass: =(19.5)*($B$2/665)^2*2+8.6+2+$B$4*$C$4+5*($B$2/665)^2
        hub_scaling_factor = (hub_size / 665) ** 2
        real_mass = (19.5 * hub_scaling_factor * 2) + 8.6 + 2 + (blade_qty * mass_per_blade) + (5 * hub_scaling_factor)
        
        # Cost: =(19.5)*($B$2/665)^2*Rates!B16*2+4*Rates!B14+Rates!B20+$B$4*$C$4*Rates!$B$18+(4226)*($B$2/665)^2
        # This requires specific material rates. We'll need a good way to fetch these by name.
        cost_part1 = (19.5 * hub_scaling_factor * 2) * rates_settings['en8_machine_cost_per_kg']  # Assumes EN8 is Rates!B16
        cost_part2 = 4 * rates_settings['taperlock_bush_cost_per_item']  # Assumes Taperlock is Rates!B14
        cost_part3 = rates_settings['scd_items_cost_per_item'] # Placeholder for Rates!B20
        cost_part4 = (blade_qty * mass_per_blade) * rates_settings['ali_blades_cost_per_kg'] # Assumes Ali is Rates!B18
        cost_part5 = 4226 * hub_scaling_factor
        material_cost = cost_part1 + cost_part2 + cost_part3 + cost_part4 + cost_part5
        labour_cost = real_mass * rates_settings['labour_per_kg']
        total_cost_before_markup = material_cost + labour_cost

        # Rotor is empirical, so some values are not applicable or are implicitly included.
        return {
            "name": component_params['name'],
            "material_thickness_mm": 0, # N/A for this component
            "fabrication_waste_percentage": 0, # N/A
            "overall_diameter_mm": hub_size, # Use hub size as representative diameter
            "total_length_mm": None, # N/A
            "ideal_mass_kg": real_mass, # For empirical, ideal and real are the same
            "real_mass_kg": real_mass,
            "feedstock_mass_kg": real_mass, # N/A
            "material_cost": material_cost,
            "labour_cost": labour_cost,
            "total_cost_before_markup": total_cost_before_markup,
            "stiffening_factor": None, # N/A
        }

class ConeSurfaceCalculator(BaseCalculator):
    def calculate(self, request_params: dict, component_params: dict, rates_settings: dict) -> dict:
        """
        Calculates properties for a conical component (like a diffuser or inlet cone).
        It expects the final diameters and length to be pre-calculated.

        The ConeSurfaceCalculator expects that the final start_diameter_mm, end_diameter_mm, and length_mm 
        have already been figured out. The job of translating the diameter_formula_type and length_formula_type
        from the database happens before the calculator is called.

        This logic will live inside our main orchestrator function, calculate_full_quote. 
        It will be responsible for looking at the component_params and resolving any formula-based 
        values into concrete numbers.
        """
        # --- 1. Gather Inputs ---
        steel_density = rates_settings['steel_density_kg_m3']
        thickness = self.get_value(component_params['default_thickness_mm'], request_params['overrides'].get('thickness_mm_override'))
        waste_factor = self.get_value(component_params['default_fabrication_waste_factor'], request_params['overrides'].get('fabrication_waste_factor_override'))
        
        # Get pre-calculated geometric values and fixed parameters
        start_diameter = component_params['start_diameter_mm']
        end_diameter = component_params['end_diameter_mm']
        length = component_params['length_mm']
        stiffening_factor = component_params['stiffening_factor']
        
        # --- 2. Perform Calculations (from Excel) ---
        
        # Ideal Mass: Based on the "average diameter" method
        # Excel: =((($B$2+(1+0.16)*$B$2)/2)*PI())*D11*$B$4*D10/10^9
        average_diameter = (start_diameter + end_diameter) / 2
        ideal_mass = (math.pi * average_diameter * length * thickness * steel_density) / 1e9
        
        # Real Mass: Excel: = IdealMass * (1 + StiffeningFactor)
        real_mass = ideal_mass * (1 + stiffening_factor)
        
        # Feedstock & Cost
        feedstock_mass = real_mass * (1 + waste_factor)
        material_cost = feedstock_mass * rates_settings['steel_s355jr_cost_per_kg']
        labour_cost = real_mass * rates_settings['labour_per_kg']
        total_cost_before_markup = material_cost + labour_cost

        return {
            "name": component_params['name'],
            "material_thickness_mm": thickness,
            "fabrication_waste_percentage": waste_factor * 100,
            "overall_diameter_mm": end_diameter, # Use the larger diameter as the overall
            "total_length_mm": length,
            "ideal_mass_kg": ideal_mass,
            "real_mass_kg": real_mass,
            "feedstock_mass_kg": feedstock_mass,
            "material_cost": material_cost,
            "labour_cost": labour_cost,
            "total_cost_before_markup": total_cost_before_markup,
            "stiffening_factor": stiffening_factor,
        }
    
# ... Add other additional classes for other surfaces if neccesary, etc., following the same pattern ...

# ==============================================================================
# PART 3: THE FACTORY FUNCTION
# ==============================================================================

def get_calculator(mass_formula_type: str) -> BaseCalculator:
    """
    Factory function that returns an instance of the correct calculator class
    based on the mass_formula_type string from the database.
    """
    calculators = {
        "CYLINDER_SURFACE": CylinderSurfaceCalculator(),
        "SCD_MASS": ScdMassCalculator(),
        "ROTOR_EMPIRICAL": RotorEmpiricalCalculator(),
        "CONE_SURFACE": ConeSurfaceCalculator(),
    }
    calculator = calculators.get(mass_formula_type)
    if not calculator:
        raise ValueError(f"Unknown mass formula type: '{mass_formula_type}'")
    return calculator


# ==============================================================================
# PART 4: THE MAIN ORCHESTRATOR FUNCTION
# ==============================================================================

def calculate_full_quote(db: Session, request: schemas.QuoteRequest) -> schemas.QuoteResponse:
    """
    Main orchestrator to perform a full quote calculation.
    """
    # --- 1. Fetch all required data from the database in bulk ---
    fan_config = crud.get_fan_configuration(db, request.fan_configuration_id)
    if not fan_config:
        # In a real API, you would raise an HTTPException here.
        raise ValueError(f"Fan configuration with ID {request.fan_configuration_id} not found.")

    component_ids = [c.component_id for c in request.components]

    # Fetch all component parameters and global rates/settings using the new CRUD functions.
    all_component_params = crud.get_parameters_for_calculation(db, fan_config.id, component_ids)
    rates_and_settings = crud.get_rates_and_settings(db)

    # Use markup override if provided, otherwise use the default from settings
    markup = request.markup_override if request.markup_override is not None else rates_and_settings.get('default_markup', 1.0)

    calculated_components_details = []
    
    # --- 2. Loop through each component, resolve parameters, and calculate ---
    for comp_request in request.components:
        params_for_this_comp = next((p for p in all_component_params if p['component_id'] == comp_request.component_id), None)
        if not params_for_this_comp:
            print(f"Warning: Parameters for component ID {comp_request.component_id} not found. Skipping.")
            continue

        # Resolve all formula-based geometry before passing to the calculator.
        # This function modifies the dictionary in place.
        resolved_params = _resolve_formulaic_parameters(
            hub_size=fan_config.hub_size_mm,
            fan_size=fan_config.fan_size_mm,
            params=params_for_this_comp
        )

        # Get the correct calculator instance using the factory based on the resolved formula type
        calculator = get_calculator(resolved_params['mass_formula_type'])

        # Build the dictionary of request-specific parameters needed by the calculator
        request_params = {
            "hub_size_mm": fan_config.hub_size_mm,
            "fan_size_mm": fan_config.fan_size_mm,
            "blade_quantity": request.blade_quantity,
            "mass_per_blade_kg": float(fan_config.mass_per_blade_kg),
            "overrides": comp_request.model_dump()
        }

        # Execute the calculation to get the detailed dictionary
        result_dict = calculator.calculate(request_params, resolved_params, rates_and_settings)

        # Add the final markup calculation to the dictionary
        result_dict["total_cost_after_markup"] = result_dict["total_cost_before_markup"] * markup
        
        calculated_components_details.append(result_dict)

    # --- 3. Aggregate final totals from the detailed list ---
    total_mass = sum(c['real_mass_kg'] for c in calculated_components_details)
    total_material_cost = sum(c['material_cost'] for c in calculated_components_details)
    total_labour_cost = sum(c['labour_cost'] for c in calculated_components_details)
    subtotal = total_material_cost + total_labour_cost
    final_price = subtotal * markup

    # --- 4. Assemble the final response object using Pydantic models ---
    return schemas.QuoteResponse(
        fan_uid=fan_config.uid,
        total_mass_kg=round(total_mass, 2),
        total_material_cost=round(total_material_cost, 2),
        total_labour_cost=round(total_labour_cost, 2),
        subtotal_cost=round(subtotal, 2),
        markup_applied=markup,
        final_price=round(final_price, 2),
        components=[schemas.CalculatedComponent(**c) for c in calculated_components_details]
    )