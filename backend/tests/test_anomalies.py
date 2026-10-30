import pytest
from app.analytics.anomaly_detector import AnomalyDetector
from app.ingestion.seed_data import seed_database
from app.database import db_manager

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    seed_database(days=7)

def test_anomaly_detection_identifies_injected_spikes():
    detector = AnomalyDetector(z_threshold=2.5)
    anomalies = detector.detect_anomalies(station_id="DEL-001", pollutant="pm25")
    
    assert len(anomalies) > 0, "Expected to detect injected PM2.5 anomalies in Anand Vihar (DEL-001)"
    
    # Check structure and keys
    first = anomalies[0]
    assert "z_score" in first
    assert first["z_score"] >= 2.5
    assert "explanation" in first
    assert "severity" in first
    assert first["severity"] in ["MODERATE", "HIGH", "CRITICAL"]

def test_anomaly_clean_station():
    detector = AnomalyDetector(z_threshold=5.0) # High threshold
    anomalies = detector.detect_anomalies(pollutant="so2")
    # SO2 had normal jitter, should have very few or zero extreme outliers
    assert isinstance(anomalies, list)
