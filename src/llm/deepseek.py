"""DeepSeek LLM client with streaming support."""

from typing import Iterator, Optional

from openai import OpenAI

from .base import BaseLLM, Message, StreamChunk


class DeepSeekClient(BaseLLM):
    """DeepSeek API client using OpenAI-compatible interface."""

    BASE_URL = "https://api.deepseek.com"
    DEFAULT_MODEL = "deepseek-chat"

    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ):
        """Initialize DeepSeek client.

        Args:
            api_key: DeepSeek API key
            model: Model to use (default: deepseek-chat)
            system_prompt: System prompt for the conversation
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in response
        """
        super().__init__(
            model=model or self.DEFAULT_MODEL,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        self.client = OpenAI(
            api_key=api_key,
            base_url=self.BASE_URL,
        )

    def generate(self, prompt: str) -> str:
        """Generate a complete response."""
        # Add user message to history
        self.history.add_user(prompt)

        # Create API request
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.history.get_messages_for_api(),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        # Extract response
        content = response.choices[0].message.content or ""

        # Add to history
        self.history.add_assistant(content)

        return content

    def generate_stream(self, prompt: str) -> Iterator[StreamChunk]:
        """Generate response with streaming.

        Yields StreamChunk objects as content arrives.
        """
        # Add user message to history
        self.history.add_user(prompt)

        # Create streaming request
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=self.history.get_messages_for_api(),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )

        full_content = ""

        for chunk in stream:
            # Extract delta content
            delta = chunk.choices[0].delta

            if delta.content:
                content_piece = delta.content
                full_content += content_piece
                yield StreamChunk(content=content_piece, is_done=False)

            # Check for completion
            if chunk.choices[0].finish_reason:
                # Save complete response to history
                self.history.add_assistant(full_content)

                yield StreamChunk(
                    content="",
                    is_done=True,
                    finish_reason=chunk.choices[0].finish_reason,
                )
                break

    def get_full_response(self, prompt: str) -> str:
        """Generate and return complete response (non-streaming convenience method)."""
        return self.generate(prompt)
