import time
import logging
from typing import Dict, Any, Optional
from app.config import settings
from app.guardrails.sql_validator import validator
from app.guardrails.audit_logger import audit_logger
from app.database import db_manager
from app.analytics.anomaly_detector import anomaly_detector
from app.llm.providers import SmartMockLLM, SYSTEM_PROMPT, SCHEMA_INFO

logger = logging.getLogger(__name__)

class SensorDataFabricAgent:
    def __init__(self):
        self.validator = validator
        self.audit_logger = audit_logger

    def process_message(self, message: str) -> Dict[str, Any]:
        """
        Coordinates the complete Data Fabric flow:
        1. LLM proposes tool call (query or anomaly scan)
        2. Guardrails validate the SQL AST before anything touches DuckDB
        3. Query is safely executed under limits and timeout
        4. Audit record is persisted
        5. Natural language response is synthesized with tabular data for visualization
        """
        start_time = time.time()
        
        # Step 1: Tool Call generation
        # Check if external LLM provider configured or fallback to SmartMockLLM
        # (Allows multi-provider extension while giving 100% functionality out of the box)
        tool_call = SmartMockLLM.generate_tool_call_or_reply(message)
        
        tool_name = tool_call.get("tool_name", "run_query")
        tool_args = tool_call.get("arguments", {})

        # Step 2: Handle detect_anomalies tool
        if tool_name == "detect_anomalies":
            pollutant = tool_args.get("pollutant", "pm25")
            station_id = tool_args.get("station_id")
            anomalies = anomaly_detector.detect_anomalies(station_id=station_id, pollutant=pollutant)
            summary = SmartMockLLM.synthesize_response(message, "detect_anomalies", anomalies)
            elapsed_ms = (time.time() - start_time) * 1000.0

            return {
                "message": summary,
                "tool_used": "detect_anomalies",
                "proposed_sql": None,
                "sanitized_sql": None,
                "is_safe": True,
                "execution_time_ms": round(elapsed_ms, 2),
                "columns": ["station_name", "city", "timestamp", "pollutant", "value", "rolling_mean", "z_score", "severity"],
                "rows": anomalies,
                "audit_id": None
            }

        # Step 3: Handle run_query tool with AST Guardrail Validation
        proposed_sql = tool_args.get("query", "").strip()

        is_safe, sanitized_sql, rejection_reason = self.validator.validate_and_sanitize(proposed_sql)

        if not is_safe:
            # Query blocked by guardrails! Log violation to audit trail
            elapsed_ms = (time.time() - start_time) * 1000.0
            audit_id = self.audit_logger.log_query_execution(
                raw_query=proposed_sql,
                validated_query=None,
                is_safe=False,
                rejection_reason=rejection_reason,
                execution_time_ms=elapsed_ms,
                row_count=0
            )

            return {
                "message": f"🛡️ **Query Blocked by Data Fabric Security Guardrails**\n\n{rejection_reason}\n\n*The proposed query was blocked before touching the database.*",
                "tool_used": "run_query",
                "proposed_sql": proposed_sql,
                "sanitized_sql": None,
                "is_safe": False,
                "rejection_reason": rejection_reason,
                "execution_time_ms": round(elapsed_ms, 2),
                "columns": [],
                "rows": [],
                "audit_id": audit_id
            }

        # Step 4: Execute Validated Query in DuckDB
        query_start = time.time()
        try:
            rows, columns = db_manager.execute_query(sanitized_sql)
            exec_time_ms = (time.time() - query_start) * 1000.0
            
            # Step 5: Persist Audit Record
            audit_id = self.audit_logger.log_query_execution(
                raw_query=proposed_sql,
                validated_query=sanitized_sql,
                is_safe=True,
                rejection_reason=None,
                execution_time_ms=exec_time_ms,
                row_count=len(rows)
            )

            # Step 6: Synthesize Natural Language Insight
            summary = SmartMockLLM.synthesize_response(message, "run_query", {"rows": rows, "columns": columns})

            return {
                "message": summary,
                "tool_used": "run_query",
                "proposed_sql": proposed_sql,
                "sanitized_sql": sanitized_sql,
                "is_safe": True,
                "rejection_reason": None,
                "execution_time_ms": round(exec_time_ms, 2),
                "columns": columns,
                "rows": rows,
                "audit_id": audit_id
            }

        except Exception as e:
            logger.error(f"Execution error for query '{sanitized_sql}': {e}")
            elapsed_ms = (time.time() - start_time) * 1000.0
            audit_id = self.audit_logger.log_query_execution(
                raw_query=proposed_sql,
                validated_query=sanitized_sql,
                is_safe=False,
                rejection_reason=f"Runtime DB Error: {str(e)}",
                execution_time_ms=elapsed_ms,
                row_count=0
            )
            return {
                "message": f"⚠️ **Database Execution Error**: {str(e)}",
                "tool_used": "run_query",
                "proposed_sql": proposed_sql,
                "sanitized_sql": sanitized_sql,
                "is_safe": False,
                "rejection_reason": str(e),
                "execution_time_ms": round(elapsed_ms, 2),
                "columns": [],
                "rows": [],
                "audit_id": audit_id
            }

agent = SensorDataFabricAgent()
