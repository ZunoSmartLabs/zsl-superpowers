.PHONY: lint format test sync-books check-upstream-books docs docs-serve

lint:
	uvx ruff check .
	uvx basedpyright skills/productivity/timesheet/scripts/digest_sessions.py \
		skills/productivity/write-a-skill/scripts/check-description-length.py

format:
	uvx ruff format .

# Tests for the deterministic-gate scripts bundled under skills/**/scripts/.
# Python scripts via pytest; shell scripts via their own assertion runners.
test:
	uvx --with pytest pytest skills -q
	bash skills/engineering/tdd-parallel/scripts/tests/test_preflight.sh
	bash skills/remote-agents/afk-fanout/scripts/tests/test_write_afk_entry.sh

# Docs run on mkdocs-material with the `social` plugin, which needs cairo at
# build time (CI installs it via apt; macOS via `brew install cairo`). uvx
# can't see Homebrew's cairo — macOS strips DYLD_* when uv's hardened binary
# spawns Python — so docs use a venv (Homebrew's Python finds cairo) instead.
.venv:
	python3 -m venv .venv
	.venv/bin/pip install --quiet --upgrade pip
	.venv/bin/pip install --quiet 'mkdocs-material[imaging]'

# Strict build — the exact gate the GitHub Pages deploy runs on push to main.
docs: .venv
	.venv/bin/mkdocs build --strict

# Live preview at http://127.0.0.1:8000 with auto-reload.
docs-serve: .venv
	.venv/bin/mkdocs serve

sync-books:
	python3 scripts/sync_book_rules.py

check-upstream-books:
	bash scripts/check_upstream_books.sh
