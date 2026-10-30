import uuid
import random
import math
from datetime import datetime, timedelta, timezone
import logging
from app.database import db_manager

logger = logging.getLogger(__name__)

STATIONS = [
    {
        "station_id": "DEL-001",
        "station_name": "Anand Vihar EcoStation",
        "city": "Delhi",
        "country": "India",
        "latitude": 28.6508,
        "longitude": 77.3153,
        "sensor_model": "AeroSens-V4 Pro",
        "base_pm25": 140.0,
        "base_pm10": 220.0,
        "base_no2": 65.0,
        "base_co": 2.2,
        "base_o3": 35.0,
        "base_so2": 18.0,
        "base_temp": 28.0,
        "base_hum": 55.0,
    },
    {
        "station_id": "LON-002",
        "station_name": "Bloomsbury CleanAir",
        "city": "London",
        "country": "United Kingdom",
        "latitude": 51.5222,
        "longitude": -0.1306,
        "sensor_model": "EnviroNode-X1",
        "base_pm25": 14.0,
        "base_pm10": 26.0,
        "base_no2": 42.0,
        "base_co": 0.5,
        "base_o3": 28.0,
        "base_so2": 4.0,
        "base_temp": 15.0,
        "base_hum": 72.0,
    },
    {
        "station_id": "NYC-003",
        "station_name": "Midtown Manhattan AirWatch",
        "city": "New York",
        "country": "United States",
        "latitude": 40.7549,
        "longitude": -73.9840,
        "sensor_model": "AeroSens-V4 Pro",
        "base_pm25": 18.0,
        "base_pm10": 32.0,
        "base_no2": 38.0,
        "base_co": 0.8,
        "base_o3": 45.0,
        "base_so2": 5.0,
        "base_temp": 18.0,
        "base_hum": 60.0,
    },
    {
        "station_id": "PEK-004",
        "station_name": "Haidian Tech District",
        "city": "Beijing",
        "country": "China",
        "latitude": 39.9590,
        "longitude": 116.2980,
        "sensor_model": "SinocAir-3000",
        "base_pm25": 65.0,
        "base_pm10": 110.0,
        "base_no2": 48.0,
        "base_co": 1.4,
        "base_o3": 40.0,
        "base_so2": 12.0,
        "base_temp": 16.0,
        "base_hum": 45.0,
    },
    {
        "station_id": "PAR-005",
        "station_name": "Champs-Élysées Central",
        "city": "Paris",
        "country": "France",
        "latitude": 48.8698,
        "longitude": 2.3075,
        "sensor_model": "EnviroNode-X1",
        "base_pm25": 16.0,
        "base_pm10": 28.0,
        "base_no2": 44.0,
        "base_co": 0.6,
        "base_o3": 32.0,
        "base_so2": 3.5,
        "base_temp": 17.0,
        "base_hum": 68.0,
    }
]

def calculate_aqi_category(pm25: float) -> str:
    if pm25 <= 12.0:
        return "Good"
    elif pm25 <= 35.4:
        return "Moderate"
    elif pm25 <= 55.4:
        return "Unhealthy for Sensitive Groups"
    elif pm25 <= 150.4:
        return "Unhealthy"
    elif pm25 <= 250.4:
        return "Very Unhealthy"
    else:
        return "Hazardous"

def seed_database(days: int = 30, hourly: bool = True):
    conn = db_manager.get_raw_connection()
    
    # Check if data already exists
    count = conn.execute("SELECT COUNT(*) FROM sensor_stations").fetchone()[0]
    if count > 0:
        logger.info(f"Database already populated ({count} stations). Skipping seed.")
        return

    logger.info("Seeding sensor database with multi-city air quality time-series...")
    
    # 1. Insert stations
    for st in STATIONS:
        conn.execute("""
            INSERT INTO sensor_stations (station_id, station_name, city, country, latitude, longitude, sensor_model)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            st["station_id"],
            st["station_name"],
            st["city"],
            st["country"],
            st["latitude"],
            st["longitude"],
            st["sensor_model"]
        ))

    # 2. Generate hourly time-series readings
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    total_hours = days * 24
    start_time = now - timedelta(hours=total_hours)
    
    random.seed(42) # Deterministic for reproducible tests & analytics

    readings_to_insert = []
    
    for st in STATIONS:
        station_id = st["station_id"]
        for h in range(total_hours + 1):
            ts = start_time + timedelta(hours=h)
            hour_of_day = ts.hour
            day_offset = (now - ts).total_seconds() / 86400.0

            # Diurnal cycle variations (rush hour traffic peak at 8am and 6pm, ozone peak at 2pm)
            traffic_factor = 1.0 + 0.35 * (math.exp(-((hour_of_day - 8) ** 2) / 4) + math.exp(-((hour_of_day - 18) ** 2) / 6))
            solar_factor = 1.0 + 0.5 * max(0.0, math.sin((hour_of_day - 6) / 12 * math.pi))

            # Noise
            jitter = random.uniform(0.85, 1.15)
            
            pm25 = max(2.0, round(st["base_pm25"] * traffic_factor * jitter, 1))
            pm10 = max(4.0, round(st["base_pm10"] * traffic_factor * jitter, 1))
            no2 = max(5.0, round(st["base_no2"] * traffic_factor * jitter, 1))
            co = max(0.1, round(st["base_co"] * traffic_factor * jitter, 2))
            o3 = max(5.0, round(st["base_o3"] * solar_factor * jitter, 1))
            so2 = max(1.0, round(st["base_so2"] * jitter, 1))
            temp = round(st["base_temp"] + 4 * math.sin((hour_of_day - 9) / 24 * 2 * math.pi) + random.uniform(-1, 1), 1)
            humidity = round(max(20.0, min(95.0, st["base_hum"] - 10 * math.sin((hour_of_day - 9) / 24 * 2 * math.pi) + random.uniform(-3, 3))), 1)

            # Injected Anomaly 1: Severe industrial/smog inversion in Anand Vihar (DEL-001) 3 days ago (between 68 and 74 hours ago)
            if station_id == "DEL-001" and 68 <= (total_hours - h) <= 76:
                pm25 = round(pm25 * 3.2, 1) # Climbs to 450+
                pm10 = round(pm10 * 2.8, 1)

            # Injected Anomaly 2: Extreme traffic congestion NO2 spike in London (LON-002) 6 days ago
            if station_id == "LON-002" and 140 <= (total_hours - h) <= 144:
                no2 = round(no2 * 2.6, 1) # Climbs to 110+

            # Injected Anomaly 3: Ozone spike in NYC (NYC-003) 10 days ago during high temp wave
            if station_id == "NYC-003" and 240 <= (total_hours - h) <= 245:
                o3 = round(o3 * 2.4, 1) # Climbs to 108+

            aqi_cat = calculate_aqi_category(pm25)
            reading_id = f"rdg_{station_id}_{int(ts.timestamp())}"

            readings_to_insert.append((
                reading_id,
                station_id,
                ts.strftime("%Y-%m-%d %H:%M:%S"),
                pm25,
                pm10,
                no2,
                co,
                o3,
                so2,
                temp,
                humidity,
                aqi_cat
            ))

    # Fast bulk insertion into DuckDB
    conn.executemany("""
        INSERT INTO air_quality_readings (
            reading_id, station_id, timestamp, pm25, pm10, no2, co, o3, so2, temperature, humidity, aqi_category
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, readings_to_insert)

    logger.info(f"Successfully seeded {len(readings_to_insert)} readings across {len(STATIONS)} stations.")

if __name__ == "__main__":
    seed_database()
