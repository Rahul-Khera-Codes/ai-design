"""Embedding Service for Qwen3-Embedding-8B model."""

import logging
from typing import List, Union, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using Qwen3-Embedding-8B."""
    
    _instance: Optional['EmbeddingService'] = None
    _model: Optional[SentenceTransformer] = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize embedding service."""
        if self._model is None:
            self._load_model()
    
    def _load_model(self):
        """Load the embedding model."""
        if self._model is not None:
            logger.info("Embedding model already loaded, skipping reload")
            return
        
        try:
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}")
            
            # Load model using sentence-transformers
            # If Qwen3-Embedding-8B is not available via sentence-transformers,
            # we'll use transformers directly
            try:
                self._model = SentenceTransformer(
                    settings.EMBEDDING_MODEL_NAME,
                    cache_folder=settings.MODEL_CACHE_DIR
                )
            except Exception:
                # Fallback: use transformers directly
                logger.info("Falling back to transformers for embedding model")
                from transformers import AutoTokenizer, AutoModel
                import torch
                
                tokenizer = AutoTokenizer.from_pretrained(
                    settings.EMBEDDING_MODEL_NAME,
                    cache_dir=settings.MODEL_CACHE_DIR,
                    trust_remote_code=True
                )
                model = AutoModel.from_pretrained(
                    settings.EMBEDDING_MODEL_NAME,
                    cache_dir=settings.MODEL_CACHE_DIR,
                    trust_remote_code=True,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
                )
                
                # Wrap in a simple interface
                class EmbeddingWrapper:
                    def __init__(self, model, tokenizer):
                        self.model = model
                        self.tokenizer = tokenizer
                        self.device = "cuda" if torch.cuda.is_available() else "cpu"
                        self.model.to(self.device)
                        self.model.eval()
                    
                    def encode(self, texts: List[str], **kwargs) -> np.ndarray:
                        """Encode texts to embeddings."""
                        import torch
                        with torch.no_grad():
                            inputs = self.tokenizer(
                                texts,
                                padding=True,
                                truncation=True,
                                return_tensors="pt",
                                max_length=512
                            ).to(self.device)
                            
                            outputs = self.model(**inputs)
                            # Use mean pooling
                            embeddings = outputs.last_hidden_state.mean(dim=1)
                            return embeddings.cpu().numpy()
                
                self._model = EmbeddingWrapper(model, tokenizer)
            
            logger.info("Embedding model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            raise
    
    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        normalize_embeddings: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings for input text(s).
        
        Args:
            texts: Single text string or list of texts
            batch_size: Batch size for processing
            normalize_embeddings: Whether to normalize embeddings to unit length
            
        Returns:
            Numpy array of embeddings (shape: [len(texts), embedding_dim])
        """
        if self._model is None:
            self._load_model()
        
        try:
            # Convert single string to list
            if isinstance(texts, str):
                texts = [texts]
            
            # Generate embeddings
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=normalize_embeddings,
                show_progress_bar=False
            )
            
            # Ensure numpy array
            if not isinstance(embeddings, np.ndarray):
                embeddings = np.array(embeddings)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings."""
        if self._model is None:
            self._load_model()
        
        # Try to get dimension from model
        try:
            if hasattr(self._model, 'get_sentence_embedding_dimension'):
                return self._model.get_sentence_embedding_dimension()
        except:
            pass
        
        # Return configured dimension as fallback
        return settings.EMBEDDING_DIMENSION


def get_embedding_service() -> EmbeddingService:
    """Get singleton instance of EmbeddingService."""
    return EmbeddingService()
