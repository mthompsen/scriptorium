# packages/llm

Shared Python LLM provider layer (DESIGN.md Section 9.3): an `LLMProvider`
protocol with Adapter/Strategy implementations for AWS Bedrock, Azure OpenAI,
Google Vertex, and Ollama (local laptop mode). Consumed by the ingestion and
agent services.

**Status:** placeholder. The provider interface and the Ollama + Bedrock
adapters land in M2.
