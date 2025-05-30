import os

# --- Application Wide Settings ---
CURRENCY_SYMBOL = "R"
APP_TITLE = "ABF Aux Axial Quoting App"

# --- Fan Configuration Constants ---
COMPONENT_ORDER = [
    "Screen Inlet Outside", "Screen Inlet Inside", "Conical Inlet",
    "Silencer 1D", "Inlet-Track", "Rotor", "Motor Barrel",
    "SCD", "Diffuser"
]

# Assumes 'images' folder is at the same level as the script you run with `streamlit run` (e.g., login_page.py)
# And that `streamlit run` is executed from the project root (abf_quoting_app/).
IMAGE_FOLDER_NAME = "images"
PROJECT_ROOT = os.getcwd() # Gets the current working directory
IMAGE_FOLDER_PATH = os.path.join(PROJECT_ROOT, IMAGE_FOLDER_NAME)

def get_image_path(component_name):
    """Generates a standardized image filename and returns the full path."""
    # Example naming convention: "Screen Inlet Outside" -> "screen_inlet_outside.png"
    filename = component_name.lower().replace(" ", "_") + ".png"
    return os.path.join(IMAGE_FOLDER_PATH, filename)

COMPONENT_IMAGES = {name: get_image_path(name) for name in COMPONENT_ORDER}

# Define Row structure: (Label, Type, Default/Dummy Value, Format Hint/Units)
# Types: 'DB' (Database/Fixed), 'Calc' (Calculated), 'Mod' (Modifiable)
ROW_DEFINITIONS = [
    ("Overall Diameter", 'DB', 1000.0, "mm"),
    ("Total Length", 'DB', 500.0, "mm"),
    ("Stiffening Factor", 'DB', 1.1, "factor"),
    ("Markup", 'DB', 25.0, "%"),
    ("Thickness", 'Mod', 5.0, "mm"),
    ("Fabrication Waste", 'Mod', 15.0, "%"),
    ("Ideal Mass", 'Calc', 50.0, "kg"),
    ("Real Mass", 'Calc', 55.0, "kg"),
    ("Feedstock Mass", 'Calc', 63.25, "kg"),
    (f"Material Cost", 'Calc', 1265.00, CURRENCY_SYMBOL),
    ("Labour", 'Calc', 10.0, "hrs"),
    (f"Total Cost", 'Calc', 2500.00, CURRENCY_SYMBOL),
]

# --- Motor Options ---
MOTOR_TYPES = ["Standard AC", "IE3 AC", "EC Motor", "Hazardous Area Motor"]