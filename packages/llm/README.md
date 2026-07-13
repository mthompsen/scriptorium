# packages/llm

Shared Python LLM provider layer (DESIGN.md Section 9.3): an `LLMProvider`
protocol with Adapter/Strategy implementations for AWS Bedrock, Azure OpenAI,
Google Vertex, and Ollama (local laptop mode). Consumed by the ingestion and
agent services.

**Status:** Ollama and Bedrock adapters implemented (M2). Azure OpenAI and
Vertex adapters arrive with the cloud milestones.

Selection is by environment (`LLM_PROVIDER=ollama|bedrock`; see
`factory.py` for the model/env knobs). Bedrock needs the `[bedrock]` extra.

Consumers (ingestion, agent) install this package by path — locally
`pip install -e packages/llm`, in Docker/CI an explicit install step before
the service — because Python path dependencies aren't portable inside a
service's own pyproject.
