from backend.ai_engine.base import BaseAIEngine
from backend.ai_engine.prototype_nlp import PrototypeAIEngine, ai_engine as prototype_engine
from backend.ai_engine.deepseek_engine import DeepSeekAIEngine, deepseek_engine

# Gunakan DeepSeek AI Engine sebagai mesin utama sistem
ai_engine = deepseek_engine

__all__ = [
    "BaseAIEngine",
    "PrototypeAIEngine",
    "DeepSeekAIEngine",
    "prototype_engine",
    "deepseek_engine",
    "ai_engine"
]
