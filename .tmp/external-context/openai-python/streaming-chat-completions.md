---
source: Official OpenAI Documentation
library: OpenAI Python SDK
package: openai
topic: Streaming chat completions
fetched: 2026-02-23T00:00:00Z
official_docs: https://platform.openai.com/docs/guides/streaming-responses
---

# OpenAI Python SDK - Streaming Chat Completions

## Basic Streaming

Stream responses as they're being generated using Server-Sent Events (SSE). This is useful for showing real-time progress to users.

### Sync Streaming

```python
from openai import OpenAI

client = OpenAI()

stream = client.chat.completions.create(
    model="gpt-5.2",
    messages=[
        {"role": "user", "content": "Write a short story about a robot."}
    ],
    stream=True,
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()  # New line at the end
```

### Async Streaming

```python
import asyncio
from openai import AsyncOpenAI

async def main():
    client = AsyncOpenAI()
    
    stream = await client.chat.completions.create(
        model="gpt-5.2",
        messages=[
            {"role": "user", "content": "Count to 10 slowly."}
        ],
        stream=True,
    )
    
    async for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()

asyncio.run(main())
```

## Understanding Stream Chunks

Each chunk in the stream is a `ChatCompletionChunk` object:

```python
ChatCompletionChunk(
    id="chatcmpl-abc123",
    object="chat.completion.chunk",
    created=1699000000,
    model="gpt-5.2",
    choices=[
        {
            "index": 0,
            "delta": {
                "content": "Hello",  # Partial text
                "role": "assistant"  # Only in first chunk
            },
            "finish_reason": None  # Set when complete
        }
    ]
)
```

### Accessing Chunk Data

```python
for chunk in stream:
    delta = chunk.choices[0].delta
    
    # Text content (None if not applicable)
    if delta.content:
        print(delta.content, end="")
    
    # Role (only in first chunk)
    if delta.role:
        print(f"\nRole: {delta.role}")
    
    # Finish reason (None until complete)
    if chunk.choices[0].finish_reason:
        print(f"\nFinished: {chunk.choices[0].finish_reason}")
```

## Complete Streaming Example

### Example 1: Simple Text Stream

```python
from openai import OpenAI

client = OpenAI()

def stream_response(message):
    """Stream a response and return the complete text."""
    stream = client.chat.completions.create(
        model="gpt-5.2",
        messages=[{"role": "user", "content": message}],
        stream=True,
    )
    
    full_response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            full_response += content
    
    return full_response

result = stream_response("Tell me about the benefits of streaming")
print(f"\n\nComplete response length: {len(result)} characters")
```

### Example 2: Progress Tracking

```python
from openai import OpenAI

client = OpenAI()

def stream_with_progress(prompt):
    """Stream with progress indicators."""
    stream = client.chat.completions.create(
        model="gpt-5.2",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    
    full_text = ""
    token_count = 0
    
    for chunk in stream:
        delta = chunk.choices[0].delta
        
        if delta.content:
            token_count += 1
            full_text += delta.content
            print(delta.content, end="", flush=True)
            
            # Show progress every 10 tokens
            if token_count % 10 == 0:
                print(f" [{token_count} tokens]", flush=True)
    
    finish_reason = chunk.choices[0].finish_reason
    print(f"\n\nComplete! {token_count} tokens. Reason: {finish_reason}")
    return full_text

result = stream_with_progress("Explain quantum computing in simple terms")
```

### Example 3: Streaming to File

```python
from openai import OpenAI

client = OpenAI()

def stream_to_file(prompt, filename):
    """Stream response directly to a file."""
    stream = client.chat.completions.create(
        model="gpt-5.2",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    
    with open(filename, 'w') as f:
        for chunk in stream:
            if chunk.choices[0].delta.content:
                f.write(chunk.choices[0].delta.content)
                print(chunk.choices[0].delta.content, end="", flush=True)
    print(f"\n\nSaved to {filename}")

stream_to_file(
    "Write a detailed explanation of machine learning",
    "ml_explanation.txt"
)
```

### Example 4: DeepSeek Streaming

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.deepseek.com",
    api_key="your-deepseek-api-key"
)

stream = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "user", "content": "Explain how you work"}
    ],
    stream=True,
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()
```

## Error Handling with Streaming

```python
from openai import OpenAI, APIError

client = OpenAI()

try:
    stream = client.chat.completions.create(
        model="gpt-5.2",
        messages=[{"role": "user", "content": "Hello"}],
        stream=True,
    )
    
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="")
    
except APIError as e:
    print(f"\nAPI Error: {e}")
except Exception as e:
    print(f"\nUnexpected error: {e}")
```

## Streaming Best Practices

1. **Always flush output** - Use `flush=True` with `print()` to ensure immediate display
2. **Handle None values** - Check `if delta.content is not None` before accessing
3. **Capture complete text** - Accumulate `delta.content` if you need the full response
4. **Handle finish reason** - Check `finish_reason` to know when streaming ends
5. **Use async for concurrent streams** - When handling multiple streaming requests

## Finish Reasons

- `"stop"` - Model completed naturally
- `"length"` - Hit max_tokens limit
- `"content_filter"` - Content was filtered
- `"tool_calls"` - Model called a tool/function

```python
if chunk.choices[0].finish_reason:
    reason = chunk.choices[0].finish_reason
    if reason == "stop":
        print("\nCompleted normally")
    elif reason == "length":
        print("\nHit token limit")
```

## Streaming with Tools (Function Calling)

```python
from openai import OpenAI

client = OpenAI()

functions = [
    {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
            },
            "required": ["location"]
        }
    }
]

stream = client.chat.completions.create(
    model="gpt-5.2",
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
    tools=[{"type": "function", "function": functions[0]}],
    stream=True,
)

for chunk in stream:
    delta = chunk.choices[0].delta
    
    # Regular content
    if delta.content:
        print(delta.content, end="")
    
    # Tool calls appear in delta.tool_calls
    if delta.tool_calls:
        print("\n[Tool call detected]", flush=True)
```
