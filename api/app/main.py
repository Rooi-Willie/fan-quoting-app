from fastapi import FastAPI
import os
from dotenv import load_dotenv

load_dotenv() # To load .env if running locally outside Docker for some reason

app = FastAPI()

@app.get("/")
async def root():
    db_url = os.getenv("DATABASE_URL", "not_set")
    return {"message": "Hello from Quoting API", "db_url_preview": db_url[:25] + "..." if db_url else "not_set"}

# Add more endpoints later