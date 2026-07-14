"""Provider-agnostic LLM layer (ARCHITECTURE.md Section 9.3).

Adapter/Strategy: services depend on the LLMProvider protocol; the concrete
provider is selected by configuration, never imported directly.
"""

from scriptorium_llm.base import ChatMessage, ChatResponse, LLMProvider
from scriptorium_llm.factory import create_provider
from scriptorium_llm.ollama import OllamaProvider

__all__ = [
    "ChatMessage",
    "ChatResponse",
    "LLMProvider",
    "OllamaProvider",
    "create_provider",
]
