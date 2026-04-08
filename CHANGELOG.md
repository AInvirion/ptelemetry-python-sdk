# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.4] - 2026-04-08

### Fixed

- **Critical**: Added file lock to prevent race condition in offline persistence
- **Critical**: Copy properties dict to prevent mutation affecting queued events
- **Security**: Config directory now created with 0o700 permissions
- **GDPR**: `request_deletion()` now clears offline events and in-memory queue
- Graceful fallback when config directory is unavailable (read-only HOME)
- Queue now drops oldest events when full instead of silently rejecting new ones
- Fixed docstring with correct default API URL

## [0.1.3] - 2026-04-08

### Added

- **Offline persistence**: Events are now saved to disk when network is unavailable
- Automatic sync when connectivity is restored on next SDK initialization
- Events trimmed to most recent 1000 when exceeding limit
- Silent operation - no noise to end users (debug logging only)

## [0.1.2] - 2026-04-08

### Fixed

- **Critical**: Fixed API endpoint paths (removed duplicate `/api` prefix)
- Updated default API URL to `https://producttelemetry.com/api`
- Verified working with production server

## [0.1.1] - 2026-04-08

### Fixed

- **Critical**: Fixed Python 3.9/3.10 compatibility by replacing `datetime.UTC` with `timezone.utc`
- **Critical**: Fixed `error()` method to properly capture stack traces using `traceback.format_exception()`
- **Security**: Added path traversal protection for `project_slug` parameter
- **Security**: Opt-out config now fails closed - malformed config disables telemetry (privacy-first)

### Changed

- Removed accidentally committed `.pyc` bytecode files
- Updated `.gitignore` with Python-specific patterns
- Bumped `actions/checkout` from v4 to v6 in CI workflows

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

[0.1.4]: https://github.com/AInvirion/ptelemetry-python-sdk/releases/tag/v0.1.4
[0.1.3]: https://github.com/AInvirion/ptelemetry-python-sdk/releases/tag/v0.1.3
[0.1.2]: https://github.com/AInvirion/ptelemetry-python-sdk/releases/tag/v0.1.2
[0.1.1]: https://github.com/AInvirion/ptelemetry-python-sdk/releases/tag/v0.1.1
[0.1.0]: https://github.com/AInvirion/ptelemetry-python-sdk/releases/tag/v0.1.0
