# genkitx-readability

Lightweight Genkit plugin to extract clean, structured main content from web URLs for use with LLMs.

## Installation

```bash
python3 -m pip install -e .
```

## Usage

```python
from genkitx_readability import extract_url_content

result = extract_url_content("https://example.com/article")
print(result["title"])
print(result["excerpt"])
```

## Testing

```bash
python3 -m pip install -e .[test]
python3 -m pytest -q
```

## Maintenance

- Plugin entry point: `genkitx_readability.plugin:register`
- Core extraction: `src/genkitx_readability/utils.py`
- Structured output: `src/genkitx_readability/schema.py`
- Agent skill guide: `skills/genkitx-readability-skill.md`
