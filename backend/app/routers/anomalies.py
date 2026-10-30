from fastapi import APIRouter, Query
from typing import Optional
from app.analytics.anomaly_detector import anomaly_detector

router = APIRouter(prefix="/api/anomalies", tags=["Anomalies"])

@router.get("/")
def get_sensor_anomalies(
    station_id: Optional[str] = None,
    pollutant: str = Query(default="pm25", pattern="^(pm25|pm10|no2|co|o3|so2|temperature|humidity)$")
):
    """
    Scans sensor readings for statistical anomalies (Z-score & rolling average spikes)
    and returns contextual plain-language explanations.
    """
    anomalies = anomaly_detector.detect_anomalies(station_id=station_id, pollutant=pollutant)
    return {
        "pollutant": pollutant,
        "station_id": station_id,
        "count": len(anomalies),
        "anomalies": anomalies
    }
