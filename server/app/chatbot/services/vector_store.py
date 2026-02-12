"""High-level vector store interface for document ingestion and querying."""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from app.chatbot.services.embedding_service import get_embedding_service
from app.chatbot.services.pinecone_service import get_pinecone_service
from app.chatbot.services.document_loader import get_document_loader

logger = logging.getLogger(__name__)


class VectorStore:
    """High-level interface for vector store operations."""
    
    def __init__(self):
        """Initialize vector store with required services."""
        self.embedding_service = get_embedding_service()
        self.pinecone_service = get_pinecone_service()
        self.document_loader = get_document_loader()
    
    def ingest_documents(
        self,
        subdirectory: Optional[str] = None,
        namespace: Optional[str] = None,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Ingest documents from directory into vector store.
        
        Args:
            subdirectory: Subdirectory to load documents from
            namespace: Optional Pinecone namespace
            batch_size: Batch size for upserting vectors
            
        Returns:
            Summary of ingestion process
        """
        try:
            # Load documents
            documents = self.document_loader.load_documents_from_directory(subdirectory)
            
            if not documents:
                logger.warning("No documents found to ingest")
                return {"status": "no_documents", "count": 0}
            
            # Process documents into chunks
            chunks = self.document_loader.process_documents(documents)
            
            # Generate embeddings for chunks
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            chunk_texts = [chunk['content'] for chunk in chunks]
            embeddings = self.embedding_service.encode(chunk_texts, batch_size=batch_size)
            
            # Prepare vectors for Pinecone
            vectors = []
            for idx, chunk in enumerate(chunks):
                vectors.append({
                    'id': chunk['id'],
                    'values': embeddings[idx],
                    'metadata': {
                        'content': chunk['content'],
                        'source': chunk['source'],
                        'type': chunk['type'],
                        **chunk['metadata']
                    }
                })
            
            # Upsert in batches
            total_upserted = 0
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.pinecone_service.upsert(batch, namespace=namespace)
                total_upserted += len(batch)
                logger.info(f"Upserted batch {i // batch_size + 1}: {len(batch)} vectors")
            
            logger.info(f"Successfully ingested {total_upserted} vectors")
            return {
                "status": "success",
                "documents_processed": len(documents),
                "chunks_created": len(chunks),
                "vectors_upserted": total_upserted
            }
            
        except Exception as e:
            logger.error(f"Error ingesting documents: {e}")
            raise
    
    def query(
        self,
        query_text: str,
        top_k: int = 5,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query vector store for similar documents.
        
        Args:
            query_text: Query text
            top_k: Number of results to return
            namespace: Optional Pinecone namespace
            filter: Optional metadata filter
            
        Returns:
            List of matching chunks with scores and metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.encode(query_text)
            
            # Query Pinecone
            results = self.pinecone_service.query(
                query_vector=query_embedding[0],  # Get first (and only) embedding
                top_k=top_k,
                namespace=namespace,
                filter=filter,
                include_metadata=True
            )
            
            # Format results
            matches = []
            for match in results.get('matches', []):
                matches.append({
                    'id': match['id'],
                    'score': match['score'],
                    'content': match['metadata'].get('content', ''),
                    'source': match['metadata'].get('source', ''),
                    'type': match['metadata'].get('type', ''),
                    'metadata': match['metadata']
                })
            
            return matches
            
        except Exception as e:
            logger.error(f"Error querying vector store: {e}")
            raise
    
    def delete_documents(
        self,
        source: Optional[str] = None,
        doc_type: Optional[str] = None,
        namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete documents from vector store.
        
        Args:
            source: Delete by source path
            doc_type: Delete by document type
            namespace: Optional Pinecone namespace
            
        Returns:
            Deletion response
        """
        try:
            filter_dict = {}
            if source:
                filter_dict['source'] = source
            if doc_type:
                filter_dict['type'] = doc_type
            
            if not filter_dict:
                raise ValueError("Must provide source or doc_type for deletion")
            
            response = self.pinecone_service.delete(
                filter=filter_dict,
                namespace=namespace
            )
            
            logger.info(f"Deleted documents matching filter: {filter_dict}")
            return response
            
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        try:
            return self.pinecone_service.get_stats()
        except Exception as e:
            logger.error(f"Error getting vector store stats: {e}")
            raise


def get_vector_store() -> VectorStore:
    """Get vector store instance."""
    return VectorStore()
