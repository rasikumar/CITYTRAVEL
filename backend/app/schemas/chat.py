from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    reply: str
    intent: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: str
