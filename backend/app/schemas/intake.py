from datetime import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    structured_output: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    assistant_message: ChatMessageResponse
    structured_update: dict | None = None
    progress: dict
    unresolved_questions: list[str] = []


class InterviewProgress(BaseModel):
    current_step: str
    completion_pct: int
    steps_completed: list[str]
    steps_remaining: list[str]
