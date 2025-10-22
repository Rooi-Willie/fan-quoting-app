"""
Configuration Management
Centralized configuration for the API
"""

import os
from typing import Optional


class Settings:
    """Application settings"""
    
    def __init__(self):
        # Environment
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = self.environment == "development"
        
        # API Configuration
        self.api_title = "Fan Quoting API"
        self.api_version = "1.0.0"
        self.api_description = "API for calculating fan quotes and managing configurations"
        
        # Database Configuration
        # Local development uses POSTGRES_* env vars from .env
        # Production uses DB_* env vars from Cloud Run
        
        # In production, fail if credentials aren't set (security requirement)
        # In development, use safe defaults for convenience
        if self.environment == "production":
            # Production: Require all credentials to be explicitly set
            self.db_user = os.getenv("DB_USER")
            self.db_password = os.getenv("DB_PASSWORD")
            self.db_name = os.getenv("DB_NAME")
            
            if not self.db_user or not self.db_password or not self.db_name:
                raise RuntimeError(
                    "Production environment requires DB_USER, DB_PASSWORD, and DB_NAME "
                    "environment variables to be set. Never use default credentials in production."
                )
        else:
            # Development: Fall back to safe defaults from Docker Compose
            self.db_user = os.getenv("DB_USER", os.getenv("POSTGRES_USER", "devuser"))
            self.db_password = os.getenv("DB_PASSWORD", os.getenv("POSTGRES_PASSWORD", "devpassword"))
            self.db_name = os.getenv("DB_NAME", os.getenv("POSTGRES_DB", "quoting_db"))
        
        self.db_host = os.getenv("DB_HOST", "db")
        self.db_port = os.getenv("DB_PORT", "5432")
        
        # Cloud SQL Configuration (for production)
        self.cloud_sql_connection_name = os.getenv("CLOUD_SQL_CONNECTION_NAME")
        
        # API Key (required for authentication)
        self.api_key = os.getenv("API_KEY")
        
        if not self.api_key:
            if self.environment == "production":
                raise RuntimeError(
                    "API_KEY environment variable must be set in production. "
                    "This is a critical security requirement."
                )
            else:
                raise RuntimeError(
                    "API_KEY environment variable is not set. "
                    "For local development, add API_KEY=dev-local-key-12345 to your .env file."
                )
        
        # CORS Origins
        self.cors_origins = self._get_cors_origins()
    
    def _get_cors_origins(self) -> list:
        """Get CORS allowed origins based on environment"""
        if self.environment == "production":
            return [
                "https://*.streamlit.app",
                "https://*.airblowfans.co.za",
            ]
        else:
            return [
                "http://localhost:8501",
                "http://localhost:3000",
                "http://127.0.0.1:8501",
            ]
    
    def get_database_url(self) -> str:
        """Get database connection URL"""
        if self.cloud_sql_connection_name:
            # Production: Cloud SQL with Unix socket
            return (
                f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
                f"@/{self.db_name}?host=/cloudsql/{self.cloud_sql_connection_name}"
            )
        else:
            # Development: Standard PostgreSQL connection
            return (
                f"postgresql://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )


# Global settings instance
settings = Settings()
