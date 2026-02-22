# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-02-22

### Added
- Flight search and booking REST API with FastAPI
- In-memory booking store with create, retrieve, and cancel operations
- Flight search by origin, destination, date, and cabin class
- Health check endpoint with version and uptime reporting
- Docker multi-stage build with non-root user
- CI pipeline with dependency vulnerability scanning (pip-audit)
- Environment-based configuration (HOST, PORT, LOG_LEVEL)
