"""Design Assistant Agent - Main orchestrator for multi-agent system using LangChain."""

import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field  # Always import from pydantic as base
try:
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain.tools import StructuredTool
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    # Use langchain's pydantic if available, otherwise use standard pydantic
    try:
        from langchain_core.pydantic_v1 import BaseModel as LangChainBaseModel, Field as LangChainField
        # Optionally use LangChain's pydantic for compatibility
        # BaseModel = LangChainBaseModel
        # Field = LangChainField
    except ImportError:
        pass
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain.agents import AgentExecutor
        from langchain.agents.react.agent import create_react_agent
        from langchain.tools import StructuredTool
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False
from app.chatbot.agents.base_agent import BaseAgent
from app.chatbot.agents.nlu_agent import NLUAgent
from app.chatbot.agents.sql_agent import SQLAgent
from app.chatbot.agents.rag_agent import RAGAgent
from app.chatbot.schemas import (
    AgentResponse, Intent, DesignContext, NLUResult
)
from app.chatbot.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class NLUInput(BaseModel):
    """Input schema for NLU tool."""
    query: str = Field(description="User query to analyze for intent and entities")


class SQLInput(BaseModel):
    """Input schema for SQL tool."""
    query: str = Field(description="Natural language query to convert to SQL and execute")


class RAGInput(BaseModel):
    """Input schema for RAG tool."""
    query: str = Field(description="Query to search knowledge base and generate answer")
    filter_type: Optional[str] = Field(None, description="Optional document type filter (faqs, manuals, guides)")


class DesignAgent(BaseAgent):
    """Main orchestrator agent that coordinates other agents using LangChain."""
    
    def __init__(self):
        """Initialize Design Agent with sub-agents and LangChain tools."""
        super().__init__("DesignAgent")
        self.nlu_agent = NLUAgent()
        self.sql_agent = SQLAgent()
        self.rag_agent = RAGAgent()
        self.llm_service = get_llm_service()
        self._agent_executor = None
        self._initialize_langchain_agent()
    
    def _initialize_langchain_agent(self):
        """Initialize LangChain agent executor with tools."""
        if not LANGCHAIN_AVAILABLE:
            self.logger.warning("LangChain not available, using manual orchestration")
            return
        
        try:
            # Create LangChain tools for each agent
            nlu_tool = StructuredTool.from_function(
                func=self._nlu_tool_func,
                name="detect_intent",
                description="Analyze user query to detect intent (learning, design_help, comparison, pricing, care) and extract entities (dress_type, fabric, color, occasion, body_type, budget, location, weather)",
                args_schema=NLUInput
            )
            
            sql_tool = StructuredTool.from_function(
                func=self._sql_tool_func,
                name="query_database",
                description="Query product database using natural language. Converts questions to SQL and returns product information, pricing, availability, etc.",
                args_schema=SQLInput
            )
            
            rag_tool = StructuredTool.from_function(
                func=self._rag_tool_func,
                name="search_knowledge_base",
                description="Search knowledge base (FAQs, manuals, guides) and generate answers based on retrieved documents. Use for learning questions, design guidelines, care instructions.",
                args_schema=RAGInput
            )
            
            tools = [nlu_tool, sql_tool, rag_tool]
            
            # Create prompt template for the agent
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a helpful fashion design assistant that helps users design dresses and answer questions about fashion.

You have access to three tools:
1. detect_intent - Analyze user queries to understand intent and extract entities
2. query_database - Query product database for dresses, fabrics, pricing, availability
3. search_knowledge_base - Search knowledge base for FAQs, design guidelines, care instructions

Your workflow:
1. First, use detect_intent to understand what the user wants
2. Based on intent:
   - For design help: Use both query_database AND search_knowledge_base, then synthesize recommendations
   - For learning questions: Use search_knowledge_base
   - For comparison/pricing: Use query_database
   - For care questions: Use search_knowledge_base with filter_type="manuals"
3. Provide clear, helpful, and actionable responses

