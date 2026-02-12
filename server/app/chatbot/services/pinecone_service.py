"""Pinecone Service for vector database operations."""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from pinecone import Pinecone, ServerlessSpec
from app.core.config import settings

logger = logging.getLogger(__name__)


class PineconeService:
    """Service for managing Pinecone vector database operations."""
    
    _instance: Optional['PineconeService'] = None
    _client: Optional[Pinecone] = None
    _index: Optional[Any] = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Pinecone service."""
        if not settings.PINECONE_API_KEY:
            logger.warning("Pinecone API key not configured")
            return
        
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Pinecone client and connect to index."""
        if not settings.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY not set in configuration")
        
        try:
            logger.info("Initializing Pinecone client")
            self._client = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # Connect to or create index
            if settings.PINECONE_INDEX_NAME:
                self._connect_to_index()
            else:
                logger.warning("PINECONE_INDEX_NAME not set, index operations disabled")
                
        except Exception as e:
            logger.error(f"Error initializing Pinecone client: {e}")
            raise
    
    def _connect_to_index(self):
        """Connect to existing Pinecone index or create if it doesn't exist."""
        try:
            index_name = settings.PINECONE_INDEX_NAME
            
            # Check if index exists
            existing_indexes = [idx.name for idx in self._client.list_indexes()]
            
            if index_name not in existing_indexes:
                logger.info(f"Index {index_name} not found, creating new index")
                self._create_index(index_name)
            else:
                logger.info(f"Connecting to existing index: {index_name}")
            
            self._index = self._client.Index(index_name)
            logger.info("Successfully connected to Pinecone index")
            
        except Exception as e:
            logger.error(f"Error connecting to Pinecone index: {e}")
            raise
    
    def _create_index(self, index_name: str, dimension: int = None):
        """Create a new Pinecone index."""
        try:
            dimension = dimension or settings.EMBEDDING_DIMENSION
            
            self._client.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=settings.PINECONE_ENVIRONMENT or "us-east-1"
                )
            )
            logger.info(f"Created Pinecone index: {index_name} with dimension {dimension}")
            
        except Exception as e:
            logger.error(f"Error creating Pinecone index: {e}")
            raise
    
    def upsert(
        self,
        vectors: List[Dict[str, Any]],
        namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upsert vectors into Pinecone index.
        
        Args:
            vectors: List of dicts with 'id', 'values', and optional 'metadata'
            namespace: Optional namespace for the vectors
            
        Returns:
            Upsert response from Pinecone
        """
        if self._index is None:
            raise RuntimeError("Pinecone index not initialized")
        
        try:
            # Ensure values are lists (not numpy arrays)
            processed_vectors = []
            for vec in vectors:
                processed_vec = vec.copy()
                if isinstance(processed_vec['values'], np.ndarray):
                    processed_vec['values'] = processed_vec['values'].tolist()
                processed_vectors.append(processed_vec)
            
            response = self._index.upsert(
                vectors=processed_vectors,
                namespace=namespace
            )
            
            logger.info(f"Upserted {len(vectors)} vectors to Pinecone")
            return response
            
        except Exception as e:
            logger.error(f"Error upserting vectors: {e}")
            raise
    
    def query(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Query Pinecone index for similar vectors.
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            namespace: Optional namespace to query
            filter: Optional metadata filter
            include_metadata: Whether to include metadata in results
            
        Returns:
            Query results with matches
        """
        if self._index is None:
            raise RuntimeError("Pinecone index not initialized")
        
        try:
            # Convert numpy array to list
            if isinstance(query_vector, np.ndarray):
                query_vector = query_vector.tolist()
            
            response = self._index.query(
                vector=query_vector,
                top_k=top_k,
                namespace=namespace,
                filter=filter,
                include_metadata=include_metadata
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error querying Pinecone: {e}")
            raise
    
    def delete(
        self,
        ids: Optional[List[str]] = None,
        filter: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None,
        delete_all: bool = False
    ) -> Dict[str, Any]:
        """
        Delete vectors from Pinecone index.
        
        Args:
            ids: List of vector IDs to delete
            filter: Metadata filter for deletion
            namespace: Optional namespace
            delete_all: Delete all vectors (use with caution)
            
        Returns:
            Delete response from Pinecone
        """
        if self._index is None:
            raise RuntimeError("Pinecone index not initialized")
        
        try:
            if delete_all:
                response = self._index.delete(delete_all=True, namespace=namespace)
            elif ids:
                response = self._index.delete(ids=ids, namespace=namespace)
            elif filter:
                response = self._index.delete(filter=filter, namespace=namespace)
            else:
                raise ValueError("Must provide ids, filter, or delete_all=True")
            
            logger.info("Deleted vectors from Pinecone")
            return response
            
        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the Pinecone index."""
        if self._index is None:
            raise RuntimeError("Pinecone index not initialized")
        
        try:
            return self._index.describe_index_stats()
        except Exception as e:
            logger.error(f"Error getting Pinecone stats: {e}")
            raise


def get_pinecone_service() -> PineconeService:
    """Get singleton instance of PineconeService."""
    return PineconeService()
