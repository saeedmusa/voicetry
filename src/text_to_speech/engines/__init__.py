"""TTS engine registry and factory."""

from typing import Optional

from ..config import TTSConfig
from ..base import TTSEngine
from .kokoro import KokoroEngine
from .piper import PiperEngine

_ENGINES = {
    "kokoro": KokoroEngine,
    "piper": PiperEngine,
}


def get_engine(engine_name: str) -> type[TTSEngine]:
    """Get the TTS engine class by name.
    
    Args:
        engine_name: Name of the engine ('kokoro' or 'piper')
        
    Returns:
        TTSEngine class
        
    Raises:
        ValueError: If engine name is not recognized
    """
    engine_name = engine_name.lower()
    if engine_name not in _ENGINES:
        raise ValueError(f"Unknown engine: {engine_name}. Available: {list(_ENGINES.keys())}")
    return _ENGINES[engine_name]


def create_engine(config: Optional[TTSConfig] = None) -> TTSEngine:
    """Create a TTS engine from config.
    
    Args:
        config: TTSConfig with engine setting. Defaults to 'piper'.
        
    Returns:
        TTSEngine instance
    """
    config = config or TTSConfig()
    engine_name = config.engine or "piper"
    engine_class = get_engine(engine_name)
    return engine_class(config)


__all__ = [
    "TTSEngine",
    "KokoroEngine", 
    "PiperEngine",
    "get_engine",
    "create_engine",
]
