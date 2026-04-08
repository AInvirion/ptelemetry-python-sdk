# API Reference

## Telemetry Class

### Constructor

```python
Telemetry(
    write_key: str | None = None,
    api_url: str | None = None,
    disabled: bool = False,
    flush_interval: float = 30.0,
    flush_at: int = 10,
    max_queue_size: int = 1000,
    project_slug: str = "default"
)
```

**Arguments:**

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `write_key` | `str \| None` | `os.environ.get('OPS_WRITE_KEY')` | Project write key |
| `api_url` | `str \| None` | `https://api.producttelemetry.com` | API endpoint URL |
| `disabled` | `bool` | `False` | Disable all telemetry |
| `flush_interval` | `float` | `30.0` | Seconds between automatic flushes |
| `flush_at` | `int` | `10` | Number of events to trigger a flush |
| `max_queue_size` | `int` | `1000` | Maximum events to queue |
| `project_slug` | `str` | `'default'` | Project identifier for client_id isolation |

### Methods

#### track()

Track a custom event.

```python
track(
    event_name: str,
    properties: dict[str, Any] | None = None,
    event_type: Literal["lifecycle", "usage", "error"] = "usage",
    timestamp: datetime | None = None
) -> None
```

**Arguments:**
- `event_name` - Event identifier (e.g., `'feature.used'`, `'export.completed'`)
- `properties` - Optional event metadata (dict with any structure)
- `event_type` - Event type: `'lifecycle'`, `'usage'`, or `'error'` (default: `'usage'`)
- `timestamp` - Event timestamp (default: `datetime.now(UTC)`)

**Example:**
```python
t.track('export.started', {
    'format': 'pdf',
    'page_count': 42
})
```

#### error()

Track an error event.

```python
error(
    exception: Exception | None = None,
    message: str | None = None,
    properties: dict[str, Any] | None = None
) -> None
```

**Arguments:**
- `exception` - Exception object to capture
- `message` - Error message (if no exception provided)
- `properties` - Optional additional metadata

**Example:**
```python
try:
    # ... code that might raise
    pass
except Exception as e:
    t.error(exception=e, properties={'context': 'file-processing'})
```

**Captured fields:**
- `error_type` - Exception class name (e.g., `ValueError`)
- `error_message` - Exception message
- `stack_trace` - Full traceback

#### identify()

Link this client to a known user ID.

```python
identify(user_id: str) -> None
```

**Arguments:**
- `user_id` - Your application's user identifier

**Example:**
```python
t.identify('user_123')
```

#### request_deletion()

Request deletion of all data for this client (GDPR compliance).

```python
request_deletion() -> bool
```

**Returns:** `True` if deletion request was submitted successfully

**Example:**
```python
success = t.request_deletion()
if success:
    print('Deletion request submitted')
```

**Behavior:**
- Submits deletion request to server
- Clears local client ID from filesystem
- Returns `True` on success, `False` on failure

#### flush()

Manually flush all queued events to the server.

```python
flush() -> None
```

**Example:**
```python
t.flush()
```

**Note:** Automatically called on interval and at exit via `atexit`. Manual flush useful for:
- Long-running processes
- Before critical shutdown
- Testing

#### shutdown()

Gracefully shutdown the client.

```python
shutdown() -> None
```

**Example:**
```python
import signal

def handle_sigterm(signum, frame):
    t.shutdown()
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_sigterm)
```

**Behavior:**
- Stops flush timer
- Flushes remaining events
- Prevents new events from being queued

### Context Manager

```python
with Telemetry(write_key='proj_wk_xxxxx') as t:
    t.track('event')
# Automatically calls shutdown()
```

## Type Aliases

### EventType

```python
EventType = Literal["lifecycle", "usage", "error"]
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPS_WRITE_KEY` | Project write key | `proj_wk_abc123` |
| `OPS_API_URL` | API endpoint URL | `https://api.producttelemetry.com` |
| `DO_NOT_TRACK` | Universal opt-out | `1` |
| `OPS_TELEMETRY` | SDK-specific opt-out | `0` |

## Configuration File

Location: `~/.config/producttelemetry/<project_slug>/config.json`

```json
{
  "telemetry": false
}
```
