---
source: Official Rich Source Code
library: Rich
package: rich
topic: Live thread safety considerations
fetched: 2026-02-23T00:00:00Z
official_docs: https://github.com/Textualize/rich/blob/master/rich/live.py
---

# Rich Live - Thread Safety Considerations

## Thread Safety Mechanisms

Rich's `Live` class is designed with thread safety in mind. All critical operations are protected by a reentrant lock (`RLock`).

### Internal Lock Implementation

```python
from threading import RLock

class Live(JupyterMixin, RenderHook):
    def __init__(self, ...):
        self._lock = RLock()  # Reentrant lock for thread safety
```

The `_lock` is an `RLock` (reentrant lock), which means:
- A thread that already holds the lock can acquire it again without blocking
- Multiple threads can safely access the Live instance concurrently
- Deadlocks are prevented when a thread calls locked methods recursively

## Thread-Safe Methods

The following methods are thread-safe (protected by `self._lock`):

### `update()` Method
```python
def update(self, renderable: RenderableType, *, refresh: bool = False) -> None:
    """Thread-safe update of the renderable."""
    if isinstance(renderable, str):
        renderable = self.console.render_str(renderable)
    with self._lock:  # 🔒 Thread-safe
        self._renderable = renderable
        if refresh:
            self.refresh()
```

### `refresh()` Method
```python
def refresh(self) -> None:
    """Thread-safe refresh of the display."""
    with self._lock:  # 🔒 Thread-safe
        self._live_render.set_renderable(self.renderable)
        # ... rest of refresh logic
```

### `start()` Method
```python
def start(self, refresh: bool = False) -> None:
    """Thread-safe start of the live display."""
    with self._lock:  # 🔒 Thread-safe
        if self._started:
            return
        self._started = True
        # ... rest of start logic
```

### `stop()` Method
```python
def stop(self) -> None:
    """Thread-safe stop of the live display."""
    with self._lock:  # 🔒 Thread-safe
        if not self._started:
            return
        self._started = False
        # ... rest of stop logic
```

## Using Live in Threading Animation Loops

### Pattern 1: External Thread Calling `update()` with `refresh=True`

When you have an external thread driving animations:

```python
import threading
import time
from rich.live import Live
from rich.table import Table

class UIAnimator:
    def __init__(self):
        self.running = True
        self.animation_thread = None
        
    def render_ui(self) -> Table:
        """Generate the current UI state."""
        table = Table(title="Animation")
        table.add_column("Frame")
        table.add_column("Value")
        return table
    
    def animation_loop(self):
        """Run animation in a separate thread."""
        frame = 0
        with Live(auto_refresh=False) as live:  # Disable auto-refresh
            while self.running:
                # Render UI and update display
                ui = self.render_ui()
                live.update(ui, refresh=True)  # ✅ Thread-safe
                
                frame += 1
                time.sleep(0.1)  # 10 FPS
    
    def start(self):
        """Start the animation."""
        self.animation_thread = threading.Thread(target=self.animation_loop)
        self.animation_thread.start()
    
    def stop(self):
        """Stop the animation."""
        self.running = False
        if self.animation_thread:
            self.animation_thread.join()
```

### Pattern 2: Auto-Refresh with Background Updates

Let Rich handle the refresh timing:

```python
import threading
import time
from rich.live import Live
from rich.table import Table

class UIState:
    def __init__(self):
        self.table = Table(title="Live Data")
        self.table.add_column("Column 1")
        self.table.add_column("Column 2")
        self.counter = 0
    
    def update_state(self):
        """Update internal state from background thread."""
        while True:
            self.counter += 1
            # Modify table in place
            if self.table.row_count > 0:
                self.table.rows[0][1] = str(self.counter)
            else:
                self.table.add_row(str(self.counter), "Initial")
            time.sleep(0.1)

# Live will auto-refresh at refresh_per_second rate
ui_state = UIState()
update_thread = threading.Thread(target=ui_state.update_state, daemon=True)
update_thread.start()

with Live(ui_state.table, refresh_per_second=10) as live:
    # Auto-refresh handles display updates
    time.sleep(10)  # Run for 10 seconds
```

## Important Considerations

### 1. Auto-Refresh Thread

When `auto_refresh=True`, Rich creates an internal daemon thread:

```python
class _RefreshThread(Thread):
    """A thread that calls refresh() at regular intervals."""
    def run(self) -> None:
        while not self.done.wait(1 / self.refresh_per_second):
            with self.live._lock:  # 🔒 Thread-safe
                if not self.done.is_set():
                    self.live.refresh()
```

This means:
- Two threads may be trying to refresh: your thread and the auto-refresh thread
- Both are protected by the same lock, so they won't conflict
- Using `auto_refresh=False` when you control timing manually is more efficient

### 2. Lock Ordering

When using `update(refresh=True)`, the lock is acquired for both operations:
1. Update the renderable (`self._renderable = renderable`)
2. Refresh the display (`self.refresh()`)

Both operations happen within the same lock context, ensuring atomicity.

### 3. Renderable Thread Safety

The Live class ensures thread-safe access to its own state, but **your renderables must be thread-safe**:

```python
# ❌ Not thread-safe - modifying list while iterating
table = Table()
table.add_column("Data")

def update_table():
    for row in table.rows:  # Race condition!
        table.update_cell(...)

# ✅ Thread-safe - create new renderable each time
def get_new_table():
    new_table = Table()
    new_table.add_column("Data")
    new_table.add_row(data)  # New table, no race
    return new_table
```

### 4. Nested Live Displays

Since Rich 14.0.0, you can nest Live instances:

```python
with Live(outer_renderable) as outer:
    with Live(inner_renderable) as inner:
        # inner displays below outer
        # Both are thread-safe independently
        pass
```

## Best Practices for Threaded Animation Loops

### Do:
- ✅ Use `auto_refresh=False` when you control timing
- ✅ Call `update(renderable, refresh=True)` from your thread
- ✅ Create new renderables for each frame (immutable pattern)
- ✅ Use thread-safe data structures for state
- ✅ Use `with Live()` context manager for proper cleanup

### Don't:
- ❌ Call `update()` from multiple threads without coordination
- ❌ Modify renderables in-place while they're being rendered
- ❌ Call `start()`/`stop()` manually from multiple threads
- ❌ Assume rendering is instantaneous (locks add overhead)

## Thread Safety Summary

| Aspect | Thread-Safe? | Notes |
|--------|--------------|-------|
| `update()` method | ✅ Yes | Protected by `RLock` |
| `refresh()` method | ✅ Yes | Protected by `RLock` |
| `start()`/`stop()` methods | ✅ Yes | Protected by `RLock` |
| Renderable objects | ❌ No | Must ensure thread safety yourself |
| Auto-refresh thread | ✅ Yes | Daemon thread with lock |
| Nested Live instances | ✅ Yes | Independent locks per instance |

## Performance Note

When using `update(renderable, refresh=True)` from a thread:
- The lock is held during the entire operation (update + refresh)
- Refresh involves rendering the renderable, which may be CPU-intensive
- For high-frequency updates (> 30 FPS), consider using `get_renderable` callback pattern or modifying renderables in-place between refreshes
