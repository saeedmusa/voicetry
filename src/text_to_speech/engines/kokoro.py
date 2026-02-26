"""Kokoro TTS engine implementation."""

import os
from pathlib import Path
from typing import AsyncGenerator, Optional

import numpy as np

try:
    from kokoro_onnx import Kokoro
    _KOKORO_AVAILABLE = True
except ImportError:
    Kokoro = None
    _KOKORO_AVAILABLE = False

from ..config import TTSConfig
from ..base import TTSEngine

_KOKORO_INSTANCE = None


def _get_kokoro_cache_dir() -> Path:
    """Get the kokoro cache directory, configurable via environment variable."""
    cache_env = os.environ.get("KOKORO_CACHE_DIR")
    if cache_env:
        return Path(cache_env)
    return Path.home() / ".cache" / "kokoro"


def _create_optimized_session_options():
    """Create optimized ONNX Runtime SessionOptions for CPU."""
    try:
        import onnxruntime as ort
        
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.execution_mode = ort.ExecutionMode.ORT_PARALLEL
        cpu_count = os.cpu_count() or 4
        sess_options.intra_op_num_threads = max(2, cpu_count - 1)
        sess_options.enable_mem_pattern = True
        sess_options.enable_cpu_mem_arena = True
        return sess_options
    except ImportError:
        return None


def _get_kokoro() -> Kokoro:
    """Get or create global Kokoro instance."""
    global _KOKORO_INSTANCE
    if _KOKORO_INSTANCE is None:
        cache_dir = _get_kokoro_cache_dir()
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        model_path = cache_dir / "kokoro-v1.0.onnx"
        voices_path = cache_dir / "voices-v1.0.bin"
        
        if not model_path.exists():
            from huggingface_hub import hf_hub_download
            print("Downloading Kokoro ONNX model...")
            model_path = hf_hub_download("fastrtc/kokoro-onnx", "kokoro-v1.0.onnx", local_dir=str(cache_dir))
            voices_path = hf_hub_download("fastrtc/kokoro-onnx", "voices-v1.0.bin", local_dir=str(cache_dir))
        
        sess_options = _create_optimized_session_options()
        
        if sess_options is not None:
            try:
                import onnxruntime as ort
                inf_sess = ort.InferenceSession(
                    str(model_path),
                    sess_options=sess_options,
                    providers=["CPUExecutionProvider"]
                )
                _KOKORO_INSTANCE = Kokoro.from_session(inf_sess, str(voices_path))
            except Exception as e:
                print(f"Warning: Could not use optimized session: {e}")
                _KOKORO_INSTANCE = Kokoro(str(model_path), str(voices_path))
        else:
            _KOKORO_INSTANCE = Kokoro(str(model_path), str(voices_path))
    
    return _KOKORO_INSTANCE


_VOICES = [
    "af_bella",
    "af_heart",
    "af_sarah",
    "af_sky",
    "am_adam",
    "am_michael",
    "bf_emma",
    "bm_george",
]

_VOICE_DESCRIPTIONS = {
    "af_bella": "Female, American",
    "af_heart": "Female, warm",
    "af_sarah": "Female, clear",
    "af_sky": "Female",
    "am_adam": "Male, American",
    "am_michael": "Male, American",
    "bf_emma": "Female, British",
    "bm_george": "Male, British",
}


def _warmup():
    """Warm up the Kokoro model."""
    global _KOKORO_INSTANCE
    try:
        kokoro = _get_kokoro()
        kokoro.create("a", voice="af_heart", speed=1.0)
    except Exception:
        pass


class KokoroEngine(TTSEngine):
    """TTS engine using Kokoro ONNX."""
    
    voices = _VOICES

    def __init__(self, config: Optional[TTSConfig] = None) -> None:
        self.config = config or TTSConfig()
        self._voice = self.config.voice_name
        
        if not _KOKORO_AVAILABLE:
            raise RuntimeError("kokoro-onnx not installed. Run: pip install kokoro-onnx")
        
        import threading
        warmup_thread = threading.Thread(target=_warmup, daemon=True)
        warmup_thread.start()

    @property
    def name(self) -> str:
        return "kokoro"

    @property
    def voice_descriptions(self) -> dict:
        return _VOICE_DESCRIPTIONS

    @property
    def sample_rate(self) -> int:
        return 24000

    def synthesize(self, text: str) -> np.ndarray:
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")
        kokoro = _get_kokoro()
        audio, _ = kokoro.create(text, voice=self._voice, speed=self.config.speed)
        return audio

    async def synthesize_stream(self, text: str) -> AsyncGenerator[tuple[np.ndarray, int], None]:
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")
        kokoro = _get_kokoro()
        async for audio_chunk, sr in kokoro.create_stream(text, voice=self._voice, speed=self.config.speed):
            yield audio_chunk, sr
