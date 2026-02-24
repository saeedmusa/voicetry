---
source: Official Rich Documentation
library: Rich
package: rich
topic: Live class constructor and update method
fetched: 2026-02-23T00:00:00Z
official_docs: https://rich.readthedocs.io/en/stable/live.html
---

# Rich Live Class - Constructor and Update Method

## Class Constructor

```python
from rich.live import Live

Live(
    renderable: Optional[RenderableType] = None,
    *,
    console: Optional[Console] = None,
    screen: bool = False,
    auto_refresh: bool = True,
    refresh_per_second: float = 4,
    transient: bool = False,
    redirect_stdout: bool = True,
    redirect_stderr: bool = True,
    vertical_overflow: VerticalOverflowMethod = "ellipsis",
    get_renderable: Optional[Callable[[], RenderableType]] = None,
) -> None
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `renderable` | `RenderableType` | `None` | The renderable to live display. Defaults to displaying nothing. |
| `console` | `Console` | `None` | Optional Console instance. Defaults to an internal Console instance writing to stdout. |
| `screen` | `bool` | `False` | Enable alternate screen mode (full-screen). |
| `auto_refresh` | `bool` | `True` | Enable auto refresh. If disabled, you will need to call `refresh()` or `update()` with `refresh=True`. |
| `refresh_per_second` | `float` | `4` | Number of times per second to refresh the live display. |
| `transient` | `bool` | `False` | Clear the renderable on exit (has no effect when `screen=True`). |
| `redirect_stdout` | `bool` | `True` | Enable redirection of stdout, so `print` may be used. |
| `redirect_stderr` | `bool` | `True` | Enable redirection of stderr. |
| `vertical_overflow` | `VerticalOverflowMethod` | `"ellipsis"` | How to handle renderable when it is too tall for the console. Options: `"crop"`, `"ellipsis"`, `"visible"`. |
| `get_renderable` | `Callable[[], RenderableType]` | `None` | Optional callable to get renderable dynamically. |

### Renderable Types

Any object that can be rendered by Rich, including:
- `str` - plain text (automatically converted)
- `Table` - from `rich.table`
- `Panel` - from `rich.panel`
- `Layout` - from `rich.layout`
- `Text` - from `rich.text`
- `Status` - from `rich.status`
- Custom renderables implementing `RichRenderable`

## `update()` Method

```python
def update(self, renderable: RenderableType, *, refresh: bool = False) -> None:
    """Update the renderable that is being displayed.

    Args:
        renderable (RenderableType): New renderable to use.
        refresh (bool, optional): Refresh the display. Defaults to False.
    """
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `renderable` | `RenderableType` | Required | New renderable to display. |
| `refresh` | `bool` | `False` | Whether to immediately refresh the display. |

### Return Type
`None`

### Usage Pattern with `refresh` Parameter

When using Live with **auto-refresh disabled** (`auto_refresh=False`), you must explicitly request refreshes:

```python
from rich.live import Live
from rich.table import Table

# Disable auto-refresh to control timing manually
with Live(auto_refresh=False) as live:
    for i in range(10):
        table = Table(title=f"Frame {i}")
        table.add_column("Column")
        table.add_row(f"Data {i}")
        
        # Update and immediately refresh
        live.update(table, refresh=True)
        time.sleep(0.5)
```

When using Live with **auto-refresh enabled** (`auto_refresh=True`, the default), refresh happens automatically:

```python
# Auto-refresh is True by default, refresh happens at refresh_per_second rate
with Live() as live:
    for i in range(10):
        table = Table(title=f"Frame {i}")
        table.add_column("Column")
        table.add_row(f"Data {i}")
        
        # Just update - auto-refresh will display it
        live.update(table)
        time.sleep(0.5)
```

## `refresh()` Method

```python
def refresh(self) -> None:
    """Update the display of the Live Render.
    
    Returns:
        None
    """
```

Manually trigger a refresh without changing the renderable. Useful when:
- The renderable is modified in-place
- Using `get_renderable` callback
- You want to force an immediate update

## Context Manager Usage

```python
from rich.live import Live
from rich.table import Table

table = Table()
table.add_column("ID")
table.add_column("Value")

# Live display persists for the duration of the context
with Live(table, refresh_per_second=4) as live:
    for row in range(10):
        table.add_row(str(row), f"Value {row}")
        time.sleep(0.4)
```

## Context Manager Exit Behavior

On context exit (`stop()`):
- If `transient=True` (and `screen=False`): Display disappears
- If `transient=False` (default): Last frame remains in terminal with cursor on following line
- If `screen=True`: Alternate screen is restored, command prompt returns

## Key Methods

| Method | Description |
|--------|-------------|
| `start(refresh=False)` | Start live rendering display |
| `stop()` | Stop live rendering display |
| `update(renderable, refresh=False)` | Update the renderable that is being displayed |
| `refresh()` | Update the display without changing renderable |
| `renderable` (property) | Get the renderable that is being displayed |
| `is_started` (property) | Check if live display has been started |
