"""RAG Agent for document retrieval and answer generation."""

import logging
from typing import Dict, Any, Optional, List
from app.chatbot.agents.base_agent import BaseAgent
from app.chatbot.schemas import AgentResponse, RAGResult
from app.chatbot.services.llm_service import get_llm_service
from app.chatbot.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)


class RAGAgent(BaseAgent):
    """Agent for Retrieval Augmented Generation - document retrieval and answer synthesis."""
    
    def __init__(self):
        """Initialize RAG Agent."""
        super().__init__("RAGAgent")
        self.llm_service = get_llm_service()
        self.vector_store = get_vector_store()
        
        # RAG prompt template
        self.rag_prompt_template = """You are a helpful assistant that answers questions based on the provided context.

Context from knowledge base:
{context}

User Question: {query}

Instructions:
1. Answer the question using only the information provided in the context
2. If the context doesn't contain enough information, say so clearly
3. Cite sources when referencing specific information
4. Be concise and accurate
5. If asked about dress design, provide practical and helpful guidance

Answer:"""
    
    def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        filter_by_type: Optional[str] = None
    ) -> AgentResponse:
        """
        Process query using RAG pipeline.
        
        Args:
            query: User query
            context: Optional context dictionary
            top_k: Number of documents to retrieve
            filter_by_type: Optional document type filter
            
        Returns:
            AgentResponse with RAGResult
        """
        try:
            # Build filter if needed
            filter_dict = None
            if filter_by_type:
                filter_dict = {"type": filter_by_type}
            
            # Retrieve relevant documents
            retrieved_chunks = self.vector_store.query(
                query_text=query,
                top_k=top_k,
                filter=filter_dict
            )
            
            if not retrieved_chunks:
                return self._create_response(
                    content="I couldn't find relevant information in the knowledge base. Please try rephrasing your question or ask about a different topic.",
                    metadata={"retrieved_chunks": 0},
                    confidence=0.0
                )
            
            # Combine context chunks
            context_text = "\n\n".join([
                f"[Source: {chunk['source']}]\n{chunk['content']}"
                for chunk in retrieved_chunks
            ])
            
            # Calculate average confidence from retrieved chunks
            avg_confidence = sum(chunk.get('score', 0.5) for chunk in retrieved_chunks) / len(retrieved_chunks)
            
            # Generate answer using LLM
            prompt = self.rag_prompt_template.format(
                context=context_text,
                query=query
            )
            
            answer = self.llm_service.generate(
                prompt=prompt,
                max_tokens=512,
                temperature=0.7,
                system_prompt="You are a helpful assistant that provides accurate information based on context."
            )
            
            # Extract sources
            sources = list(set([chunk['source'] for chunk in retrieved_chunks]))
            
            # Create RAG result
            rag_result = RAGResult(
                answer=answer,
                context_chunks=retrieved_chunks,
                sources=sources,
                confidence=float(avg_confidence),
                metadata={
                    "retrieved_count": len(retrieved_chunks),
                    "filter_applied": filter_by_type is not None
                }
            )
            
            # Format response with sources
            response_content = answer
            if sources:
                response_content += f"\n\nSources: {', '.join(sources[:3])}"  # Show first 3 sources
            
            return self._create_response(
                content=response_content,
                metadata={"rag_result": rag_result.dict()},
                confidence=rag_result.confidence,
                structured_data={"answer": answer, "sources": sources},
                sources=sources
            )
            
        except Exception as e:
            self.logger.error(f"Error in RAG processing: {e}", exc_info=True)
            return self._handle_error(e, "Failed to retrieve information. Please try again.")
    
    def retrieve_only(
        self,
        query: str,
        top_k: int = 5,
        filter_by_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents without generating answer.
        
        Args:
            query: Search query
            top_k: Number of results
            filter_by_type: Optional document type filter
            
        Returns:
            List of retrieved chunks
        """
        try:
            filter_dict = None
            if filter_by_type:
                filter_dict = {"type": filter_by_type}
            
            return self.vector_store.query(
                query_text=query,
                top_k=top_k,
                filter=filter_dict
            )
        except Exception as e:
            self.logger.error(f"Error retrieving documents: {e}")
            return []
