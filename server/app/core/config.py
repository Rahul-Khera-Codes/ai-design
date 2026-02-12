"""Application configuration using pydantic-settings."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str
    
    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CLIENT_URL: Optional[str] = None
    
    # Server
    PORT: int = 8000
    
    # Model Configuration
    MODEL_CACHE_DIR: str = "./models"
    DEVICE: str = "auto"  # auto, cuda, cpu
    HUGGINGFACE_MODEL_NAME: str = "meta-llama/Llama-2-7b-chat-hf"
    HUGGINGFACE_TOKEN: Optional[str] = None  # Optional HF token for private models
    EMBEDDING_MODEL_NAME: str = "Qwen/Qwen2.5-7B-Instruct"
    MODEL_DEVICE: str = "auto"  # cuda, cpu, auto
    MAX_TOKENS: int = 512
    TEMPERATURE: float = 0.7
    EMBEDDING_DIMENSION: int = 768
    
    # Pinecone Configuration
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_INDEX_NAME: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra env vars (e.g. OPENAI_*) when using Hugging Face only


settings = Settings()
