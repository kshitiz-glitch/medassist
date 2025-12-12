"""
Chat Router
Handles AI agent chat interactions for both patients and doctors.
"""

import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, ConversationHistory
from app.schemas import (
    ChatRequest, ChatResponse, ConversationResponse, 
    PromptHistoryResponse
)
from app.agent import agent
from app.routers.auth import get_current_active_user


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message to the AI agent.
    The agent will process the message, potentially using tools,
    and return a response.
    
    Supports multi-turn conversations via session_id.
    """
    try:
        result = await agent.process_message(
            user_message=request.message,
            user_id=str(current_user.id),
            session_id=request.session_id,
            user_role=current_user.role.value
        )
        
        return ChatResponse(
            message=result["message"],
            session_id=result["session_id"],
            tools_used=result.get("tools_used", []),
            context=result.get("context", {})
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )


@router.get("/history", response_model=List[ConversationResponse])
async def get_conversation_history(
    session_id: Optional[str] = None,
    limit: int = Query(default=10, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get conversation history for the current user.
    Optionally filter by session_id.
    """
    query = select(ConversationHistory).where(
        ConversationHistory.user_id == current_user.id
    )
    
    if session_id:
        query = query.where(ConversationHistory.session_id == session_id)
    
    query = query.order_by(ConversationHistory.updated_at.desc()).limit(limit)
    
    result = await db.execute(query)
    conversations = result.scalars().all()
    
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.get("/session/{session_id}", response_model=ConversationResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific conversation session."""
    result = await db.execute(
        select(ConversationHistory).where(
            ConversationHistory.user_id == current_user.id,
            ConversationHistory.session_id == session_id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return ConversationResponse.model_validate(conversation)


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Clear a conversation session (marks as inactive)."""
    success = await agent.clear_conversation(
        user_id=str(current_user.id),
        session_id=session_id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session cleared successfully"}


@router.post("/new-session")
async def create_new_session(
    current_user: User = Depends(get_current_active_user)
):
    """Create a new conversation session."""
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}


@router.get("/prompts", response_model=List[PromptHistoryResponse])
async def get_prompt_history(
    limit: int = Query(default=50, le=100),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get prompt history for the current user (Bonus feature).
    Shows all prompts sent and responses received.
    """
    history = await agent.get_prompt_history(
        user_id=str(current_user.id),
        limit=limit
    )
    
    return history


@router.get("/prompts/stats")
async def get_prompt_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get statistics about prompt usage (Bonus feature)."""
    from sqlalchemy import func
    from app.models import PromptHistory
    
    # Total prompts
    result = await db.execute(
        select(func.count(PromptHistory.id)).where(
            PromptHistory.user_id == current_user.id
        )
    )
    total_prompts = result.scalar()
    
    # Average processing time
    result = await db.execute(
        select(func.avg(PromptHistory.processing_time_ms)).where(
            PromptHistory.user_id == current_user.id
        )
    )
    avg_processing_time = result.scalar() or 0
    
    # Most used tools
    result = await db.execute(
        select(PromptHistory.tools_used).where(
            PromptHistory.user_id == current_user.id
        )
    )
    all_tools = []
    for row in result.scalars():
        if row:
            all_tools.extend(row)
    
    tool_counts = {}
    for tool in all_tools:
        tool_counts[tool] = tool_counts.get(tool, 0) + 1
    
    most_used_tools = sorted(tool_counts.items(), key=lambda x: -x[1])[:5]
    
    return {
        "total_prompts": total_prompts,
        "avg_processing_time_ms": round(avg_processing_time, 2),
        "most_used_tools": [{"tool": t, "count": c} for t, c in most_used_tools]
    }
