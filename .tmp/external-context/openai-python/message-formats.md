---
source: Official OpenAI Documentation
library: OpenAI Python SDK
package: openai
topic: Message formats and roles
fetched: 2026-02-23T00:00:00Z
official_docs: https://platform.openai.com/docs/guides/text
---

# OpenAI Python SDK - Message Formats and Roles

## Message Object Structure

Every message in the `messages` array is a dictionary with two required fields:

```python
{
    "role": "user",  # The role of the message sender
    "content": "Your message content here"  # The actual message
}
```

## Message Roles

### 1. `system` / `developer` Role
**Purpose**: Set the behavior and instructions for the AI assistant

**Priority**: Highest - these instructions take priority over user messages

**Use when**: You want to define how the assistant should behave

```python
messages = [
    {
        "role": "system",  # or "developer" in newer versions
        "content": "You are a helpful coding assistant. Always explain your answers clearly and provide code examples."
    }
]
```

**Best practices for system messages**:
- Be clear and specific about the assistant's role
- Include behavioral guidelines (tone, format, style)
- Set constraints or limitations
- Provide examples of desired behavior

```python
# Good system message
{
    "role": "system",
    "content": """You are a math tutor for middle school students.
    - Explain concepts simply
    - Use real-world examples
    - Be encouraging
    - Show step-by-step solutions
    """
}

# Less effective
{
    "role": "system", 
    "content": "Help with math"
}
```

### 2. `user` Role
**Purpose**: Represent the actual user input or questions

**Priority**: Lower than system/developer messages

**Use when**: Sending questions, commands, or user content

```python
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is Python?"}
]
```

**User message formats**:

**Simple text:**
```python
{"role": "user", "content": "Hello, how are you?"}
```

**Multiline text:**
```python
{
    "role": "user",
    "content": """I need help with the following:
    1. Setting up Python
    2. Installing packages
    3. Running my first script
    """
}
```

**With context/data:**
```python
{
    "role": "user",
    "content": """Here's the code I'm working with:
    
    def calculate(x, y):
        return x + y
    
    It's giving me an error. Can you help?
    """
}
```

### 3. `assistant` Role
**Purpose**: Represent the AI's previous responses in a conversation

**Priority**: N/A (used for context/history)

**Use when**: 
- Maintaining conversation history
- Providing few-shot examples
- Showing previous assistant responses for context

```python
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What's 2+2?"},
    {"role": "assistant", "content": "2+2 equals 4."},
    {"role": "user", "content": "What about 3+3?"}
]
```

**Note**: You typically don't send `assistant` messages as input (they come from model responses), but you include them when maintaining conversation history.

## Complete Message Array Examples

### Single Turn (Simple Query)

```python
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain quantum computing"}
]
```

### Multi-Turn Conversation

```python
messages = [
    {"role": "system", "content": "You are a coding tutor."},
    {"role": "user", "content": "What is a variable?"},
    {"role": "assistant", "content": "A variable is like a container that stores data."},
    {"role": "user", "content": "How do I create one in Python?"},
    {"role": "assistant", "content": "In Python, you create a variable by assigning a value: x = 5"},
    {"role": "user", "content": "Can I store text in a variable?"}
]
```

### Few-Shot Examples (Using assistant messages)

```python
messages = [
    {
        "role": "system",
        "content": "You are a sentiment classifier. Output only: positive, negative, or neutral."
    },
    {"role": "user", "content": "I love this product!"},
    {"role": "assistant", "content": "positive"},
    {"role": "user", "content": "This is terrible."},
    {"role": "assistant", "content": "negative"},
    {"role": "user", "content": "It's okay, nothing special."},
    {"role": "assistant", "content": "neutral"},
    {"role": "user", "content": "I'm so happy with this!"}  # What we want classified
]
```

## Advanced Message Content

### Structured Content (Arrays)

For more complex inputs, content can be an array:

```python
{
    "role": "user",
    "content": [
        {"type": "text", "text": "What's in this image?"},
        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
    ]
}
```

### Text with Citations/References

```python
{
    "role": "user",
    "content": """According to the documentation [1], the function should work like this:
    
    Reference [1]: https://docs.example.com/functions
    
    Can you explain this in simpler terms?"""
}
```

## Conversation Management Pattern

```python
class ConversationManager:
    def __init__(self, system_message):
        self.messages = [{"role": "system", "content": system_message}]
    
    def add_user_message(self, content):
        self.messages.append({"role": "user", "content": content})
    
    def add_assistant_message(self, content):
        self.messages.append({"role": "assistant", "content": content})
    
    def get_messages(self):
        return self.messages
    
    def clear_history(self):
        """Keep only the system message"""
        self.messages = [self.messages[0]]
    
    def truncate_history(self, keep_last_n=10):
        """Keep system message + last N exchanges"""
        if len(self.messages) > 2 * keep_last_n + 1:
            # Keep system + last N user/assistant pairs
            self.messages = self.messages[:1] + self.messages[-(2*keep_last_n):]

# Usage
conv = ConversationManager("You are a helpful assistant.")
conv.add_user_message("Hello!")
# After getting response...
conv.add_assistant_message("Hi! How can I help?")
conv.add_user_message("What's the weather?")
```

## DeepSeek API Message Format

DeepSeek API uses the exact same message format as OpenAI:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.deepseek.com",
    api_key="your-api-key"
)

messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant specialized in Chinese-English translation."
    },
    {
        "role": "user",
        "content": "Translate this to English: 你好世界"
    }
]

completion = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages
)
```

## Common Mistakes

### ❌ Wrong: Missing system message
```python
messages = [
    {"role": "user", "content": "Hello"}  # No context set
]
```

### ✅ Correct: Include system message
```python
messages = [
    {"role": "system", "content": "You are a friendly assistant."},
    {"role": "user", "content": "Hello"}
]
```

### ❌ Wrong: Incorrect role name
```python
messages = [
    {"role": "System", "content": "Hello"}  # Capitalized incorrectly
]
```

### ✅ Correct: Lowercase role names
```python
messages = [
    {"role": "system", "content": "Hello"}
]
```

### ❌ Wrong: Empty content
```python
messages = [
    {"role": "user", "content": ""}  # Empty string
]
```

### ✅ Correct: Valid content
```python
messages = [
    {"role": "user", "content": "Hello!"}
]
```

## Message Order Matters

Messages are processed in order, building context incrementally:

```python
# Correct order: system → user → assistant → user
messages = [
    {"role": "system", "content": "Be concise."},
    {"role": "user", "content": "What is AI?"},
    {"role": "assistant", "content": "AI is..."},
    {"role": "user", "content": "And machine learning?"}
]
```

## Token Limits and Messages

Keep track of total tokens across all messages:

```python
def estimate_tokens(text):
    """Rough estimate: 1 token ≈ 4 characters"""
    return len(text) // 4

messages = [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Hello"}
]

total_estimated = sum(estimate_tokens(m["content"]) for m in messages)
print(f"Estimated tokens: {total_estimated}")
```

## Best Practices Summary

1. **Always start with a system message** to set context
2. **Keep system messages clear and specific**
3. **Maintain conversation order** when including history
4. **Use assistant role** for conversation history
5. **Be mindful of token limits** in long conversations
6. **Include examples** in messages for few-shot learning
7. **Use structured content** for complex inputs (images, files)
