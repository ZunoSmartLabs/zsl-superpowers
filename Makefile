.PHONY: lint format sync-books check-upstream-books

lint:
	uvx ruff check .
	uvx basedpyright skills/productivity/timesheet/scripts/digest_sessions.py

format:
	uvx ruff format .

sync-books:
	python3 scripts/sync_book_rules.py

check-upstream-books:
	bash scripts/check_upstream_books.sh
