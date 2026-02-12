"""SQL Agent for text-to-SQL conversion and database queries."""

import logging
import json
from typing import Dict, Any, Optional, List
from sqlalchemy import text
from app.chatbot.agents.base_agent import BaseAgent
from app.chatbot.schemas import AgentResponse, SQLQueryResult
from app.chatbot.services.llm_service import get_llm_service
from app.chatbot.services.database_schema import get_database_schema
from app.core.database import engine
from app.core.config import settings

logger = logging.getLogger(__name__)


class SQLAgent(BaseAgent):
    """Agent for converting natural language to SQL queries and executing them."""
    
    def __init__(self):
        """Initialize SQL Agent."""
        super().__init__("SQLAgent")
        self.llm_service = get_llm_service()
        self.db_schema = get_database_schema()
        self._agent = None
        self._db = None
    
    def _initialize_agent(self):
        """Initialize SQL agent (placeholder for future enhancements)."""
        if self._agent is not None:
            return
        
        try:
            # Custom SQL generation implementation using direct LLM calls
            # No LangChain dependencies needed for this implementation
            self.logger.info("SQL Agent initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing SQL agent: {e}")
            raise
    
    def _generate_sql(
        self,
        query: str,
        schema_description: str
    ) -> str:
        """
        Generate SQL query from natural language using LLM.
        
        Args:
            query: Natural language query
            schema_description: Database schema description
            
        Returns:
            SQL query string
        """
        prompt = f"""You are an expert SQL query generator. Given a database schema and a user question, generate a valid PostgreSQL SQL query.

Database Schema:
{schema_description}

User Question: {query}

Rules:
1. Only generate the SQL query, no explanations
2. Use parameterized queries with placeholders if needed
3. Use proper SQL syntax for PostgreSQL
4. Include appropriate JOINs if multiple tables are needed
5. Use LIMIT if the query might return many rows

Generate the SQL query:"""
        
        try:
            sql_query = self.llm_service.generate(
                prompt=prompt,
                max_tokens=256,
                temperature=0.1,  # Low temperature for deterministic SQL
                system_prompt="You are a SQL expert. Always generate valid PostgreSQL queries."
            )
            
            # Clean up the SQL query
            sql_query = sql_query.strip()
            
            # Remove markdown code blocks if present
            if sql_query.startswith("```"):
                lines = sql_query.split("\n")
                sql_query = "\n".join([line for line in lines if not line.strip().startswith("```")])
            
            # Extract SQL if wrapped in explanations
            if "SELECT" in sql_query.upper():
                # Find the SELECT statement
                select_idx = sql_query.upper().find("SELECT")
                sql_query = sql_query[select_idx:]
            
            return sql_query
            
        except Exception as e:
            self.logger.error(f"Error generating SQL: {e}")
            raise
    
    def _execute_sql(self, sql_query: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query safely.
        
        Args:
            sql_query: SQL query string
            
        Returns:
            List of result dictionaries
        """
        try:
            # Basic safety check - prevent dangerous operations
            sql_upper = sql_query.upper().strip()
            dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE"]
            
            # Allow SELECT only for now (can be extended)
            if not sql_upper.startswith("SELECT"):
                raise ValueError("Only SELECT queries are allowed")
            
            # Check for dangerous patterns
            for keyword in dangerous_keywords:
                if keyword in sql_upper and keyword != "SELECT":
                    raise ValueError(f"Operation {keyword} is not allowed")
            
            # Execute query
            with engine.connect() as conn:
                result = conn.execute(text(sql_query))
                columns = result.keys()
                rows = result.fetchall()
                
                # Convert to list of dictionaries
                results = [
                    {col: str(val) if val is not None else None for col, val in zip(columns, row)}
                    for row in rows
                ]
                
                return results
                
        except Exception as e:
            self.logger.error(f"Error executing SQL: {e}")
            raise
    
    def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Process natural language query and generate/execute SQL.
        
        Args:
            query: Natural language query
            context: Optional context dictionary
            
        Returns:
            AgentResponse with SQLQueryResult
        """
        try:
            self._initialize_agent()
            
            # Get schema description
            schema_desc = self.db_schema.get_schema_description()
            
            # Generate SQL query
            sql_query = self._generate_sql(query, schema_desc)
            
            # Execute query
            results = self._execute_sql(sql_query)
            
            # Create SQL query result
            sql_result = SQLQueryResult(
                query=sql_query,
                results=results,
                metadata={
                    "row_count": len(results),
                    "schema_used": True
                },
                success=True
            )
            
            # Format response
            if results:
                response_content = f"Query executed successfully. Found {len(results)} result(s).\n\n"
                response_content += f"SQL: {sql_query}\n\n"
                response_content += f"Results: {json.dumps(results[:5], indent=2)}"  # Show first 5 results
            else:
                response_content = f"Query executed successfully but returned no results.\n\nSQL: {sql_query}"
            
            return self._create_response(
                content=response_content,
                metadata={"sql_result": sql_result.dict()},
                confidence=0.9,
                structured_data={"query": sql_query, "results": results}
            )
            
        except Exception as e:
            self.logger.error(f"Error in SQL processing: {e}", exc_info=True)
            
            error_msg = f"Failed to generate or execute SQL query: {str(e)}"
            return self._create_response(
                content=error_msg,
                metadata={"error": True, "error_type": type(e).__name__},
                confidence=0.0,
                structured_data={"query": "", "results": [], "error": str(e)}
            )
