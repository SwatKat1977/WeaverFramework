# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- `validate_json` decorator: moved error response construction inside the
  `except TypeError` block, removing a dangling `error_msg` reference that
  would have caused a `NameError` if any non-TypeError exception were raised
  in a future refactor.

### Added
- Unit tests for `validate_json` decorator covering: valid JSON pass-through,
  validation failure, schema mismatch, and TypeError handling.

---

## [0.2.0a1] - 2026-06-15

### Added
- `ConfigurationManager`: multi-source configuration resolution (environment
  variable -> config file -> default) with type conversion for `str`, `int`,
  `bool`, `path`, `file`, and `directory` types.
- `SqliteInterface`: thread-safe SQLite wrapper with WAL journal mode, foreign
  key enforcement, and a 5-second busy timeout.
- `BaseMicroservice`: abstract async base class providing initialise/run/stop
  lifecycle, asyncio Event-based shutdown signalling, and task management.
- `BaseApiRoute`: base class for Quart route handlers with JSON body validation
  via `jsonschema`.
- `validate_json` decorator for automatic request body validation on route
  handlers.
- `RestClient`: async HTTP client wrapping `aiohttp` with consistent
  `ApiResponse` returns and timeout/error handling for all standard HTTP verbs.
- `HttpContentType`: content-type constants and detection helpers including
  vendor MIME type support.
- `ApiResponse`: standardised response dataclass with a `success` property for
  HTTP 2xx detection.
- `LoggingConfiguration`: immutable logging settings dataclass.
- CI/CD pipeline (GitHub Actions) enforcing Pylint greater or equal 10.0 and 100% unit test
  coverage on every pull request.
