import duckdb
import threading
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance: Optional["DatabaseManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self.db_path = settings.DUCKDB_PATH
        self._db_lock = threading.Lock()
        self.conn = duckdb.connect(self.db_path)
        self._init_schema()
        self._initialized = True
        logger.info(f"Connected to DuckDB at {self.db_path}")

    def _init_schema(self):
        with self._db_lock:
            # 1. Sensor stations table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS sensor_stations (
                    station_id VARCHAR PRIMARY KEY,
                    station_name VARCHAR NOT NULL,
                    city VARCHAR NOT NULL,
                    country VARCHAR NOT NULL,
                    latitude DOUBLE NOT NULL,
                    longitude DOUBLE NOT NULL,
                    sensor_model VARCHAR,
                    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR DEFAULT 'ACTIVE'
                );
            """)

            # 2. Sensor readings time-series table
            # Modeled after OpenAQ standard pollutants: PM2.5, PM10, NO2, CO, O3, SO2
            # plus ambient temperature and humidity
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS air_quality_readings (
                    reading_id VARCHAR PRIMARY KEY,
                    station_id VARCHAR NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    pm25 DOUBLE,       -- µg/m³
                    pm10 DOUBLE,       -- µg/m³
                    no2 DOUBLE,        -- ppb
                    co DOUBLE,         -- ppm
                    o3 DOUBLE,         -- ppb
                    so2 DOUBLE,        -- ppb
                    temperature DOUBLE,-- °C
                    humidity DOUBLE,   -- %
                    aqi_category VARCHAR
                );
            """)

            # 3. Query audit log table for Data Fabric governance tracking
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS query_audit_log (
                    audit_id VARCHAR PRIMARY KEY,
                    query_text VARCHAR NOT NULL,
                    validated_query VARCHAR,
                    is_safe BOOLEAN NOT NULL,
                    rejection_reason VARCHAR,
                    execution_time_ms DOUBLE,
                    row_count INTEGER,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    executed_by VARCHAR DEFAULT 'llm_tool'
                );
            """)

            # Create indices for fast time-series queries and station lookups
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_readings_station_time 
                ON air_quality_readings (station_id, timestamp);
            """)

    def execute_query(self, sql: str, params: tuple = ()):
        """Execute query under a lock and return rows as list of dicts and column names."""
        with self._db_lock:
            cur = self.conn.cursor()
            cur.execute(sql, params)
            if cur.description is None:
                return [], []
            columns = [desc[0] for desc in cur.description]
            records = [dict(zip(columns, row)) for row in cur.fetchall()]
            return records, columns

    def get_raw_connection(self):
        return self.conn

db_manager = DatabaseManager()
