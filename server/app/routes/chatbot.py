"""Chatbot API routes - chat and design flow using Hugging Face models."""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException

from app.chatbot.schemas import (
    ChatRequest,
    ChatResponse,
    DesignStartRequest,
    DesignStartResponse,
    DesignStepRequest,
    DesignStepResponse,
    DesignContext,
)
from app.chatbot.agents.agent_factory import get_agent_factory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])

# In-memory store for design flow sessions (session_id -> design_context dict)
_design_sessions: Dict[str, Dict[str, Any]] = {}


def _design_context_from_dict(data: Dict[str, Any]) -> DesignContext:
    """Recreate DesignContext from stored dict."""
    return DesignContext(
        user_id=data.get("user_id"),
        session_id=data.get("session_id"),
        conversation_history=data.get("conversation_history", []),
        current_step=data.get("current_step"),
        preferences=data.get("preferences", {}),
        collected_info=data.get("collected_info", {}),
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message with the design assistant (Hugging Face model)."""
    try:
        factory = get_agent_factory()
        design_agent = factory.get_design_agent()
        context = request.context or {}
        if request.session_id and request.session_id in _design_sessions:
            ctx_data = _design_sessions[request.session_id]
            context["design_context"] = _design_context_from_dict(ctx_data)
        response = design_agent.process(query=request.message, context=context or None)
        intent_raw = response.metadata.get("intent")
        intent = None
        if intent_raw is not None:
            try:
                intent = Intent(intent_raw) if isinstance(intent_raw, str) else intent_raw
            except (ValueError, TypeError):
                pass
        return ChatResponse(
            response=response.content,
            session_id=request.session_id or "",
            intent=intent,
            entities=None,
            metadata=response.metadata,
            sources=response.sources,
        )
    except Exception as e:
        logger.exception("Chat error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/design/start", response_model=DesignStartResponse)
async def design_start(request: DesignStartRequest) -> DesignStartResponse:
    """Start a new design assistance flow."""
    try:
        factory = get_agent_factory()
        design_agent = factory.get_design_agent()
        result = design_agent.start_design_flow(
            user_id=request.user_id,
            initial_preferences=request.initial_preferences,
        )
        ctx = result.get("design_context")
        if ctx is not None:
            _design_sessions[result["session_id"]] = (
                ctx.model_dump() if hasattr(ctx, "model_dump") else ctx.dict()
            )
        return DesignStartResponse(
            session_id=result["session_id"],
            step=result["step"],
            question=result["question"],
            options=result.get("options"),
        )
    except Exception as e:
        logger.exception("Design start error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/design/step", response_model=DesignStepResponse)
async def design_step(request: DesignStepRequest) -> DesignStepResponse:
    """Submit answer for current design step and get next step or recommendation."""
    try:
        if request.session_id not in _design_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        ctx_data = _design_sessions[request.session_id]
        design_context = _design_context_from_dict(ctx_data)
        factory = get_agent_factory()
        design_agent = factory.get_design_agent()
        result = design_agent.process_design_step(
            session_id=request.session_id,
            answer=request.answer,
            design_context=design_context,
        )
        # Persist updated context
        design_context.current_step = result.get("step", design_context.current_step)
        if result.get("completed"):
            _design_sessions.pop(request.session_id, None)
        else:
            _design_sessions[request.session_id] = (
                design_context.model_dump() if hasattr(design_context, "model_dump") else design_context.dict()
            )
        return DesignStepResponse(
            session_id=result["session_id"],
            step=result["step"],
            question=result.get("question"),
            recommendation=result.get("recommendation"),
            options=result.get("options"),
            completed=result.get("completed", False),
            metadata=result.get("metadata", {}),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Design step error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(session_id: Optional[str] = None) -> Dict[str, Any]:
    """Get conversation/design history for a session (if stored)."""
    if session_id and session_id in _design_sessions:
        ctx = _design_sessions[session_id]
        return {
            "session_id": session_id,
            "conversation_history": ctx.get("conversation_history", []),
            "current_step": ctx.get("current_step"),
            "collected_info": ctx.get("collected_info", {}),
        }
    return {"session_id": session_id, "conversation_history": [], "collected_info": {}}
