"""Base agent class for all chatbot agents."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.chatbot.schemas import AgentResponse

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all chatbot agents."""
    
    def __init__(self, name: str):
        """
        Initialize base agent.
        
        Args:
            name: Name of the agent
        """
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Process a query and return a response.
        
        Args:
            query: User query
            context: Optional context dictionary
            
        Returns:
            AgentResponse with processed result
        """
        pass
    
    def _create_response(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        structured_data: Optional[Dict[str, Any]] = None,
        sources: Optional[list] = None
    ) -> AgentResponse:
        """
        Create a standardized agent response.
        
        Args:
            content: Response content
            metadata: Optional metadata
            confidence: Optional confidence score
            structured_data: Optional structured data
            sources: Optional list of sources
            
        Returns:
            AgentResponse object
        """
        return AgentResponse(
            content=content,
            agent_name=self.name,
            metadata=metadata or {},
            confidence=confidence,
            structured_data=structured_data,
            sources=sources
        )
    
    def _handle_error(self, error: Exception, fallback_message: str = None) -> AgentResponse:
        """
        Handle errors gracefully.
        
        Args:
            error: Exception that occurred
            fallback_message: Optional fallback message
            
        Returns:
            AgentResponse with error information
        """
        self.logger.error(f"Error in {self.name}: {error}", exc_info=True)
        
        message = fallback_message or f"An error occurred while processing your request: {str(error)}"
        
        return self._create_response(
            content=message,
            metadata={"error": True, "error_type": type(error).__name__},
            confidence=0.0
        )
