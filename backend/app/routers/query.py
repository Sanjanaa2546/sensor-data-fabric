import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.guardrails.sql_validator import validator
from app.guardrails.audit_logger import audit_logger
from app.database import db_manager

router = APIRouter(prefix="/api/query", tags=["Query Guardrails"])

class QueryRequest(BaseModel):
    sql: str
    executed_by: Optional[str] = "api_client"

class QueryResponse(BaseModel):
    is_safe: bool
    raw_sql: str
    sanitized_sql: Optional[str] = None
    rejection_reason: Optional[str] = None
    execution_time_ms: float
    row_count: int
    columns: List[str]
    rows: List[Dict[str, Any]]
    audit_id: str

@router.post("/execute", response_model=QueryResponse)
def execute_guardrailed_sql(payload: QueryRequest):
    """
    Executes an SQL query through the Data Fabric AST security guardrail.
    Validates AST, checks table whitelist, restricts to SELECT, injects LIMIT, logs audit.
    """
    start_time = time.time()
    raw_sql = payload.sql

    is_safe, sanitized_sql, rejection_reason = validator.validate_and_sanitize(raw_sql)

    if not is_safe:
        elapsed_ms = (time.time() - start_time) * 1000.0
        audit_id = audit_logger.log_query_execution(
            raw_query=raw_sql,
            validated_query=None,
            is_safe=False,
            rejection_reason=rejection_reason,
            execution_time_ms=elapsed_ms,
            row_count=0,
            executed_by=payload.executed_by
        )
        return QueryResponse(
            is_safe=False,
            raw_sql=raw_sql,
            sanitized_sql=None,
            rejection_reason=rejection_reason,
            execution_time_ms=round(elapsed_ms, 2),
            row_count=0,
            columns=[],
            rows=[],
            audit_id=audit_id
        )

    try:
        q_start = time.time()
        rows, columns = db_manager.execute_query(sanitized_sql)
        elapsed_ms = (time.time() - q_start) * 1000.0

        audit_id = audit_logger.log_query_execution(
            raw_query=raw_sql,
            validated_query=sanitized_sql,
            is_safe=True,
            rejection_reason=None,
            execution_time_ms=elapsed_ms,
            row_count=len(rows),
            executed_by=payload.executed_by
        )

        return QueryResponse(
            is_safe=True,
            raw_sql=raw_sql,
            sanitized_sql=sanitized_sql,
            rejection_reason=None,
            execution_time_ms=round(elapsed_ms, 2),
            row_count=len(rows),
            columns=columns,
            rows=rows,
            audit_id=audit_id
        )
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000.0
        audit_id = audit_logger.log_query_execution(
            raw_query=raw_sql,
            validated_query=sanitized_sql,
            is_safe=False,
            rejection_reason=f"Runtime DB Error: {str(e)}",
            execution_time_ms=elapsed_ms,
            row_count=0,
            executed_by=payload.executed_by
        )
        return QueryResponse(
            is_safe=False,
            raw_sql=raw_sql,
            sanitized_sql=sanitized_sql,
            rejection_reason=str(e),
            execution_time_ms=round(elapsed_ms, 2),
            row_count=0,
            columns=[],
            rows=[],
            audit_id=audit_id
        )

@router.get("/audit")
def get_audit_trail(limit: int = 50):
    """Returns the governance audit trail of all executed and blocked queries."""
    audits = audit_logger.get_recent_audits(limit=limit)
    return {"audits": audits, "count": len(audits)}
