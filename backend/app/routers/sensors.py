from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from app.database import db_manager

router = APIRouter(prefix="/api/sensors", tags=["Sensors"])

@router.get("/stations")
def get_sensor_stations():
    """Retrieve all registered IoT sensor stations."""
    sql = "SELECT * FROM sensor_stations ORDER BY city ASC"
    rows, _ = db_manager.execute_query(sql)
    return {"stations": rows, "count": len(rows)}

@router.get("/readings")
def get_readings(
    station_id: Optional[str] = None,
    city: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    pollutant: Optional[str] = None
):
    """Direct query endpoint for time-series air quality readings without AI."""
    sql = """
        SELECT r.*, s.station_name, s.city, s.country
        FROM air_quality_readings r
        JOIN sensor_stations s ON r.station_id = s.station_id
        WHERE 1=1
    """
    params = []
    if station_id:
        sql += " AND r.station_id = ?"
        params.append(station_id)
    if city:
        sql += " AND LOWER(s.city) = LOWER(?)"
        params.append(city)
    
    sql += " ORDER BY r.timestamp DESC LIMIT ?"
    params.append(limit)

    rows, cols = db_manager.execute_query(sql, tuple(params))
    return {
        "readings": rows,
        "count": len(rows),
        "columns": cols
    }

@router.get("/summary")
def get_city_summary():
    """Returns high-level air quality aggregates grouped by city."""
    sql = """
        SELECT 
            s.city,
            s.country,
            COUNT(DISTINCT s.station_id) AS active_stations,
            ROUND(AVG(r.pm25), 1) AS avg_pm25,
            ROUND(MAX(r.pm25), 1) AS peak_pm25,
            ROUND(AVG(r.no2), 1) AS avg_no2,
            ROUND(AVG(r.temperature), 1) AS avg_temp,
            ROUND(AVG(r.humidity), 1) AS avg_humidity
        FROM air_quality_readings r
        JOIN sensor_stations s ON r.station_id = s.station_id
        GROUP BY s.city, s.country
        ORDER BY avg_pm25 DESC
    """
    rows, cols = db_manager.execute_query(sql)
    return {"summary": rows, "columns": cols}
