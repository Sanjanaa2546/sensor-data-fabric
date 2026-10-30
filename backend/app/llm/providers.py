import os
import json
import logging
import httpx
from typing import Dict, Any, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the AI Data Fabric Assistant for an IoT Sensor & Air Quality Monitoring Network.
You help engineers, environmental researchers, and city officials query and analyze live sensor data.

You have access to the tool `run_query(query: str)` which executes a SQL query on DuckDB.
IMPORTANT ARCHITECTURAL & SECURITY RULES:
1. You NEVER access the database directly; you MUST propose a SQL query via `run_query`.
2. All proposed queries are verified by an AST guardrail validator before execution.
3. Propose ONLY SELECT statements. DROP, DELETE, INSERT, UPDATE, ALTER, PRAGMA, or system functions are strictly rejected.
4. Available tables and columns:
   - `sensor_stations` (station_id, station_name, city, country, latitude, longitude, sensor_model, status)
   - `air_quality_readings` (reading_id, station_id, timestamp, pm25, pm10, no2, co, o3, so2, temperature, humidity, aqi_category)
   - `query_audit_log` (audit_id, query_text, is_safe, execution_time_ms, row_count, executed_at)
5. Timestamp formatting: DuckDB supports standard SQL intervals like `timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days'`.
6. Return concise, insightful summaries highlighting key readings, trends, and health categories.
"""

SCHEMA_INFO = """
Table: sensor_stations
- station_id: VARCHAR (e.g., 'DEL-001', 'LON-002', 'NYC-003', 'PEK-004', 'PAR-005')
- station_name: VARCHAR (e.g., 'Anand Vihar EcoStation')
- city: VARCHAR ('Delhi', 'London', 'New York', 'Beijing', 'Paris')
- country: VARCHAR ('India', 'United Kingdom', 'United States', 'China', 'France')
- latitude, longitude: DOUBLE
- sensor_model: VARCHAR

Table: air_quality_readings
- reading_id: VARCHAR
- station_id: VARCHAR
- timestamp: TIMESTAMP (Hourly records for the past 30 days)
- pm25: DOUBLE (µg/m³, fine particulate matter)
- pm10: DOUBLE (µg/m³, coarse particulate matter)
- no2: DOUBLE (ppb, nitrogen dioxide from vehicular emissions)
- co: DOUBLE (ppm, carbon monoxide)
- o3: DOUBLE (ppb, ground-level ozone)
- so2: DOUBLE (ppb, sulfur dioxide)
- temperature: DOUBLE (°C)
- humidity: DOUBLE (%)
- aqi_category: VARCHAR ('Good', 'Moderate', 'Unhealthy for Sensitive Groups', 'Unhealthy', 'Very Unhealthy', 'Hazardous')
"""

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "run_query",
            "description": "Proposes a SQL query to query sensor stations and air quality readings. Strictly SELECT only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute against the sensor fabric (DuckDB)."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "detect_anomalies",
            "description": "Runs statistical Z-score and rolling average anomaly detection on sensor time series.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pollutant": {
                        "type": "string",
                        "description": "Pollutant metric to evaluate (pm25, pm10, no2, o3, so2, co, temperature). Defaults to pm25."
                    },
                    "station_id": {
                        "type": "string",
                        "description": "Optional station ID filter (e.g. DEL-001)."
                    }
                }
            }
        }
    }
]

class SmartMockLLM:
    """
    Intelligent zero-API-key local query translator.
    Enables immediate local and CI execution without requiring external API keys.
    """
    @staticmethod
    def generate_tool_call_or_reply(prompt: str) -> Dict[str, Any]:
        p = prompt.lower()
        
        # Security test detection: if user asks to test drop table or malicious queries
        if "drop table" in p or "drop" in p and "table" in p:
            return {
                "type": "tool_call",
                "tool_name": "run_query",
                "arguments": {"query": "DROP TABLE sensor_stations;"}
            }
        if "delete from" in p:
            return {
                "type": "tool_call",
                "tool_name": "run_query",
                "arguments": {"query": "DELETE FROM air_quality_readings WHERE pm25 > 100;"}
            }
        if "union select" in p or "information_schema" in p:
            return {
                "type": "tool_call",
                "tool_name": "run_query",
                "arguments": {"query": "SELECT * FROM sensor_stations UNION SELECT * FROM information_schema.tables;"}
            }

        # Anomaly detection intent
        if any(w in p for w in ["anomal", "outlier", "spike", "unusual", "flag"]):
            pollutant = "pm25"
            for poll in ["pm10", "no2", "o3", "co", "so2", "temp"]:
                if poll in p:
                    pollutant = "temperature" if poll == "temp" else poll
            station_id = None
            if "delhi" in p or "del-001" in p or "anand vihar" in p:
                station_id = "DEL-001"
            elif "london" in p or "lon-002" in p:
                station_id = "LON-002"
            elif "new york" in p or "nyc" in p:
                station_id = "NYC-003"
            
            return {
                "type": "tool_call",
                "tool_name": "detect_anomalies",
                "arguments": {"pollutant": pollutant, "station_id": station_id}
            }

        # Which city had the worst PM2.5 last week / highest pollution?
        if ("worst" in p or "highest" in p or "peak" in p or "max" in p) and ("pm25" in p or "pm2.5" in p or "pollution" in p):
            return {
                "type": "tool_call",
                "tool_name": "run_query",
                "arguments": {
                    "query": """SELECT s.city, s.station_name, 
       ROUND(AVG(r.pm25), 2) AS avg_pm25, 
       ROUND(MAX(r.pm25), 2) AS max_pm25, 
       COUNT(*) AS total_readings
