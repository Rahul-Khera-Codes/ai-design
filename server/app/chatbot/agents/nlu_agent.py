"""NLU Agent for intent detection and entity extraction."""

import logging
import json
from typing import Dict, Any, Optional
from app.chatbot.agents.base_agent import BaseAgent
from app.chatbot.schemas import AgentResponse, NLUResult, Intent, Entity
from app.chatbot.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class NLUAgent(BaseAgent):
    """Agent for Natural Language Understanding - intent detection and entity extraction."""
    
    def __init__(self):
        """Initialize NLU Agent."""
        super().__init__("NLUAgent")
        self.llm_service = get_llm_service()
        
        # Intent detection prompt template
        self.intent_prompt_template = """You are an expert at understanding user intent in conversations about dress design and fashion.

Available intents:
- learning: User wants to learn about dresses, fabrics, styles, etc.
- design_help: User wants help designing or customizing a dress
- comparison: User wants to compare different dresses or options
- pricing: User is asking about prices or costs
- care: User is asking about care instructions or maintenance
- general: General conversation or unclear intent

Analyze the following user query and determine:
1. The primary intent (one of the above)
2. Extract relevant entities (dress_type, fabric, color, occasion, body_type, budget, location, weather, style, size)

User query: "{query}"

Respond with valid JSON only in this format:
{{
    "intent": "intent_name",
    "confidence": 0.0-1.0,
    "entities": {{
        "dress_type": "value or null",
        "fabric": "value or null",
        "color": "value or null",
        "occasion": "value or null",
        "body_type": "value or null",
        "budget": "value or null",
        "location": "value or null",
        "weather": "value or null",
        "style": "value or null",
        "size": "value or null"
    }}
}}"""
    
    def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Process user query to detect intent and extract entities.
        
        Args:
            query: User query text
            context: Optional context dictionary
            
        Returns:
            AgentResponse with NLUResult
        """
        try:
            # Format prompt
            prompt = self.intent_prompt_template.format(query=query)
            
            # Generate structured response
            system_prompt = "You are a natural language understanding system. Always respond with valid JSON."
            result = self.llm_service.generate_structured(
                prompt=prompt,
                system_prompt=system_prompt,
                json_schema={
                    "type": "object",
                    "properties": {
                        "intent": {"type": "string"},
                        "confidence": {"type": "number"},
                        "entities": {"type": "object"}
                    },
                    "required": ["intent", "confidence", "entities"]
                }
            )
            
            # Parse intent
            intent_str = result.get("intent", "general").lower()
            try:
                intent = Intent(intent_str)
            except ValueError:
                self.logger.warning(f"Unknown intent: {intent_str}, defaulting to GENERAL")
                intent = Intent.GENERAL
            
            # Parse entities
            entities_dict = result.get("entities", {})
            entities = Entity(**entities_dict)
            
            # Get confidence
            confidence = float(result.get("confidence", 0.7))
            
            # Create NLU result
            nlu_result = NLUResult(
                intent=intent,
                entities=entities,
                confidence=confidence,
                raw_response=json.dumps(result)
            )
            
            # Create response
            response_content = f"Intent: {intent.value}\nConfidence: {confidence:.2f}\nEntities: {entities.dict(exclude_none=True)}"
            
            return self._create_response(
                content=response_content,
                metadata={"nlu_result": nlu_result.dict()},
                confidence=confidence,
                structured_data={"intent": intent.value, "entities": entities.dict(exclude_none=True)}
            )
            
        except Exception as e:
            self.logger.error(f"Error in NLU processing: {e}", exc_info=True)
            return self._handle_error(e, "Failed to understand the query. Please try rephrasing.")
    
    def detect_intent(self, query: str) -> NLUResult:
        """
        Detect intent and extract entities, returning NLUResult directly.
        
        Args:
            query: User query
            
        Returns:
            NLUResult object
        """
        response = self.process(query)
        if response.structured_data:
            intent_str = response.structured_data.get("intent", "general")
            entities_dict = response.structured_data.get("entities", {})
            
            return NLUResult(
                intent=Intent(intent_str),
                entities=Entity(**entities_dict),
                confidence=response.confidence or 0.7
            )
        else:
            # Fallback
            return NLUResult(
                intent=Intent.GENERAL,
                entities=Entity(),
                confidence=0.5
            )
