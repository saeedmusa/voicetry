"""Text-to-speech synthesizer using Kokoro ONNX TTS model."""

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

from .config import TTSConfig

_KOKORO_INSTANCE = None


def _create_optimized_session_options():
    """Create optimized ONNX Runtime SessionOptions for CPU."""
    try:
        import onnxruntime as ort
        
        sess_options = ort.SessionOptions()
        
        # Enable all graph optimizations (basic, extended, layout, etc.)
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        # Use parallel execution for better CPU utilization
        sess_options.execution_mode = ort.ExecutionMode.ORT_PARALLEL
        
        # Optimize intra-op threads - use most available cores
        # Leave 1-2 cores free for other operations
        cpu_count = os.cpu_count() or 4
        sess_options.intra_op_num_threads = max(2, cpu_count - 1)
        
        # Enable memory optimization
        sess_options.enable_mem_pattern = True
        sess_options.enable_cpu_mem_arena = True
        
        return sess_options
    except ImportError:
        return None


def _get_kokoro() -> Kokoro:
    """Get or create global Kokoro instance with optimized settings."""
    global _KOKORO_INSTANCE
    if _KOKORO_INSTANCE is None:
        cache_dir = Path.home() / ".cache" / "kokoro"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        model_path = cache_dir / "kokoro-v1.0.onnx"
        voices_path = cache_dir / "voices-v1.0.bin"
        
        if not model_path.exists():
            from huggingface_hub import hf_hub_download
            print("Downloading Kokoro ONNX model...")
            model_path = hf_hub_download("fastrtc/kokoro-onnx", "kokoro-v1.0.onnx", local_dir=str(cache_dir))
            voices_path = hf_hub_download("fastrtc/kokoro-onnx", "voices-v1.0.bin", local_dir=str(cache_dir))
        
        # Try to use optimized session options
        sess_options = _create_optimized_session_options()
        
        if sess_options is not None:
            try:
                # Use custom session with optimizations
                import onnxruntime as ort
                inf_sess = ort.InferenceSession(
                    str(model_path),
                    sess_options=sess_options,
                    providers=["CPUExecutionProvider"]
                )
                _KOKORO_INSTANCE = Kokoro.from_session(inf_sess, str(voices_path))
            except Exception as e:
                print(f"Warning: Could not use optimized session: {e}")
                # Fall back to default
                _KOKORO_INSTANCE = Kokoro(str(model_path), str(voices_path))
        else:
            _KOKORO_INSTANCE = Kokoro(str(model_path), str(voices_path))
    
    return _KOKORO_INSTANCE


def _warmup_kokoro():
    """Warm up the Kokoro model with a short synthesis."""
    global _KOKORO_INSTANCE
    if _KOKORO_INSTANCE is not None:
        try:
            # Quick warmup with short text
            _KOKORO_INSTANCE.create("a", voice="af_heart", speed=1.0)
        except Exception:
            pass  # Ignore warmup errors


class Synthesizer:
    """TTS synthesizer using Kokoro ONNX.

    Processes text and returns audio as numpy array at 24kHz.
    Optimized for CPU performance.
    """

    def __init__(self, config: Optional[TTSConfig] = None, warmup: bool = True) -> None:
        """Initialize synthesizer with TTS configuration.

        Args:
            config: TTS configuration. Uses defaults if None.
            warmup: Whether to warm up the model on first init.
        """
        self.config = config or TTSConfig()
        self._is_warmed = False
        
        if not _KOKORO_AVAILABLE:
            raise RuntimeError(
                "kokoro-onnx not installed. Run: pip install kokoro-onnx"
            )
        
        # Warm up the model in background after initialization
        if warmup:
            import threading
            warmup_thread = threading.Thread(target=_warmup_kokoro, daemon=True)
            warmup_thread.start()

    def synthesize(self, text: str) -> np.ndarray:
        """Synthesize text to audio (sync, returns full audio).

        Args:
            text: Input text to synthesize.

        Returns:
            Audio samples as numpy array (float32, 24kHz).

        Raises:
            ValueError: If text is empty or synthesis fails.
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")

        kokoro = _get_kokoro()
        audio, _ = kokoro.create(text, voice=self.config.voice_name, speed=self.config.speed)
        
        return audio

    async def synthesize_stream(self, text: str) -> AsyncGenerator[tuple[np.ndarray, int], None]:
        """Synthesize text to audio stream (async, yields chunks).

        Args:
            text: Input text to synthesize.

        Yields:
            Tuple of (audio_chunk, sample_rate).

        Raises:
            ValueError: If text is empty.
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")

        kokoro = _get_kokoro()
        
        async for audio_chunk, sr in kokoro.create_stream(
            text, 
            voice=self.config.voice_name, 
            speed=self.config.speed
        ):
            yield audio_chunk, sr

    @property
    def sample_rate(self) -> int:
        """Return output sample rate."""
        return self.config.sample_rate
