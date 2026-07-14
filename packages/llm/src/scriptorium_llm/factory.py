"""Provider selection by configuration (Strategy), twelve-factor style."""

import os

from scriptorium_llm.base import LLMProvider


def create_provider(env: dict[str, str] | None = None) -> LLMProvider:
    """Build the configured provider.

    Reads LLM_PROVIDER: ollama (default) | anthropic | bedrock.
    CHAT_MODEL/EMBED_MODEL override each provider's default models.
    """
    env = env if env is not None else dict(os.environ)
    provider = env.get("LLM_PROVIDER", "ollama").lower()

    if provider == "anthropic":
        from scriptorium_llm.anthropic_api import DEFAULT_CHAT_MODEL, AnthropicProvider

        return AnthropicProvider(chat_model=env.get("CHAT_MODEL", DEFAULT_CHAT_MODEL))
    if provider == "ollama":
        from scriptorium_llm.ollama import OllamaProvider

        return OllamaProvider(
            host=env.get("OLLAMA_URL", "http://localhost:11434"),
            embed_model=env.get("EMBED_MODEL", "nomic-embed-text"),
            chat_model=env.get("CHAT_MODEL", "llama3.2:3b"),
            # Cold model loads + big-model CPU inference can exceed the 300s
            # default on modest hardware.
            timeout_s=float(env.get("OLLAMA_TIMEOUT_S", "300")),
        )
    if provider == "bedrock":
        from scriptorium_llm.bedrock import BedrockProvider

        return BedrockProvider(
            region=env.get("AWS_REGION", "us-east-1"),
            embed_model=env.get("EMBED_MODEL", "amazon.titan-embed-text-v2:0"),
            chat_model=env.get("CHAT_MODEL", "anthropic.claude-3-5-haiku-20241022-v1:0"),
        )
    raise ValueError(
        f"Unknown LLM_PROVIDER '{provider}' (expected: ollama, anthropic, bedrock)"
    )
