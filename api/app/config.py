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
        self.db_user = os.getenv("DB_USER", "postgres")
        self.db_password = os.getenv("DB_PASSWORD", "postgres")
        self.db_name = os.getenv("DB_NAME", "fan_quoting")
        self.db_host = os.getenv("DB_HOST", "db")
        self.db_port = os.getenv("DB_PORT", "5432")
        
        # Cloud SQL Configuration (for production)
        self.cloud_sql_connection_name = os.getenv("CLOUD_SQL_CONNECTION_NAME")
        
        # API Key
        self.api_key = os.getenv("API_KEY")
        
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
