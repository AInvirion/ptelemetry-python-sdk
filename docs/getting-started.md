# Getting Started

## Installation

Install via pip:

```bash
pip install ptelemetry
```

## Quick Start

```python
from ptelemetry import Telemetry

t = Telemetry(write_key='proj_wk_xxxxx')

# Track an event
t.track('feature.used', {'feature': 'export'})

# Track an error
try:
    risky_operation()
except Exception as e:
    t.error(exception=e)

# Link to a user
t.identify('user_123')
```

## Configuration

### Constructor Arguments

```python
t = Telemetry(
    write_key='proj_wk_xxxxx',        # Required: Your project write key
    api_url='https://api.producttelemetry.com',  # Optional: API endpoint
    disabled=False,                    # Optional: Disable all telemetry
    flush_interval=30.0,               # Optional: Seconds between flushes (default: 30)
    flush_at=10,                       # Optional: Events to trigger flush (default: 10)
    max_queue_size=1000,               # Optional: Max events in queue (default: 1000)
    project_slug='my-project'          # Optional: Project identifier (default: 'default')
)
```

### Environment Variables

- `OPS_WRITE_KEY` - Project write key (alternative to constructor arg)
- `OPS_API_URL` - API endpoint URL (alternative to constructor arg)

## Opt-Out Mechanisms

Users can opt out of telemetry via:

**Environment Variables:**
- `DO_NOT_TRACK=1` - Universal opt-out
- `OPS_TELEMETRY=0` - SDK-specific opt-out

**Config File:**
Create `~/.config/producttelemetry/<project_slug>/config.json`:
```json
{
  "telemetry": false
}
```

**Programmatic:**
```python
t = Telemetry(disabled=True)
```

## Context Manager Usage

```python
with Telemetry(write_key='proj_wk_xxxxx') as t:
    t.track('app.started')
    # ... do work
# Automatically calls shutdown() on exit
```

## Troubleshooting

### Events not appearing in dashboard

1. Check write key is correct
2. Verify API URL is reachable
3. Check network connectivity
4. Ensure `flush()` is called before process exit

### Client ID not persisting

Check that `~/.config/producttelemetry/<project_slug>/client_id` file is writable

### Import errors

Ensure Python 3.9+ is installed:
```bash
python --version
```

Ensure httpx is installed:
```bash
pip install httpx>=0.24.0
```
