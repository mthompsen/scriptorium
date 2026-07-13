import pytest

from scriptorium_llm import LLMProvider, OllamaProvider, create_provider


def test_defaults_to_ollama_with_env_overrides() -> None:
    provider = create_provider(
        {"OLLAMA_URL": "http://ollama:11434", "EMBED_MODEL": "custom-embed"}
    )

    assert isinstance(provider, OllamaProvider)
    assert isinstance(provider, LLMProvider)  # satisfies the port


def test_unknown_provider_is_rejected() -> None:
    with pytest.raises(ValueError, match="azure-someday"):
        create_provider({"LLM_PROVIDER": "azure-someday"})
