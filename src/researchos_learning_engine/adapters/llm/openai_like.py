"""Generic OpenAI-compatible LLM adapter.

Supports any API provider that implements the OpenAI chat completions
interface (OpenAI, Minimax, Claude via Anthropic's OpenAI-compatible
endpoint, local models via vLLM/Ollama, etc.).

Model provider is configured via LLM_BASE_URL and LLM_MODEL in .env.
No provider-specific logic is hardcoded here.
"""

from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI


class OpenAICompatibleAdapter:
    """Adapter for any OpenAI-compatible chat completion API.

    Reads configuration from environment variables:
        LLM_API_KEY: API key (required if not using a local model)
        LLM_BASE_URL: Base URL of the API endpoint
        LLM_MODEL: Model name/deployment name
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.base_url = base_url or os.getenv(
            "LLM_BASE_URL", "https://api.openai.com/v1"
        )
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o")

        if not self.api_key:
            raise ValueError(
                "LLM API key is required. Set LLM_API_KEY in .env or pass api_key."
            )

        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Generate a response from the LLM."""
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    def generate_json(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Generate a structured JSON response using the LLM's JSON mode."""
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        text = response.choices[0].message.content or "{}"
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw_text": text}
