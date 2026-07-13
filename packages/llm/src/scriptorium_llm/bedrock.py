"""AWS Bedrock adapter — the primary cloud target (R6). Requires the
[bedrock] extra (boto3). Exercised end to end in M6; unit-tested now."""

import json
from typing import Any

from scriptorium_llm.base import ChatMessage, ChatResponse


class BedrockProvider:
    def __init__(
        self,
        region: str = "us-east-1",
        embed_model: str = "amazon.titan-embed-text-v2:0",
        chat_model: str = "anthropic.claude-3-5-haiku-20241022-v1:0",
        client: Any = None,
    ) -> None:
        if client is None:
            import boto3

            client = boto3.client("bedrock-runtime", region_name=region)
        self._client = client
        self._embed_model = embed_model
        self._chat_model = chat_model

    def embed(self, texts: list[str]) -> list[list[float]]:
        # Titan embeddings accept one input per invocation.
        embeddings: list[list[float]] = []
        for text in texts:
            response = self._client.invoke_model(
                modelId=self._embed_model,
                body=json.dumps({"inputText": text}),
            )
            embeddings.append(json.loads(response["body"].read())["embedding"])
        return embeddings

    def chat(
        self,
        messages: list[ChatMessage],
        tools: list[dict[str, Any]] | None = None,
        stream: bool = False,
    ) -> ChatResponse:
        if stream:
            raise NotImplementedError("streaming arrives with the agent loop (M3)")
        system = [
            {"text": m["content"]} for m in messages if m["role"] == "system"
        ]
        conversation = [
            {"role": m["role"], "content": [{"text": m["content"]}]}
            for m in messages
            if m["role"] != "system"
        ]
        kwargs: dict[str, Any] = {
            "modelId": self._chat_model,
            "messages": conversation,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["toolConfig"] = {"tools": tools}
        response = self._client.converse(**kwargs)
        parts = response["output"]["message"]["content"]
        text = "".join(part.get("text", "") for part in parts)
        usage = response.get("usage", {})
        return ChatResponse(
            content=text,
            usage={
                "input": usage.get("inputTokens", 0),
                "output": usage.get("outputTokens", 0),
            },
        )
