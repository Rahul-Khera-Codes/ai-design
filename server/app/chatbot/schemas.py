"""Pydantic schemas for chatbot agents and responses."""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Intent(str, Enum):
    """User intent categories."""
    LEARNING = "learning"
    DESIGN_HELP = "design_help"
    COMPARISON = "comparison"
    PRICING = "pricing"
    CARE = "care"
    GENERAL = "general"


class Entity(BaseModel):
    """Extracted entity from user query."""
    dress_type: Optional[str] = None
    fabric: Optional[str] = None
    color: Optional[str] = None
    occasion: Optional[str] = None
    body_type: Optional[str] = None
    budget: Optional[str] = None
    location: Optional[str] = None
    weather: Optional[str] = None
    style: Optional[str] = None
    size: Optional[str] = None
    
    class Config:
        extra = "allow"  # Allow additional fields


class NLUResult(BaseModel):
    """Result from NLU Agent."""
    intent: Intent
    entities: Entity
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    raw_response: Optional[str] = None


class SQLQueryResult(BaseModel):
    """Result from SQL Agent."""
    query: str = Field(description="Generated SQL query")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Query results")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Query metadata")
    success: bool = True
    error: Optional[str] = None


class RAGResult(BaseModel):
    """Result from RAG Agent."""
    answer: str = Field(description="Generated answer from retrieved context")
    context_chunks: List[Dict[str, Any]] = Field(default_factory=list, description="Retrieved context chunks")
    sources: List[str] = Field(default_factory=list, description="Source documents")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Standard response from any agent."""
    content: str = Field(description="Response content")
    agent_name: str = Field(description="Name of the agent that generated the response")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    structured_data: Optional[Dict[str, Any]] = None
    sources: Optional[List[str]] = None


class DesignContext(BaseModel):
    """Context for design assistance flow."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    current_step: Optional[int] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    collected_info: Dict[str, Any] = Field(default_factory=dict)
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def update_preference(self, key: str, value: Any):
        """Update user preference."""
        self.preferences[key] = value
    
    def update_collected_info(self, key: str, value: Any):
        """Update collected information."""
        self.collected_info[key] = value


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    user_id: Optional[str] = Field(None, description="User ID")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str = Field(..., description="Chatbot response")
    session_id: str = Field(..., description="Session ID")
    intent: Optional[Intent] = None
    entities: Optional[Entity] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    sources: Optional[List[str]] = None


class DesignStartRequest(BaseModel):
    """Request to start design flow."""
    user_id: Optional[str] = None
    initial_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DesignStartResponse(BaseModel):
    """Response from starting design flow."""
    session_id: str
    step: int
    question: str
    options: Optional[List[str]] = None


class DesignStepRequest(BaseModel):
    """Request for next design step."""
    session_id: str
    answer: str
    user_id: Optional[str] = None


class DesignStepResponse(BaseModel):
    """Response from design step."""
    session_id: str
    step: int
    question: Optional[str] = None
    recommendation: Optional[str] = None
    options: Optional[List[str]] = None
    completed: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
