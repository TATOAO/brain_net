"""
Chat API routes for Brain_Net LLM Service
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import AsyncGenerator
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse
from app.services.chat import ChatService
from app.core.dependencies import get_chat_service

router = APIRouter()


@router.post("/completions", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatResponse:
    """Generate chat completion for a given prompt."""
    try:
        response = await chat_service.generate_completion(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")


@router.post("/completions/stream")
async def chat_completion_stream(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
) -> StreamingResponse:
    """Generate streaming chat completion for a given prompt."""
    try:
        async def generate():
            async for chunk in chat_service.generate_completion_stream(request):
                yield f"data: {chunk.json()}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(generate(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming chat completion failed: {str(e)}")


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatHistoryResponse:
    """Get chat history for a session."""
    try:
        history = await chat_service.get_chat_history(session_id, limit)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")


@router.delete("/history/{session_id}")
async def clear_chat_history(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
) -> dict:
    """Clear chat history for a session."""
    try:
        await chat_service.clear_chat_history(session_id)
        return {"message": f"Chat history cleared for session {session_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear chat history: {str(e)}")


@router.post("/sessions/{session_id}/summarize")
async def summarize_session(
    session_id: str,
    background_tasks: BackgroundTasks,
    chat_service: ChatService = Depends(get_chat_service)
) -> dict:
    """Summarize a chat session."""
    try:
        background_tasks.add_task(chat_service.summarize_session, session_id)
        return {"message": f"Session {session_id} summarization started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start summarization: {str(e)}") 