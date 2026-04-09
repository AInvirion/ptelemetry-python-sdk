# Product Telemetry SDK (Python)

Privacy-first product analytics and telemetry SDK

## Features

- **Privacy-first** - IP hashing, GDPR compliant
- **Event tracking** - Lifecycle, usage, and error events
- **User identification** - Link anonymous users to known IDs
- **GDPR deletion** - Self-service data deletion requests
- **Multiple opt-out mechanisms** - DO_NOT_TRACK, config file, env vars
- **Minimal dependencies** - Only httpx required
- **Thread-safe** - Use from multiple threads safely
- **Automatic batching** - Efficient event queueing and flushing

## Installation

```bash
pip install ptelemetry
```

## Quick Start

```python
from ptelemetry import Telemetry

t = Telemetry(write_key='proj_wk_xxxxx')

# Track events
t.track('feature.used', {'feature': 'export'})

# Track errors
try:
    risky_operation()
except Exception as e:
    t.error(exception=e)

# Link to user
t.identify('user_123')
```

## Documentation

- [Getting Started](docs/getting-started.md) - Installation, configuration, troubleshooting
- [API Reference](docs/api-reference.md) - Complete API documentation
- [Examples](docs/examples.md) - Real-world usage examples

## Links

- [Product Telemetry Platform](https://ptelemetry.com)
- [JavaScript/TypeScript SDK](https://github.com/AInvirion/ptelemetry-npm-sdk)
- [PyPI Package](https://pypi.org/project/ptelemetry/)

## Contributing

We welcome contributions! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting a pull request.

### Development Setup

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Build package
python -m build
```

## Security

If you discover a security vulnerability, please follow our [Security Policy](SECURITY.md).

## License

MIT - see [LICENSE](LICENSE) file for details.

Copyright (c) 2025-2026 AInvirion LLC. All Rights Reserved.
