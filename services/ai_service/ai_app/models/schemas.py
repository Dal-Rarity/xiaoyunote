from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="用户问题")
    session_id: str = Field(..., min_length=8, max_length=64, description="会话 ID")


class RetrieveDebug(BaseModel):
    question: str
    user_id: int
    data_type: str | None = None
    category: str | None = None