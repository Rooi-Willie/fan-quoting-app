# This file will manage the connection to your PostgreSQL container or Cloud SQL.

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Load environment variables from the .env file in the root directory (for local dev)
load_dotenv(dotenv_path='../.env')

# Get database URL from settings (handles both local and Cloud SQL)
SQLALCHEMY_DATABASE_URL = settings.get_database_url()

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,
    max_overflow=2
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()