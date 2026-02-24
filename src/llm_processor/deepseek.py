"""DeepSeek LLM processor with streaming support."""

from typing import Iterator, Optional

from openai import OpenAI

from .config import LLMConfig, get_config


class StreamChunk:
    """A chunk of streamed response."""

    content: str
    is_done: bool = False
    finish_reason: Optional[str] = None

    def __init__(
        self,
        content: str,
        is_done: bool = False,
        finish_reason: Optional[str] = None,
    ):
        self.content = content
        self.is_done = is_done
        self.finish_reason = finish_reason


class DeepSeekLLM:
    """DeepSeek API client using OpenAI-compatible interface."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        config: Optional[LLMConfig] = None,
    ):
        """Initialize DeepSeek client.

        Args:
            api_key: DeepSeek API key. If not provided, loads from environment.
            model: Model to use. Defaults to "deepseek-chat".
            system_prompt: System prompt for the conversation.
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Maximum tokens in response.
            config: LLMConfig object. If provided, overrides other params.
        """
        if config:
            self.config = config
        else:
            loaded = get_config()
            self.config = LLMConfig(
                api_key=api_key or loaded.api_key,
                model=model or loaded.model,
                base_url=loaded.base_url,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt or loaded.system_prompt,
            )

        self.client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
        )
        self._messages: list[dict[str, str]] = []

        if self.config.system_prompt:
            self._messages.append(
                {"role": "system", "content": self.config.system_prompt}
            )

    def generate(self, prompt: str) -> str:
        """Generate a complete response.

        Args:
            prompt: User prompt to send to the model.

        Returns:
            The generated response text.
        """
        # Add user message
        messages = self._messages + [{"role": "user", "content": prompt}]

        # Create API request
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        # Extract response
        content = response.choices[0].message.content or ""

        # Save to history
        self._messages.append({"role": "user", "content": prompt})
        self._messages.append({"role": "assistant", "content": content})

        return content

    def generate_stream(self, prompt: str) -> Iterator[StreamChunk]:
        """Generate response with streaming.

        Args:
            prompt: User prompt to send to the model.

        Yields:
            StreamChunk objects as content arrives.
        """
        # Prepare messages
        messages = self._messages + [{"role": "user", "content": prompt}]

        # Create streaming request
        stream = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
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
                self._messages.append({"role": "user", "content": prompt})
                self._messages.append({"role": "assistant", "content": full_content})

                yield StreamChunk(
                    content="",
                    is_done=True,
                    finish_reason=chunk.choices[0].finish_reason,
                )
                break

    def clear_history(self) -> None:
        """Clear conversation history except system prompt."""
        system_prompt = None
        if self._messages and self._messages[0].get("role") == "system":
            system_prompt = self._messages[0]

        self._messages = [system_prompt] if system_prompt else []
