import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
from app.database import db_manager

logger = logging.getLogger(__name__)

class AnomalyDetector:
    def __init__(self, z_threshold: float = 2.5, spike_ratio_threshold: float = 2.2):
        self.z_threshold = z_threshold
        self.spike_ratio_threshold = spike_ratio_threshold

    def detect_anomalies(
        self,
        station_id: Optional[str] = None,
        pollutant: str = "pm25",
        hours_lookback: int = 720
    ) -> List[Dict[str, Any]]:
        """
        Runs time-series anomaly detection using Z-score and rolling 24-hour baseline.
        """
        allowed_pollutants = {"pm25", "pm10", "no2", "co", "o3", "so2", "temperature", "humidity"}
        if pollutant.lower() not in allowed_pollutants:
            pollutant = "pm25"

        query = f"""
            SELECT 
                r.reading_id,
                r.station_id,
                s.station_name,
                s.city,
                r.timestamp,
                r.{pollutant} as value,
                r.aqi_category
            FROM air_quality_readings r
            JOIN sensor_stations s ON r.station_id = s.station_id
            WHERE r.{pollutant} IS NOT NULL
        """
        params = []
        if station_id:
            query += " AND r.station_id = ?"
            params.append(station_id)

        query += " ORDER BY r.station_id, r.timestamp ASC"

        records, _ = db_manager.execute_query(query, tuple(params))
        if not records:
            return []

        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        anomalies = []

        # Process per station to respect local baselines
        for st_id, group in df.groupby("station_id"):
            group = group.sort_values("timestamp").copy()
            values = group["value"].values
            
            if len(values) < 10:
                continue

            # 1. Overall baseline statistics
            mean_val = float(np.mean(values))
            std_val = float(np.std(values))
            if std_val < 1e-4:
                std_val = 1.0

            # 2. 24-period rolling average
            group["rolling_mean"] = group["value"].rolling(window=24, min_periods=4).mean()
            group["rolling_std"] = group["value"].rolling(window=24, min_periods=4).std().fillna(std_val)
            
            # Compute Z-score against overall & local rolling window
            group["z_score"] = (group["value"] - mean_val) / std_val
            group["local_z_score"] = (group["value"] - group["rolling_mean"]) / group["rolling_std"].replace(0, 1)
            group["spike_ratio"] = group["value"] / group["rolling_mean"].replace(0, 1)

            # Flag condition: high Z-score and prominent spike ratio
            condition = (group["z_score"] >= self.z_threshold) | (group["spike_ratio"] >= self.spike_ratio_threshold)
            flagged = group[condition]

            for _, row in flagged.iterrows():
                z = round(float(row["z_score"]), 2)
                val = round(float(row["value"]), 1)
                r_mean = round(float(row["rolling_mean"]), 1) if pd.notnull(row["rolling_mean"]) else mean_val
                ratio = round(float(row["spike_ratio"]), 2) if pd.notnull(row["spike_ratio"]) else 1.0

                severity = "CRITICAL" if z >= 4.0 or ratio >= 3.0 else ("HIGH" if z >= 3.0 else "MODERATE")

                explanation = (
                    f"{row['station_name']} ({row['city']}) detected an abnormal {pollutant.upper()} level of {val} "
                    f"at {row['timestamp'].strftime('%Y-%m-%d %H:%M')}. "
                    f"This reading is {ratio}x higher than the 24-hour moving average ({r_mean}) "
                    f"with a statistical deviation of Z=+{z}. "
                    f"Current air quality status is classified as {row['aqi_category']}."
                )

                anomalies.append({
                    "reading_id": row["reading_id"],
                    "station_id": row["station_id"],
                    "station_name": row["station_name"],
                    "city": row["city"],
                    "timestamp": row["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    "pollutant": pollutant.upper(),
                    "value": val,
                    "rolling_mean": r_mean,
                    "z_score": z,
                    "spike_ratio": ratio,
                    "severity": severity,
                    "aqi_category": row["aqi_category"],
                    "explanation": explanation
                })

        # Sort descending by z_score
        anomalies.sort(key=lambda x: x["z_score"], reverse=True)
        return anomalies

anomaly_detector = AnomalyDetector()
