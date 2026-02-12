"""LLM Service for LLaMA model loading and text generation using Hugging Face Transformers."""

import logging
from typing import Optional, List, Dict, Any
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for managing LLaMA model inference."""
    
    _instance: Optional['LLMService'] = None
    _model: Optional[Any] = None
    _tokenizer: Optional[Any] = None
    _pipeline: Optional[Any] = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize LLM service."""
        if self._model is None:
            self._load_model()
    
    def _get_device(self) -> str:
        """Determine the device to use for model inference."""
        if settings.MODEL_DEVICE == "auto":
            if torch.cuda.is_available():
                return "cuda"
            return "cpu"
        return settings.MODEL_DEVICE
    
    def _load_model(self):
        """Load LLaMA model and tokenizer."""
        if self._model is not None:
            logger.info("Model already loaded, skipping reload")
            return
        
        try:
            device = self._get_device()
            logger.info(f"Loading LLaMA model: {settings.HUGGINGFACE_MODEL_NAME} on {device}")
            
            # Load tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(
                settings.HUGGINGFACE_MODEL_NAME,
                cache_dir=settings.MODEL_CACHE_DIR,
                trust_remote_code=True
            )
            
            # Set padding token if not present
            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token
            
            # Load model
            self._model = AutoModelForCausalLM.from_pretrained(
                settings.HUGGINGFACE_MODEL_NAME,
                cache_dir=settings.MODEL_CACHE_DIR,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="auto" if device == "cuda" else None,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            
            if device == "cpu":
                self._model = self._model.to(device)
            
            # Create pipeline for easier text generation
            self._pipeline = pipeline(
                "text-generation",
                model=self._model,
                tokenizer=self._tokenizer,
                device=0 if device == "cuda" else -1,
                return_full_text=False
            )
            
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: float = 0.9,
        stop_sequences: Optional[List[str]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text using the LLaMA model.
        
        Args:
            prompt: Input prompt for generation
            max_tokens: Maximum tokens to generate (defaults to config)
            temperature: Sampling temperature (defaults to config)
            top_p: Nucleus sampling parameter
            stop_sequences: List of sequences to stop generation at
            system_prompt: Optional system prompt to prepend
            
        Returns:
            Generated text
        """
        if self._pipeline is None:
            self._load_model()
        
        try:
            # Format prompt with system prompt if provided
            if system_prompt:
                formatted_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:"
            else:
                formatted_prompt = prompt
            
            # Generate text
            max_new_tokens = max_tokens or settings.MAX_TOKENS
            temp = temperature if temperature is not None else settings.TEMPERATURE
            
            outputs = self._pipeline(
                formatted_prompt,
                max_new_tokens=max_new_tokens,
                temperature=temp,
                top_p=top_p,
                do_sample=True,
                return_full_text=False,
                pad_token_id=self._tokenizer.eos_token_id
            )
            
            generated_text = outputs[0]["generated_text"]
            
            # Apply stop sequences if provided
            if stop_sequences:
                for stop_seq in stop_sequences:
                    if stop_seq in generated_text:
                        generated_text = generated_text.split(stop_seq)[0]
            
            return generated_text.strip()
            
        except Exception as e:
            logger.error(f"Error during text generation: {e}")
            raise
    
    def generate_structured(
        self,
        prompt: str,
        json_schema: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate structured output (JSON) from prompt.
        
        Args:
            prompt: Input prompt
            json_schema: Optional JSON schema to guide output
            system_prompt: Optional system prompt
            
        Returns:
            Parsed JSON dictionary
        """
        import json
        import re
        
        # Add instruction for JSON output
        json_instruction = "\n\nPlease respond with valid JSON only."
        if json_schema:
            json_instruction += f"\nSchema: {json.dumps(json_schema, indent=2)}"
        
        full_prompt = prompt + json_instruction
        
        response = self.generate(
            full_prompt,
            system_prompt=system_prompt,
            temperature=0.3  # Lower temperature for structured output
        )
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from response")
        
        # Fallback: try to parse entire response
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error(f"Could not parse JSON from response: {response}")
            return {"error": "Failed to generate structured output", "raw": response}


def get_llm_service() -> LLMService:
    """Get singleton instance of LLMService."""
    return LLMService()
