"""Factory for creating and managing agent instances."""

import logging
from typing import Dict, Optional
from app.chatbot.agents.base_agent import BaseAgent
from app.chatbot.agents.nlu_agent import NLUAgent
from app.chatbot.agents.sql_agent import SQLAgent
from app.chatbot.agents.rag_agent import RAGAgent
from app.chatbot.agents.design_agent import DesignAgent

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for creating and managing agent instances."""
    
    _instance: Optional['AgentFactory'] = None
    _agents: Dict[str, BaseAgent] = {}
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize agent factory."""
        if not self._agents:
            self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all agents (lazy loading)."""
        logger.info("Initializing agents...")
        # Agents will be created on first access
        pass
    
    def get_nlu_agent(self) -> NLUAgent:
        """Get NLU agent instance."""
        if "nlu" not in self._agents:
            logger.info("Creating NLU agent...")
            self._agents["nlu"] = NLUAgent()
        return self._agents["nlu"]
    
    def get_sql_agent(self) -> SQLAgent:
        """Get SQL agent instance."""
        if "sql" not in self._agents:
            logger.info("Creating SQL agent...")
            self._agents["sql"] = SQLAgent()
        return self._agents["sql"]
    
    def get_rag_agent(self) -> RAGAgent:
        """Get RAG agent instance."""
        if "rag" not in self._agents:
            logger.info("Creating RAG agent...")
            self._agents["rag"] = RAGAgent()
        return self._agents["rag"]
    
    def get_design_agent(self) -> DesignAgent:
        """Get Design Assistant agent instance."""
        if "design" not in self._agents:
            logger.info("Creating Design Assistant agent...")
            self._agents["design"] = DesignAgent()
        return self._agents["design"]
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """
        Get agent by name.
        
        Args:
            agent_name: Name of the agent (nlu, sql, rag, design)
            
        Returns:
            Agent instance or None if not found
        """
        agent_map = {
            "nlu": self.get_nlu_agent,
            "sql": self.get_sql_agent,
            "rag": self.get_rag_agent,
            "design": self.get_design_agent
        }
        
        if agent_name.lower() in agent_map:
            return agent_map[agent_name.lower()]()
        
        logger.warning(f"Unknown agent name: {agent_name}")
        return None
    
    def reset_agents(self):
        """Reset all agents (useful for testing)."""
        self._agents.clear()
        logger.info("All agents reset")


def get_agent_factory() -> AgentFactory:
    """Get singleton instance of AgentFactory."""
    return AgentFactory()
