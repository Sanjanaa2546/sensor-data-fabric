import pytest
from app.guardrails.sql_validator import SQLValidator

@pytest.fixture
def validator():
    return SQLValidator(
        allowed_tables={"sensor_stations", "air_quality_readings", "query_audit_log"},
        default_limit=100,
        max_limit=1000
    )

def test_drop_table_is_blocked(validator):
    bad_queries = [
        "DROP TABLE sensor_stations;",
        "drop table air_quality_readings",
        "DROP TABLE IF EXISTS sensor_stations CASCADE;"
    ]
    for q in bad_queries:
        is_safe, _, reason = validator.validate_and_sanitize(q)
        assert not is_safe, f"Expected '{q}' to be blocked!"
        assert "Security Violation" in reason

def test_delete_is_blocked(validator):
    bad_queries = [
        "DELETE FROM sensor_stations WHERE station_id = 'DEL-001';",
        "delete from air_quality_readings"
    ]
    for q in bad_queries:
        is_safe, _, reason = validator.validate_and_sanitize(q)
        assert not is_safe
        assert "Security Violation" in reason

def test_insert_and_update_blocked(validator):
    bad_queries = [
        "INSERT INTO sensor_stations VALUES ('X', 'Y', 'Z', 'C', 0, 0, 'M', NOW(), 'A');",
        "UPDATE air_quality_readings SET pm25 = 0 WHERE station_id = 'DEL-001';"
    ]
    for q in bad_queries:
        is_safe, _, reason = validator.validate_and_sanitize(q)
        assert not is_safe
        assert "Security Violation" in reason

def test_multiple_statement_chaining_blocked(validator):
    # Semicolon injection attack
    bad_sql = "SELECT * FROM sensor_stations; DROP TABLE air_quality_readings;"
    is_safe, _, reason = validator.validate_and_sanitize(bad_sql)
    assert not is_safe
    assert "Multiple SQL statements detected" in reason

def test_unauthorized_tables_blocked(validator):
    bad_queries = [
        "SELECT * FROM user_passwords;",
        "SELECT * FROM information_schema.tables;",
        "SELECT * FROM system_credentials JOIN sensor_stations ON 1=1;",
        "SELECT (SELECT secret_key FROM admin_config) FROM sensor_stations;"
    ]
    for q in bad_queries:
        is_safe, _, reason = validator.validate_and_sanitize(q)
        assert not is_safe
        assert "Access Denied" in reason or "unauthorized table" in reason

def test_dangerous_functions_blocked(validator):
    bad_queries = [
        "SELECT * FROM read_csv('secret.csv');",
        "SELECT getenv('AWS_SECRET_ACCESS_KEY') FROM sensor_stations;"
    ]
    for q in bad_queries:
        is_safe, _, reason = validator.validate_and_sanitize(q)
        assert not is_safe

def test_valid_select_allowed_and_limit_injected(validator):
    valid_sql = "SELECT city, station_name FROM sensor_stations WHERE city = 'Delhi'"
    is_safe, sanitized, reason = validator.validate_and_sanitize(valid_sql)
    assert is_safe
    assert reason is None
    # Verify LIMIT 100 was automatically injected
    assert "LIMIT 100" in sanitized.upper()

def test_excessive_limit_capped(validator):
    sql_with_large_limit = "SELECT * FROM air_quality_readings LIMIT 999999;"
    is_safe, sanitized, reason = validator.validate_and_sanitize(sql_with_large_limit)
    assert is_safe
    assert "LIMIT 1000" in sanitized.upper()
    assert "999999" not in sanitized

def test_valid_ctes_allowed(validator):
    cte_sql = """
        WITH city_stats AS (
            SELECT city, AVG(pm25) as avg_p 
            FROM air_quality_readings r
            JOIN sensor_stations s ON r.station_id = s.station_id
            GROUP BY city
        )
        SELECT * FROM city_stats WHERE avg_p > 50;
    """
    is_safe, sanitized, reason = validator.validate_and_sanitize(cte_sql)
    assert is_safe
    assert reason is None
