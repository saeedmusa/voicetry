"""Base LLM interface for modular provider support."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator, List, Optional


class MessageRole(Enum):
    """Role of a message in the conversation.

    Per OpenAI API specification, roles are lowercase strings.
    """

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """A single message in the conversation.

    Message format matches OpenAI API specification:
        {"role": "system|user|assistant", "content": "message content"}
    """

    role: MessageRole
    content: str

    def to_dict(self) -> dict:
        """Convert to OpenAI API message format."""
        return {"role": self.role.value, "content": self.content}

    @classmethod
    def system(cls, content: str) -> "Message":
        """Factory method for system messages."""
        return cls(role=MessageRole.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str) -> "Message":
        """Factory method for user messages."""
        return cls(role=MessageRole.USER, content=content)

    @classmethod
    def assistant(cls, content: str) -> "Message":
        """Factory method for assistant messages."""
        return cls(role=MessageRole.ASSISTANT, content=content)


@dataclass
class StreamChunk:
    """A chunk of streamed response."""

    content: str
    is_done: bool = False
    finish_reason: Optional[str] = None


@dataclass
class ConversationHistory:
    """Manages conversation history with context window limits."""

    messages: List[Message] = field(default_factory=list)
    max_messages: int = 20
    system_prompt: Optional[str] = None

    def add_message(self, message: Message) -> None:
        """Add a message to history, respecting limits."""
        self.messages.append(message)

        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def add_user(self, content: str) -> None:
        """Add a user message."""
        self.add_message(Message.user(content))

    def add_assistant(self, content: str) -> None:
        """Add an assistant message."""
        self.add_message(Message.assistant(content))

    def clear(self) -> None:
        """Clear conversation history."""
        self.messages = []

    def get_messages_for_api(self) -> List[dict]:
        """Get messages formatted for API call.

        Returns system prompt (if set) followed by conversation history.
        """
        result = []

        if self.system_prompt:
            result.append(Message.system(self.system_prompt).to_dict())

        result.extend([msg.to_dict() for msg in self.messages])
        return result


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""

    def __init__(
        self,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.history = ConversationHistory(system_prompt=system_prompt)

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a response for the given prompt."""
        pass

    @abstractmethod
    def generate_stream(self, prompt: str) -> Iterator[StreamChunk]:
        """Generate a response with streaming."""
        pass

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.history.clear()
