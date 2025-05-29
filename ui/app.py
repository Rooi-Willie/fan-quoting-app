import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000") # Fallback for local run

st.title("Fan Quoting App UI")

st.write(f"Attempting to connect to API at: {API_BASE_URL}")

st.write(f"Hello there!")
st.write(f"1222567567")

try:
    response = requests.get(f"{API_BASE_URL}/")
    response.raise_for_status() # Raise an exception for HTTP errors
    st.json(response.json())
except requests.exceptions.RequestException as e:
    st.error(f"Could not connect to API: {e}")

# Add more UI elements later