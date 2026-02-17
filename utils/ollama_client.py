"""
ollama_client.py - Direct Ollama client for TwistedDebate V2

Handles direct Ollama API calls for distortion without TwistedPair dependency.
Implements distortion through prompt engineering and sampling parameters.
"""

import requests
from typing import Dict, Any, Optional
from dataclasses import dataclass


class OllamaConnectionError(Exception):
    """Raised when cannot connect to Ollama server."""
    pass


class OllamaGenerationError(Exception):
    """Raised when Ollama generation fails."""
    pass


@dataclass
class DistortionResult:
    """Result from a distortion operation."""
    output: str
    mode: str
    tone: str
    gain: int
    model: str
    metadata: Dict[str, Any]


class OllamaClient:
    """
    Client for direct Ollama API calls implementing TwistedPair-style distortion.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "gemma3:27b",
        timeout: int = 300,
        verbose: bool = False
    ):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama server URL
            default_model: Default model to use
            timeout: Request timeout in seconds
            verbose: Enable debug logging
        """
        self.base_url = base_url.rstrip('/')
        self.default_model = default_model
        self.timeout = timeout
        self.verbose = verbose
        
        self._log(f"OllamaClient initialized: {self.base_url}")
    
    def _log(self, message: str):
        """Print log message if verbose."""
        if self.verbose:
            print(f"[OllamaClient] {message}")
    
    def is_healthy(self) -> bool:
        """
        Check if Ollama server is reachable.
        
        Returns:
            True if server is healthy
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            self._log(f"Health check failed: {e}")
            return False
    
    def list_models(self) -> list:
        """
        List available Ollama models.
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            response.raise_for_status()
            models = response.json().get("models", [])
            return [m["name"] for m in models]
        except Exception as e:
            self._log(f"Error listing models: {e}")
            return []
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        repeat_penalty: float = 1.1,
        num_ctx: int = 128000,
        num_predict: int = -1,
        **kwargs
    ) -> str:
        """
        Generate text using Ollama.
        
        Args:
            prompt: Input prompt
            model: Model to use (defaults to self.default_model)
            system: Optional system prompt
            temperature: Sampling temperature
            top_p: Nucleus sampling threshold
            top_k: Top-k sampling parameter
            repeat_penalty: Repetition penalty
            num_ctx: Context window size
            num_predict: Max tokens to generate (-1 for unlimited)
            **kwargs: Additional Ollama options
            
        Returns:
            Generated text
            
        Raises:
            OllamaConnectionError: If server unreachable
            OllamaGenerationError: If generation fails
        """
        if model is None:
            model = self.default_model
        
        self._log(f"Generating with model: {model}")
        self._log(f"Params: temp={temperature}, top_p={top_p}, top_k={top_k}")
        
        # Import config for keep_alive setting
        from app.config import OLLAMA_KEEP_ALIVE
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": OLLAMA_KEEP_ALIVE,  # Release GPU memory per config
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "repeat_penalty": repeat_penalty,
                "num_ctx": num_ctx,
            }
        }
        
        if num_predict > 0:
            payload["options"]["num_predict"] = num_predict
        
        if system:
            payload["system"] = system
        
        # Add any extra kwargs to options
        payload["options"].update(kwargs)
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 404:
                raise OllamaConnectionError(
                    f"Model '{model}' not found. Available: {self.list_models()}"
                )
            
            response.raise_for_status()
            result = response.json()
            
            output = result.get("response", "").strip()
            self._log(f"Generated {len(output)} chars")
            
            return output
            
        except requests.exceptions.ConnectionError as e:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self.base_url}: {e}"
            )
        except requests.exceptions.Timeout as e:
            raise OllamaGenerationError(f"Generation timed out: {e}")
        except requests.exceptions.RequestException as e:
            raise OllamaGenerationError(f"Generation failed: {e}")
    
    def distort(
        self,
        text: str,
        mode: str,
        tone: str,
        gain: int,
        model: Optional[str] = None,
        prompt_builder = None,
        param_getter = None
    ) -> DistortionResult:
        """
        Distort text using mode/tone/gain combinations.
        
        This is the main interface compatible with the old TwistedPairClient.
        
        Args:
            text: Input text to distort
            mode: Distortion mode (echo_er, invert_er, etc.)
            tone: Tone style (neutral, technical, etc.)
            gain: Intensity level (1-10)
            model: Optional model override
            prompt_builder: Function to build prompt (uses config.build_distortion_prompt if None)
            param_getter: Function to get params (uses config.get_ollama_params if None)
            
        Returns:
            DistortionResult with output and metadata
        """
        # Import here to avoid circular dependency
        if prompt_builder is None:
            from app.config import build_distortion_prompt
            prompt_builder = build_distortion_prompt
        
        if param_getter is None:
            from app.config import get_ollama_params
            param_getter = get_ollama_params
        
        self._log(f"Distorting: mode={mode}, tone={tone}, gain={gain}")
        
        # Build the prompt
        try:
            prompt = prompt_builder(text, mode, tone)
        except Exception as e:
            raise ValueError(f"Error building prompt: {e}")
        
        # Get sampling parameters for gain level
        try:
            sampling_params = param_getter(gain)
        except Exception as e:
            raise ValueError(f"Error getting sampling params: {e}")
        
        # Generate with Ollama
        try:
            output = self.generate(
                prompt=prompt,
                model=model,
                **sampling_params
            )
        except Exception as e:
            raise OllamaGenerationError(f"Distortion failed: {e}")
        
        # Build result
        result = DistortionResult(
            output=output,
            mode=mode,
            tone=tone,
            gain=gain,
            model=model or self.default_model,
            metadata={
                "prompt_length": len(prompt),
                "output_length": len(output),
                "sampling_params": sampling_params
            }
        )
        
        self._log(f"Distortion complete: {len(output)} chars")
        return result


def main():
    """Test the Ollama client."""
    print("=" * 60)
    print("OllamaClient Test")
    print("=" * 60)
    
    client = OllamaClient(verbose=True)
    
    # Health check
    print("\n1. Health check...")
    if client.is_healthy():
        print("✓ Ollama is healthy")
    else:
        print("✗ Ollama is not available")
        return
    
    # List models
    print("\n2. Available models...")
    models = client.list_models()
    for model in models[:5]:
        print(f"  - {model}")
    
    # Test distortion
    print("\n3. Test distortion...")
    test_text = "What are the implications of artificial intelligence?"
    
    try:
        result = client.distort(
            text=test_text,
            mode="echo_er",
            tone="neutral",
            gain=5
        )
        print(f"✓ Distortion successful")
        print(f"  Mode: {result.mode}")
        print(f"  Tone: {result.tone}")
        print(f"  Output length: {len(result.output)} chars")
        print(f"  Output preview: {result.output[:200]}...")
    except Exception as e:
        print(f"✗ Distortion failed: {e}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
