"""Document loader for processing and chunking documents."""

import logging
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Service for loading and chunking documents."""
    
    def __init__(self, documents_dir: str = "data/documents"):
        """
        Initialize document loader.
        
        Args:
            documents_dir: Base directory containing documents
        """
        self.documents_dir = Path(documents_dir)
        if not self.documents_dir.exists():
            logger.warning(f"Documents directory does not exist: {documents_dir}")
            self.documents_dir.mkdir(parents=True, exist_ok=True)
    
    def load_text_file(self, file_path: str) -> str:
        """
        Load text content from a file.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            File content as string
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
            raise
    
    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separator: str = "\n\n"
    ) -> List[str]:
        """
        Split text into chunks.
        
        Args:
            text: Text to chunk
            chunk_size: Maximum size of each chunk (in characters)
            chunk_overlap: Overlap between chunks
            separator: Separator to use for splitting
            
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        # Split by separator first
        sections = text.split(separator)
        
        current_chunk = ""
        for section in sections:
            # If adding this section would exceed chunk size, save current chunk
            if len(current_chunk) + len(section) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap
                overlap_text = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else current_chunk
                current_chunk = overlap_text + separator + section
            else:
                current_chunk += (separator if current_chunk else "") + section
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def load_documents_from_directory(
        self,
        subdirectory: Optional[str] = None,
        file_extensions: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Load all documents from a directory.
        
        Args:
            subdirectory: Subdirectory within documents_dir (e.g., 'faqs', 'manuals')
            file_extensions: List of file extensions to load (default: ['.txt', '.md'])
            
        Returns:
            List of document dictionaries with 'content', 'source', 'type', 'metadata'
        """
        if file_extensions is None:
            file_extensions = ['.txt', '.md']
        
        documents = []
        target_dir = self.documents_dir / subdirectory if subdirectory else self.documents_dir
        
        if not target_dir.exists():
            logger.warning(f"Directory does not exist: {target_dir}")
            return documents
        
        for file_path in target_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in file_extensions:
                try:
                    content = self.load_text_file(str(file_path))
                    
                    # Generate document ID from file path
                    doc_id = hashlib.md5(str(file_path).encode()).hexdigest()
                    
                    documents.append({
                        'id': doc_id,
                        'content': content,
                        'source': str(file_path.relative_to(self.documents_dir)),
                        'type': subdirectory or 'general',
                        'metadata': {
                            'file_path': str(file_path),
                            'file_name': file_path.name,
                            'file_size': len(content),
                            'chunk_count': 0
                        }
                    })
                    
                except Exception as e:
                    logger.error(f"Error loading document {file_path}: {e}")
                    continue
        
        logger.info(f"Loaded {len(documents)} documents from {target_dir}")
        return documents
    
    def process_documents(
        self,
        documents: List[Dict[str, Any]],
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Process documents by chunking them.
        
        Args:
            documents: List of document dictionaries
            chunk_size: Maximum chunk size
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of chunk dictionaries with 'content', 'source', 'chunk_id', 'metadata'
        """
        chunks = []
        
        for doc in documents:
            doc_chunks = self.chunk_text(
                doc['content'],
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            for idx, chunk_content in enumerate(doc_chunks):
                chunk_id = f"{doc['id']}_chunk_{idx}"
                chunks.append({
                    'id': chunk_id,
                    'content': chunk_content,
                    'source': doc['source'],
                    'type': doc['type'],
                    'metadata': {
                        **doc['metadata'],
                        'chunk_index': idx,
                        'total_chunks': len(doc_chunks),
                        'parent_doc_id': doc['id']
                    }
                })
            
            # Update document metadata
            doc['metadata']['chunk_count'] = len(doc_chunks)
        
        logger.info(f"Processed {len(documents)} documents into {len(chunks)} chunks")
        return chunks


def get_document_loader(documents_dir: str = "data/documents") -> DocumentLoader:
    """Get document loader instance."""
    return DocumentLoader(documents_dir)