Always explain your reasoning and cite sources when available."""),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            # Create LangChain LLM wrapper for our HuggingFace model
            try:
                from langchain_core.language_models.llms import BaseLLM
                
                class HuggingFaceLLMWrapper(BaseLLM):
                    def __init__(self, llm_service):
                        super().__init__()
                        self.llm_service = llm_service
                    
                    def _llm_type(self) -> str:
                        return "huggingface"
                    
                    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
                        return self.llm_service.generate(
                            prompt=prompt,
                            max_tokens=kwargs.get("max_tokens", 512),
                            temperature=kwargs.get("temperature", 0.7),
                            stop_sequences=stop
                        )
                
                llm = HuggingFaceLLMWrapper(self.llm_service)
            except ImportError:
                # Fallback: use a simple callable wrapper
                class SimpleLLMWrapper:
                    def __init__(self, llm_service):
                        self.llm_service = llm_service
                    
                    def __call__(self, prompt: str, **kwargs) -> str:
                        return self.llm_service.generate(
                            prompt=prompt,
                            max_tokens=kwargs.get("max_tokens", 512),
                            temperature=kwargs.get("temperature", 0.7)
                        )
                
                llm = SimpleLLMWrapper(self.llm_service)
            
            # Try to create agent (may fail with custom LLM, that's okay)
            try:
                agent = create_react_agent(llm, tools, prompt)
                
                # Create agent executor
                self._agent_executor = AgentExecutor(
                    agent=agent,
                    tools=tools,
                    verbose=True,
                    handle_parsing_errors=True,
                    max_iterations=5
                )
            except Exception as e:
                self.logger.warning(f"Could not create LangChain agent executor: {e}. Using manual orchestration.")
                self._agent_executor = None
            
            self.logger.info("LangChain agent executor initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing LangChain agent: {e}", exc_info=True)
            # Fallback: continue without LangChain agent executor
            self._agent_executor = None
    
    def _nlu_tool_func(self, query: str) -> str:
        """Tool function for NLU agent."""
        try:
            nlu_result = self.nlu_agent.detect_intent(query)
            return f"Intent: {nlu_result.intent.value}, Confidence: {nlu_result.confidence:.2f}, Entities: {nlu_result.entities.dict(exclude_none=True)}"
        except Exception as e:
            return f"Error in intent detection: {str(e)}"
    
    def _sql_tool_func(self, query: str) -> str:
        """Tool function for SQL agent."""
        try:
            response = self.sql_agent.process(query)
            results = response.structured_data.get("results", []) if response.structured_data else []
            return f"Database query results: {results[:3]}"  # Return first 3 results
        except Exception as e:
            return f"Error querying database: {str(e)}"
    
    def _rag_tool_func(self, query: str, filter_type: Optional[str] = None) -> str:
        """Tool function for RAG agent."""
        try:
            response = self.rag_agent.process(query, filter_by_type=filter_type)
            return response.content
        except Exception as e:
            return f"Error searching knowledge base: {str(e)}"
    
    def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Process query by orchestrating appropriate agents using LangChain.
        
        Args:
            query: User query
            context: Optional context including DesignContext
            
        Returns:
            AgentResponse with synthesized result
        """
        try:
            # Use LangChain agent executor if available
            if self._agent_executor:
                result = self._agent_executor.invoke({"input": query})
                return self._create_response(
                    content=result.get("output", "I couldn't process your request."),
                    metadata={"langchain_used": True, "steps": result.get("intermediate_steps", [])},
                    confidence=0.8
                )
            
            # Fallback to manual orchestration if LangChain not available
            return self._process_manual(query, context)
            
        except Exception as e:
            self.logger.error(f"Error in Design Agent processing: {e}", exc_info=True)
            # Fallback to manual processing
            return self._process_manual(query, context)
    
    def _process_manual(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Manual orchestration fallback (original implementation)."""
        try:
            # Extract design context if provided
            design_context = None
            if context and "design_context" in context:
                design_context = context["design_context"]
            
            # Step 1: NLU - Understand intent and extract entities
            nlu_result = self.nlu_agent.detect_intent(query)
            
            # Step 2: Route to appropriate agents based on intent
            if nlu_result.intent == Intent.DESIGN_HELP:
                return self._handle_design_help(query, nlu_result, design_context)
            elif nlu_result.intent == Intent.LEARNING:
                return self._handle_learning(query, nlu_result, design_context)
            elif nlu_result.intent == Intent.COMPARISON or nlu_result.intent == Intent.PRICING:
                return self._handle_comparison_pricing(query, nlu_result, design_context)
            elif nlu_result.intent == Intent.CARE:
                return self._handle_care(query, nlu_result, design_context)
            else:
                return self._handle_general(query, nlu_result, design_context)
                
        except Exception as e:
            self.logger.error(f"Error in manual processing: {e}", exc_info=True)
            return self._handle_error(e, "I encountered an error processing your request. Please try again.")
    
    def _handle_design_help(
        self,
        query: str,
        nlu_result: NLUResult,
        design_context: Optional[DesignContext]
    ) -> AgentResponse:
        """Handle design help requests."""
        try:
            # Get product information from SQL agent
            sql_response = self.sql_agent.process(query)
            sql_data = sql_response.structured_data or {}
            
            # Get design guidelines from RAG agent
            rag_response = self.rag_agent.process(query, filter_by_type="guides")
            rag_data = rag_response.structured_data or {}
            
            # Synthesize recommendation
            synthesis_prompt = f"""You are a fashion design assistant helping a user design a dress.

User Query: {query}
Extracted Information: {nlu_result.entities.dict(exclude_none=True)}
Product Data: {sql_data.get('results', [])}
Design Guidelines: {rag_data.get('answer', '')}

Provide a comprehensive design recommendation that:
1. Addresses the user's specific needs
2. Incorporates the product information
3. Follows design best practices
4. Is practical and actionable

Recommendation:"""
            
            recommendation = self.llm_service.generate(
                prompt=synthesis_prompt,
                max_tokens=512,
                temperature=0.7,
                system_prompt="You are an expert fashion design consultant."
            )
            
            # Combine sources
            sources = []
            if sql_response.sources:
                sources.extend(sql_response.sources)
            if rag_response.sources:
                sources.extend(rag_response.sources)
            
            return self._create_response(
                content=recommendation,
                metadata={
                    "intent": nlu_result.intent.value,
                    "entities": nlu_result.entities.dict(exclude_none=True),
                    "sql_results": sql_data.get('results', []),
                    "rag_sources": rag_data.get('sources', [])
                },
                confidence=(nlu_result.confidence + rag_response.confidence) / 2,
                structured_data={"recommendation": recommendation},
                sources=list(set(sources))
            )
            
        except Exception as e:
            self.logger.error(f"Error handling design help: {e}")
            # Fallback to RAG only
            return self.rag_agent.process(query)
    
    def _handle_learning(
        self,
        query: str,
        nlu_result: NLUResult,
        design_context: Optional[DesignContext]
    ) -> AgentResponse:
        """Handle learning/educational queries."""
        # Use RAG agent for learning queries
        return self.rag_agent.process(query, filter_by_type="faqs")
    
    def _handle_comparison_pricing(
        self,
        query: str,
        nlu_result: NLUResult,
        design_context: Optional[DesignContext]
    ) -> AgentResponse:
        """Handle comparison and pricing queries."""
        # Use SQL agent for product data
        sql_response = self.sql_agent.process(query)
        
        # Enhance with RAG if needed
        if sql_response.confidence and sql_response.confidence < 0.7:
            rag_response = self.rag_agent.process(query, filter_by_type="guides")
            # Combine responses
            combined_content = f"{sql_response.content}\n\nAdditional Information:\n{rag_response.content}"
            
            return self._create_response(
                content=combined_content,
                metadata={**sql_response.metadata, **rag_response.metadata},
                confidence=max(sql_response.confidence or 0, rag_response.confidence or 0),
                sources=rag_response.sources
            )
        
        return sql_response
    
    def _handle_care(
        self,
        query: str,
        nlu_result: NLUResult,
        design_context: Optional[DesignContext]
    ) -> AgentResponse:
        """Handle care/maintenance queries."""
        # Use RAG agent for care instructions
        return self.rag_agent.process(query, filter_by_type="manuals")
    
    def _handle_general(
        self,
        query: str,
        nlu_result: NLUResult,
        design_context: Optional[DesignContext]
    ) -> AgentResponse:
        """Handle general queries."""
        # Try RAG first, fallback to SQL if needed
        rag_response = self.rag_agent.process(query)
        
        if rag_response.confidence and rag_response.confidence > 0.6:
            return rag_response
        
        # Try SQL as fallback
        try:
            return self.sql_agent.process(query)
        except:
            return rag_response
    
    def start_design_flow(
        self,
        user_id: Optional[str] = None,
        initial_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start a new design assistance flow.
        
        Args:
            user_id: Optional user ID
            initial_preferences: Optional initial preferences
            
        Returns:
            Dictionary with session_id, step, and first question
        """
        import uuid
        
        session_id = str(uuid.uuid4())
        design_context = DesignContext(
            user_id=user_id,
            session_id=session_id,
            preferences=initial_preferences or {},
            current_step=1
        )
        
        # First question
        question = "What occasion are you designing this dress for?"
        options = ["Wedding", "Party", "Office", "Casual", "Formal Event", "Other"]
        
        return {
            "session_id": session_id,
            "step": 1,
            "question": question,
            "options": options,
            "design_context": design_context
        }
    
    def process_design_step(
        self,
        session_id: str,
        answer: str,
        design_context: Optional[DesignContext]
    ) -> Dict[str, Any]:
        """
        Process a step in the design flow.
        
        Args:
            session_id: Session ID
            answer: User's answer to current step
            design_context: Design context
            
        Returns:
            Dictionary with next step or recommendation
        """
        if design_context is None:
            raise ValueError("Design context is required")
        
        # Update collected info
        step = design_context.current_step or 1
        
        if step == 1:
            design_context.update_collected_info("occasion", answer)
            design_context.current_step = 2
            return {
                "session_id": session_id,
                "step": 2,
                "question": "What is your preferred fabric?",
                "options": ["Cotton", "Silk", "Linen", "Polyester", "Wool", "Other"],
                "completed": False
            }
        elif step == 2:
            design_context.update_collected_info("fabric", answer)
            design_context.current_step = 3
            return {
                "session_id": session_id,
                "step": 3,
                "question": "What is your preferred color?",
                "options": None,  # Open-ended
                "completed": False
            }
        elif step == 3:
            design_context.update_collected_info("color", answer)
            # Generate recommendation
            recommendation = self._generate_design_recommendation(design_context)
            
            return {
                "session_id": session_id,
                "step": 4,
                "recommendation": recommendation,
                "completed": True
            }
        
        return {
            "session_id": session_id,
            "step": step,
            "completed": True
        }
    
    def _generate_design_recommendation(self, design_context: DesignContext) -> str:
        """Generate design recommendation based on collected information."""
        collected = design_context.collected_info
        
        prompt = f"""Based on the following information, provide a detailed dress design recommendation:

Occasion: {collected.get('occasion', 'Not specified')}
Fabric: {collected.get('fabric', 'Not specified')}
Color: {collected.get('color', 'Not specified')}

Provide a comprehensive recommendation including:
1. Specific dress style suggestions
2. Design elements that would work well
3. Practical considerations
4. Any additional tips

Recommendation:"""
        
        return self.llm_service.generate(
            prompt=prompt,
            max_tokens=512,
            temperature=0.7,
            system_prompt="You are an expert fashion design consultant."
        )
