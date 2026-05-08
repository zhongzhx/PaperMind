"""Abstract LLM adapter interface.

All LLM interaction goes through this protocol. Implementations
provide the actual API calls to different providers.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMAdapter(Protocol):
    """Protocol for LLM adapters.

    Implementations must provide a `generate` method that takes
    a system prompt and a user message and returns the model's
    response text.
    """

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Generate a response from the LLM.

        Args:
            system_prompt: System-level instructions for the model.
            user_message: The user's message / query.
            temperature: Sampling temperature (0.0 = deterministic).
            max_tokens: Maximum tokens in the response.

        Returns:
            The model's response text.
        """
        ...

    def generate_json(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict:
        """Generate a structured JSON response from the LLM.

        The default implementation calls generate() and attempts to
        parse the result as JSON. Providers with native JSON mode
        may override this.
        """
        ...
