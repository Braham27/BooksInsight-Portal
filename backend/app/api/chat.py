from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.clerk import AuthUser, get_current_user
from app.database import get_db
from app.models.case import Case
from app.models.chat_message import ChatMessage
from app.schemas.intake import ChatRequest, ChatResponse, ChatMessageResponse
from app.services.interview_service import process_message

router = APIRouter(prefix="/cases/{case_id}", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def send_message(
    case_id: str,
    body: ChatRequest,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    response = await process_message(db, case, body.message, user.user_id)
    return response


@router.get("/chat/history", response_model=list[ChatMessageResponse])
async def get_chat_history(
    case_id: str,
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    if case.user_id != user.user_id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.case_id == case_id)
        .order_by(ChatMessage.created_at)
    )
    return result.scalars().all()
