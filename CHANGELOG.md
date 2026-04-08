# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-08

### Added

- Initial release of ProductTelemetry Python SDK
- Event tracking with `track()` method
- Error tracking with `error()` method
- User identification with `identify()` method
- GDPR-compliant data deletion with `request_deletion()` method
- Automatic event batching and flushing
- Multiple opt-out mechanisms (DO_NOT_TRACK, config file, env vars)
- Thread-safe implementation
- Privacy-first design with client-side anonymization
- Context manager support (`with` statement)
- Comprehensive documentation and examples

### Security

- IP addresses are never sent to the server
- Client IDs stored locally in user config directory
- Support for DO_NOT_TRACK and custom opt-out mechanisms

[0.1.0]: https://github.com/AInvirion/ptelemetry-python-sdk/releases/tag/v0.1.0
