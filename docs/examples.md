# Examples

## CLI Tool Integration

```python
#!/usr/bin/env python3
import sys
from ptelemetry import Telemetry

t = Telemetry(
    write_key=os.environ.get('MY_TELEMETRY_KEY'),
    project_slug='my-cli-tool'
)

# Track CLI start
t.track('cli.started', {
    'version': '1.0.0',
    'python_version': sys.version
}, event_type='lifecycle')

def run_command(cmd: str):
    t.track('command.executed', {'command': cmd})
    
    try:
        # ... command logic
        t.track('command.completed', {'command': cmd})
    except Exception as e:
        t.error(exception=e, properties={'command': cmd})
        raise

# Graceful shutdown
import atexit
atexit.register(t.flush)

run_command(sys.argv[1])
```

## Error Tracking with Stack Traces

```python
from ptelemetry import Telemetry

t = Telemetry(write_key='proj_wk_xxxxx')

def process_file(path: str):
    try:
        with open(path) as f:
            data = f.read()
        return parse_data(data)
    except Exception as e:
        # Automatic stack trace capture
        t.error(exception=e, properties={
            'file_path': path,
            'operation': 'parse'
        })
        raise

# Custom error with context
def validate_input(data: dict):
    if 'email' not in data:
        error = ValueError('Email required')
        t.error(exception=error, properties={
            'validation_field': 'email',
            'input_type': type(data).__name__
        })
        raise error
```

## User Identification Flow

```python
from ptelemetry import Telemetry

t = Telemetry(write_key='proj_wk_xxxxx')

# Anonymous usage before login
t.track('app.opened')
t.track('feature.explored', {'feature': 'dashboard'})

# User logs in
def on_login(user):
    # Link anonymous client_id to user_id
    t.identify(user.id)
    
    # Now all future events are linked to this user
    t.track('user.logged_in', {
        'plan': user.subscription_plan
    }, event_type='lifecycle')

# User logs out
def on_logout():
    t.track('user.logged_out', event_type='lifecycle')
    # Client keeps same client_id, just not linked to user anymore
```

## GDPR Data Deletion

```python
from ptelemetry import Telemetry

t = Telemetry(write_key='proj_wk_xxxxx')

def handle_account_deletion():
    # User requests account deletion
    success = t.request_deletion()
    
    if success:
        print('Telemetry data deletion requested')
        # Server will delete all events for this client_id within 72 hours
        # Local client_id is cleared immediately
    else:
        print('Failed to request deletion', file=sys.stderr)
```

## Custom Event Properties

```python
from ptelemetry import Telemetry

t = Telemetry(write_key='proj_wk_xxxxx')

# Rich event metadata
t.track('export.completed', {
    'format': 'pdf',
    'page_count': 42,
    'file_size_bytes': 1024000,
    'duration_ms': 3500,
    'quality': 'high',
    'includes_images': True,
    'color_mode': 'rgb'
})

# Nested structures work too
t.track('purchase.completed', {
    'items': [
        {'sku': 'ABC-123', 'quantity': 2, 'price': 29.99},
        {'sku': 'XYZ-789', 'quantity': 1, 'price': 49.99}
    ],
    'total': 109.97,
    'currency': 'USD',
    'payment_method': 'credit_card'
})
```

## Testing/Development Setup

```python
import os
from ptelemetry import Telemetry

# Disable telemetry in tests
t = Telemetry(
    write_key='test-key',
    disabled=os.environ.get('TESTING') == '1'
)

# Or use environment variable
# DO_NOT_TRACK=1 pytest

# Development with local backend
dev_t = Telemetry(
    write_key='dev-key',
    api_url='http://localhost:8000'
)
```

## Context Manager for Automatic Cleanup

```python
from ptelemetry import Telemetry

with Telemetry(write_key='proj_wk_xxxxx') as t:
    t.track('app.started')
    
    # ... do work
    
    t.track('app.finished')
# Automatically calls shutdown() and flushes events
```

## Batch Operations

```python
from ptelemetry import Telemetry

t = Telemetry(
    write_key='proj_wk_xxxxx',
    flush_at=100  # Batch 100 events before flushing
)

# Track many events
for i in range(1000):
    t.track('item.processed', {'item_id': i})

# Events are automatically batched and sent in groups of 100
# Force flush remaining events
t.flush()
```

## Background Task Tracking

```python
from ptelemetry import Telemetry
import threading

t = Telemetry(write_key='proj_wk_xxxxx')

def background_job():
    t.track('job.started', event_type='lifecycle')
    try:
        # ... long-running work
        t.track('job.completed')
    except Exception as e:
        t.error(exception=e)

# SDK is thread-safe
thread = threading.Thread(target=background_job)
thread.start()
thread.join()

t.shutdown()
```
