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