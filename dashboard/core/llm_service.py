"""
LLM Service for Prompt Enhancement
Manages local LLM loading, inference, and unloading.
"""
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import threading


# LLM Model configurations
LLM_MODELS = {
    "phi-3-mini": {
        "name": "Phi-3 Mini",
        "size_gb": 2.0,
        "url": "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf",
        "filename": "phi-3-mini-q4.gguf",
    },
    "qwen-2.5-1.5b": {
        "name": "Qwen 2.5 1.5B",
        "size_gb": 1.5,
        "url": "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "filename": "qwen-2.5-1.5b-q4.gguf",
    },
    "llama-3.2-3b": {
        "name": "Llama 3.2 3B",
        "size_gb": 3.0,
        "url": "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "filename": "llama-3.2-3b-q4.gguf",
    },
}


class LLMService:
    """Manages local LLM for prompt enhancement."""

    def __init__(self, model_base_path: Path):
        self.model_base_path = Path(model_base_path)
        self.llm_dir = self.model_base_path / "llm"
        self.llm_dir.mkdir(parents=True, exist_ok=True)

        self._model = None
        self._current_model_id: Optional[str] = None
        self._last_used: Optional[datetime] = None
        self._lock = threading.Lock()
        self._unload_task: Optional[asyncio.Task] = None

    def get_model_path(self, model_id: str) -> Path:
        """Get the path to a model file."""
        return self.llm_dir / model_id / LLM_MODELS[model_id]["filename"]

    def is_installed(self, model_id: str) -> bool:
        """Check if a model is installed."""
        return self.get_model_path(model_id).exists()

    def get_status(self) -> Dict[str, Any]:
        """Get LLM service status."""
        installed = {}
        for model_id, config in LLM_MODELS.items():
            installed[model_id] = {
                "name": config["name"],
                "size_gb": config["size_gb"],
                "installed": self.is_installed(model_id),
            }

        return {
            "available_models": list(LLM_MODELS.keys()),
            "installed": installed,
            "current_model": self._current_model_id,
            "is_loaded": self._model is not None,
        }

    def _load_model(self, model_id: str):
        """Load a model into memory (lazy)."""
        if self._model is not None and self._current_model_id == model_id:
            return self._model

        try:
            from llama_cpp import Llama

            model_path = self.get_model_path(model_id)
            if not model_path.exists():
                raise FileNotFoundError(f"Model not installed: {model_id}")

            self._model = Llama(
                model_path=str(model_path),
                n_ctx=2048,
                n_threads=4,
                verbose=False,
            )
            self._current_model_id = model_id
            self._last_used = datetime.now()

            return self._model

        except ImportError:
            raise RuntimeError("llama-cpp-python not installed")

    async def enhance_prompt(
        self,
        prompt: str,
        style: str = "detailed",
        model_id: str = "phi-3-mini"
    ) -> Dict[str, Any]:
        """
        Enhance a prompt using the local LLM.

        Args:
            prompt: Original prompt to enhance
            style: Enhancement style (detailed, cinematic, artistic, minimal)
            model_id: Model to use for enhancement

        Returns:
            Dict with enhanced prompt and metadata
        """
        style_prompts = {
            "detailed": "Add quality tags, lighting details, and composition suggestions.",
            "cinematic": "Add film terminology, camera angles, and mood descriptors.",
            "artistic": "Add art style references, techniques, and artistic elements.",
            "minimal": "Fix grammar and lightly improve clarity only.",
        }

        system_prompt = f"""You are a prompt enhancement assistant for AI image/video generation.
Enhance the user's prompt by {style_prompts.get(style, style_prompts['detailed'])}
Keep the enhanced prompt concise (under 200 words).
Only output the enhanced prompt, nothing else."""

        try:
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()

            def run_inference():
                with self._lock:
                    model = self._load_model(model_id)
                    response = model.create_chat_completion(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        max_tokens=200,
                        temperature=0.7,
                    )
                    return response["choices"][0]["message"]["content"]

            enhanced = await loop.run_in_executor(None, run_inference)
            self._last_used = datetime.now()

            return {
                "success": True,
                "original_prompt": prompt,
                "enhanced_prompt": enhanced.strip(),
                "style": style,
                "model": model_id,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "original_prompt": prompt,
            }

    async def download_model(self, model_id: str) -> Dict[str, Any]:
        """Download a model from HuggingFace."""
        if model_id not in LLM_MODELS:
            return {"success": False, "error": f"Unknown model: {model_id}"}

        config = LLM_MODELS[model_id]
        model_dir = self.llm_dir / model_id
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_dir / config["filename"]

        if model_path.exists():
            return {"success": True, "message": "Model already installed", "path": str(model_path)}

        # Download using aiohttp
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(config["url"]) as response:
                    if response.status != 200:
                        raise Exception(f"Download failed: HTTP {response.status}")

                    total_size = int(response.headers.get("content-length", 0))
                    downloaded = 0

                    with open(model_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            # TODO: Broadcast progress via WebSocket

            return {
                "success": True,
                "message": f"Downloaded {config['name']}",
                "path": str(model_path),
                "size_mb": downloaded / (1024 * 1024),
            }

        except Exception as e:
            # Clean up partial download
            if model_path.exists():
                model_path.unlink()
            return {"success": False, "error": str(e)}


# Global instance
llm_service = LLMService(Path("/workspace/models"))


__all__ = ["LLMService", "llm_service", "LLM_MODELS"]
