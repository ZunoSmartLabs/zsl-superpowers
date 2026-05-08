.PHONY: lint format

lint:
	uvx ruff check .
	uvx basedpyright skills/productivity/timesheet/scripts/digest_sessions.py

format:
	uvx ruff format .