FROM air_quality_readings r
JOIN sensor_stations s ON r.station_id = s.station_id
WHERE r.timestamp >= (SELECT MAX(timestamp) - INTERVAL '7 days' FROM air_quality_readings)
GROUP BY s.city, s.station_name
ORDER BY avg_pm25 DESC;"""
                }
            }

        # Compare cities (e.g. London and Delhi)
        if "compare" in p or ("london" in p and "delhi" in p):
            return {
                "type": "tool_call",
                "tool_name": "run_query",
                "arguments": {
                    "query": """SELECT s.city,
       ROUND(AVG(r.pm25), 2) AS avg_pm25,
       ROUND(AVG(r.no2), 2) AS avg_no2,
       ROUND(AVG(r.o3), 2) AS avg_o3,
       ROUND(AVG(r.temperature), 1) AS avg_temp
FROM air_quality_readings r
JOIN sensor_stations s ON r.station_id = s.station_id
GROUP BY s.city
ORDER BY avg_pm25 DESC;"""
                }
            }

        # Hazardous / Unhealthy AQI counts
        if "hazardous" in p or "unhealthy" in p:
            return {
                "type": "tool_call",
                "tool_name": "run_query",
                "arguments": {
                    "query": """SELECT s.city, r.aqi_category, COUNT(*) AS count
FROM air_quality_readings r
JOIN sensor_stations s ON r.station_id = s.station_id
WHERE r.aqi_category IN ('Unhealthy', 'Very Unhealthy', 'Hazardous')
GROUP BY s.city, r.aqi_category
ORDER BY count DESC;"""
                }
            }

        # Temperature or weather
        if "temp" in p or "temperature" in p or "weather" in p:
            return {
                "type": "tool_call",
                "tool_name": "run_query",
                "arguments": {
                    "query": """SELECT s.city, s.station_name, 
       ROUND(AVG(r.temperature), 1) AS avg_temp,
       ROUND(MIN(r.temperature), 1) AS min_temp,
       ROUND(MAX(r.temperature), 1) AS max_temp,
       ROUND(AVG(r.humidity), 1) AS avg_humidity
FROM air_quality_readings r
JOIN sensor_stations s ON r.station_id = s.station_id
GROUP BY s.city, s.station_name
ORDER BY avg_temp DESC;"""
                }
            }

        # Station info / sensor list
        if "station" in p or "sensor" in p or "model" in p or "status" in p:
            return {
                "type": "tool_call",
                "tool_name": "run_query",
                "arguments": {
                    "query": "SELECT station_id, station_name, city, country, sensor_model, status FROM sensor_stations ORDER BY city ASC;"
                }
            }

        # Default fallback query: latest readings across stations
        return {
            "type": "tool_call",
            "tool_name": "run_query",
            "arguments": {
                "query": """SELECT s.city, s.station_name, r.timestamp, r.pm25, r.pm10, r.no2, r.aqi_category
FROM air_quality_readings r
JOIN sensor_stations s ON r.station_id = s.station_id
WHERE r.timestamp = (SELECT MAX(timestamp) FROM air_quality_readings)
ORDER BY r.pm25 DESC;"""
            }
        }

    @staticmethod
    def synthesize_response(prompt: str, tool_name: str, tool_result: Any) -> str:
        """Translates query results into a structured executive summary."""
        if tool_name == "detect_anomalies":
            anomalies = tool_result if isinstance(tool_result, list) else []
            if not anomalies:
                return "Statistical time-series scan complete. No critical sensor anomalies or baseline outliers were detected in the designated monitoring window."
            
            top = anomalies[:3]
            bullets = "\n".join([f"- **{a['station_name']} ({a['city']})**: {a['explanation']}" for a in top])
            return f"### Anomaly Detection Summary\nDetected **{len(anomalies)}** statistically significant deviations across sensor telemetry:\n\n{bullets}\n\n*Recommended action:* Inspect station hardware filters and correlate with local atmospheric boundary layer advisories."

        # SQL Query result synthesis
        rows = tool_result.get("rows", []) if isinstance(tool_result, dict) else []
        col_count = len(tool_result.get("columns", [])) if isinstance(tool_result, dict) else 0
        
        if not rows:
            return "The validated query executed successfully, but returned 0 rows matching your criteria."

        first_row = rows[0]
        summary_intro = f"Analysis returned **{len(rows)}** records across the sensor telemetry network."

        if "city" in first_row and "avg_pm25" in first_row:
            top_city = first_row.get("city", "Unknown")
            worst_val = first_row.get("avg_pm25", 0)
            return (
                f"### Air Quality Analysis\n\n"
                f"**{top_city}** recorded the highest PM2.5 levels, averaging **{worst_val} µg/m³**.\n"
                f"{summary_intro} See the chart and data table below for the complete comparative breakdown."
            )
        
        return f"### Query Results Summary\n\n{summary_intro} The data has been retrieved and displayed below with AST guardrail validation."
