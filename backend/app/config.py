import os
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    APP_NAME: str = "Sensor Data Fabric API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    # Database configuration
    DUCKDB_PATH: str = os.getenv("DUCKDB_PATH", "sensor_fabric.duckdb")
    
    # Query Guardrail settings
    MAX_ROW_LIMIT: int = 1000
    DEFAULT_ROW_LIMIT: int = 100
    QUERY_TIMEOUT_SECONDS: float = 3.0
    ALLOWED_TABLES: List[str] = ["sensor_stations", "air_quality_readings", "query_audit_log"]
    
    # LLM Settings (optional API keys; fallback to smart offline synthesizer if none provided)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY", None)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "auto") # auto, gemini, openai, anthropic, mock
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "*"]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
