from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.llm.agent import agent

router = APIRouter(prefix="/api/chat", tags=["AI Chat & Agent"])

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    message: str
    tool_used: Optional[str] = None
    proposed_sql: Optional[str] = None
    sanitized_sql: Optional[str] = None
    is_safe: bool
    rejection_reason: Optional[str] = None
    execution_time_ms: float
    columns: List[str]
    rows: List[Dict[str, Any]]
    audit_id: Optional[str] = None

@router.post("/", response_model=ChatResponse)
def chat_with_sensor_data(payload: ChatRequest):
    """
    Natural language chat interface with the Data Fabric.
    The LLM proposes tools/queries, guardrails validate them before execution,
    and structured visual data is returned alongside natural language answers.
    """
    result = agent.process_message(payload.message)
    return ChatResponse(**result)
