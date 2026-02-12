"""Utility for PostgreSQL schema introspection."""

import logging
from typing import Dict, List, Any, Optional
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from app.core.database import engine

logger = logging.getLogger(__name__)


class DatabaseSchema:
    """Utility class for database schema introspection."""
    
    def __init__(self, db_engine: Engine = None):
        """
        Initialize database schema utility.
        
        Args:
            db_engine: SQLAlchemy engine (defaults to app engine)
        """
        self.engine = db_engine or engine
        self.inspector = inspect(self.engine)
    
    def get_table_names(self) -> List[str]:
        """Get list of all table names in the database."""
        try:
            return self.inspector.get_table_names()
        except Exception as e:
            logger.error(f"Error getting table names: {e}")
            return []
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Get schema information for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with table schema information
        """
        try:
            columns = self.inspector.get_columns(table_name)
            primary_keys = self.inspector.get_primary_keys(table_name)
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            indexes = self.inspector.get_indexes(table_name)
            
            return {
                "table_name": table_name,
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col.get("nullable", True),
                        "default": str(col.get("default", ""))
                    }
                    for col in columns
                ],
                "primary_keys": primary_keys,
                "foreign_keys": [
                    {
                        "constrained_columns": fk["constrained_columns"],
                        "referred_table": fk["referred_table"],
                        "referred_columns": fk["referred_columns"]
                    }
                    for fk in foreign_keys
                ],
                "indexes": [
                    {
                        "name": idx["name"],
                        "columns": idx["column_names"],
                        "unique": idx.get("unique", False)
                    }
                    for idx in indexes
                ]
            }
        except Exception as e:
            logger.error(f"Error getting schema for table {table_name}: {e}")
            return {}
    
    def get_all_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        Get schema information for all tables.
        
        Returns:
            Dictionary mapping table names to their schemas
        """
        schemas = {}
        for table_name in self.get_table_names():
            schemas[table_name] = self.get_table_schema(table_name)
        return schemas
    
    def get_schema_description(self, table_name: Optional[str] = None) -> str:
        """
        Get a natural language description of the database schema.
        
        Args:
            table_name: Optional specific table name, otherwise describes all tables
            
        Returns:
            Natural language schema description
        """
        if table_name:
            schema = self.get_table_schema(table_name)
            if not schema:
                return f"Table {table_name} not found."
            
            desc = f"Table '{schema['table_name']}':\n"
            desc += "Columns:\n"
            for col in schema["columns"]:
                nullable = "nullable" if col["nullable"] else "not null"
                desc += f"  - {col['name']} ({col['type']}, {nullable})\n"
            
            if schema["primary_keys"]:
                desc += f"Primary keys: {', '.join(schema['primary_keys'])}\n"
            
            if schema["foreign_keys"]:
                desc += "Foreign keys:\n"
                for fk in schema["foreign_keys"]:
                    desc += f"  - {', '.join(fk['constrained_columns'])} -> {fk['referred_table']}.{', '.join(fk['referred_columns'])}\n"
            
            return desc
        else:
            # Describe all tables
            schemas = self.get_all_schemas()
            desc = "Database Schema:\n\n"
            for table_name, schema in schemas.items():
                desc += self.get_schema_description(table_name) + "\n"
            return desc
    
    def get_sample_data(self, table_name: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Get sample data from a table.
        
        Args:
            table_name: Name of the table
            limit: Number of sample rows to return
            
        Returns:
            List of dictionaries with sample data
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT {limit}"))
                columns = result.keys()
                rows = result.fetchall()
                
                return [
                    {col: val for col, val in zip(columns, row)}
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting sample data from {table_name}: {e}")
            return []


def get_database_schema() -> DatabaseSchema:
    """Get database schema utility instance."""
    return DatabaseSchema()
