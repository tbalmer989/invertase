# Genkitx Readability — Agent Skill

Purpose: Help an AI coding assistant understand how to maintain and extend the `genkitx-readability` plugin.

Maintenance notes:

- **Entry point**: `genkitx_readability.plugin:register` — returns a simple dict describing the tool.
- **Core extraction**: `src/genkitx_readability/utils.py` — `extract_main_content()` and `fetch_url()`.
- **Structured output**: `src/genkitx_readability/schema.py` defines `ReadabilityResult`.

Extension points:

- Swap or configure extraction backend: prefer `trafilatura` (already optional). To add `readability-lxml`, update `utils.py` to try it before fallback.
- Add richer metadata: parse OpenGraph and JSON-LD in `utils.extract_main_content`.
- Improve image handling: resolve relative URLs using `urllib.parse.urljoin` and optionally download thumbnails.

Testing & CI:

- Tests live under `tests/` and should mock network calls. Use `pytest` and `requests-mock`/`responses`.
- The package defines `project.optional-dependencies.test` in `pyproject.toml` to install `pytest` with `pip install -e .[test]`.
- A GitHub Actions workflow exists at `.github/workflows/ci.yml` to run the test matrix on push and PR.

Common pitfalls:

- Network fetching should use timeouts and sensible user-agent headers.
- LLM-ready output should include both `text` (plaintext) and `excerpt`; keep HTML optional.
- Truncate long content for cost control before sending to models.

Developer workflow:

1. Create feature branch.
2. Run tests: `pip install -e .[test] && pytest`.
3. Update `pyproject.toml` for new dependencies and add changelog entry.
