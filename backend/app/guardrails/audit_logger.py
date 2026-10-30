import uuid
import time
import logging
from typing import Optional, Dict, Any, List
from app.database import db_manager

logger = logging.getLogger(__name__)

class AuditLogger:
    @staticmethod
    def log_query_execution(
        raw_query: str,
        validated_query: Optional[str],
        is_safe: bool,
        rejection_reason: Optional[str] = None,
        execution_time_ms: float = 0.0,
        row_count: int = 0,
        executed_by: str = "llm_agent"
    ) -> str:
        audit_id = f"aud_{uuid.uuid4().hex[:12]}"
        try:
            conn = db_manager.get_raw_connection()
            conn.execute("""
                INSERT INTO query_audit_log (
                    audit_id, query_text, validated_query, is_safe,
                    rejection_reason, execution_time_ms, row_count, executed_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                audit_id,
                raw_query,
                validated_query,
                is_safe,
                rejection_reason,
                round(execution_time_ms, 2),
                row_count,
                executed_by
            ))
            logger.info(f"Audit record [{audit_id}]: is_safe={is_safe}, rows={row_count}, time={execution_time_ms:.2f}ms")
        except Exception as e:
            logger.error(f"Failed to record audit log: {e}")
        return audit_id

    @staticmethod
    def get_recent_audits(limit: int = 50) -> List[Dict[str, Any]]:
        records, _ = db_manager.execute_query(
            "SELECT * FROM query_audit_log ORDER BY executed_at DESC LIMIT ?",
            (limit,)
        )
        return records

audit_logger = AuditLogger()
