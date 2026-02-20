# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2026-02-20

### Changed
- Docker base image (`python:3.12-slim`) pinned to SHA256 digest for fully reproducible builds
- Docker HEALTHCHECK refactored from inline Python one-liner to a dedicated `healthcheck.py` script for clarity and maintainability
- Broad `except Exception` in LLM agent replaced with specific `ImportError`, `anthropic.APIConnectionError`, and `anthropic.APIStatusError` handlers to avoid masking misconfigurations
- All dependencies in `requirements.txt` now include `--require-hashes` integrity hashes (via `pip-compile --generate-hashes`) for supply chain security
- README Docker example updated to use `latest` tag instead of stale version reference

### Added
- `healthcheck.py` — standalone health check script used by Docker HEALTHCHECK
- `certifi` and `packaging` added as explicit transitive dependencies (previously implicit)

## [0.6.0] - 2026-02-20

### Changed
- Dockerfile now uses a virtual environment in the builder stage and copies it with `--chown` to the non-root user, replacing the `/usr/local` prefix overlay for cleaner dependency isolation
- Readiness check (`/readyz`) now verifies the flight data store via `len(SAMPLE_FLIGHTS)` instead of the fragile `co_consts` bytecode heuristic
- `anthropic` SDK upgraded from 0.42.0 to 0.52.0 for confirmed compatibility with the `claude-sonnet-4-20250514` model identifier
- Version management unified: `config.py` and `pyproject.toml` now read from the `VERSION` file as the single source of truth (previously duplicated in three places)
- Docker image version label now set via `--build-arg APP_VERSION` instead of being hardcoded

### Fixed
- CHANGELOG v0.4.0 entry incorrectly listed `gunicorn==23.0.0`; corrected to `gunicorn==25.1.0` to match `requirements.txt`
- Missing `distro` and `jiter` transitive dependencies added to `requirements.txt` (required by `anthropic` SDK)

## [0.5.0] - 2026-02-20

### Added
- Conversational AI agent endpoint (`POST /api/v1/agent`) powered by Claude via the Anthropic SDK
- Keyword-based fallback agent when no `ANTHROPIC_API_KEY` is configured
- `anthropic==0.42.0` dependency for LLM integration
- `ANTHROPIC_API_KEY` environment variable support
- `.env.example` documenting all configuration variables
- `.gitignore` for clean repository hygiene

### Changed
- Version bumped to 0.5.0 (minor release – new feature, no breaking changes)
- README updated with agent endpoint documentation and example usage
- Docker image label updated to reflect conversational AI capability

## [0.4.0] - 2026-02-20

### Changed
- Default `APP_HOST` changed from `0.0.0.0` to `127.0.0.1` for safer local development; Docker container explicitly sets `0.0.0.0` via environment variable
- Dockerfile ENTRYPOINT switched from bare `uvicorn` to `gunicorn` with `UvicornWorker` workers for production-grade process management
- Health check endpoint now returns version and uptime information
- Readiness check endpoint verifies data store accessibility and respects shutdown state
- Docker HEALTHCHECK timeout increased and made configurable via `HEALTH_CHECK_TIMEOUT` env var

### Added
- `VERSION` file for explicit version tracking
- `gunicorn==25.1.0` production dependency for multi-worker process management
- `WEB_CONCURRENCY` and `HEALTH_CHECK_TIMEOUT` environment variable support in Docker
- Transitive dev dependencies pinned in `requirements-dev.txt` for reproducible dev environments

## [0.3.0] - 2026-02-20

### Added
- Graceful shutdown handling via SIGTERM/SIGINT signal handlers using FastAPI lifespan
- `pyproject.toml` with `requires-python = ">=3.12"` for Python version pinning
- Development setup instructions in README.md
- Git tag `v0.1.0` for initial release version tracking

### Changed
- Application version bumped to 0.3.0

## [0.2.0] - 2026-02-20

### Security
- SECRET_KEY no longer defaults to an empty string; an ephemeral key is auto-generated if unset, with a runtime warning urging operators to set it explicitly
- Dockerfile now applies OS-level security updates during build
- Application code is mounted read-only inside the container
- Non-root user shell set to `/usr/sbin/nologin`

### Changed
- Health check uses `127.0.0.1` instead of `localhost` for reliable container networking
- All transitive Python dependencies are pinned to exact versions in `requirements.txt` for reproducible builds

### Added
- `requirements-dev.txt` with testing and linting tools (pytest, black, flake8, mypy)
- `CHANGELOG.md` for structured release notes

## [0.1.0] - 2026-02-20

### Added
- Initial flight booking agent REST API
- Flight search and booking endpoints
- Docker container packaging with multi-stage build
- Health and readiness check endpoints
