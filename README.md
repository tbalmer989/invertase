# genkitx-readability

A lightweight Genkit plugin that extracts clean, structured main content from web URLs. The plugin is designed for use in Genkit host applications and for direct Python consumption.

## Functionality

- Fetches HTML from a provided URL
- Extracts the main body of an article or text-heavy page
- Cleans out navigation, ads, scripts, and boilerplate
- Optionally removes related-content sections and invitation/comment sections
- Extracts metadata such as title, author, publish date, language, and top image
- Supports output as plain text or JSON
- Can write formatted output directly to a file

## Installation

```bash
cd /home/orwell/projects/invertase
python3 -m pip install -e .
```

For test dependencies:

```bash
python3 -m pip install -e .[test]
```

## Usage

### Python API

```python
from genkitx_readability import extract_url_content

result = extract_url_content(
    "https://example.com/article",
    max_chars=1200,
    exclude_related=True,
    exclude_invite=True,
    output="json",
    output_file="article.json",
)

print(result["title"])
print(result["text"][:300])
```

### Plugin options

- `url`: URL to fetch
- `max_chars`: truncate the extracted text to this length
- `exclude_related`: remove related-content/topics sections
- `exclude_invite`: remove comment/invitation blocks
- `output`: `text` or `json`
- `output_file`: optional path to write formatted output

### Save text to a file

```python
extract_url_content(
    "https://example.com/article",
    output="text",
    output_file="article.txt",
)
```

### Save JSON to a file

```python
extract_url_content(
    "https://example.com/article",
    output="json",
    output_file="article.json",
)
```

## Using with genkit-base

The companion host app in `genkit-base` forwards the same plugin options.

```bash
genkit-base --output json --output-file article.json https://example.com/article
```

## Testing

```bash
cd /home/orwell/projects/invertase
python3 -m pytest -q
```

## Project structure

- `src/genkitx_readability/plugin.py`: plugin entry point and formatting/export support
- `src/genkitx_readability/utils.py`: HTML fetch and content extraction logic
- `src/genkitx_readability/schema.py`: result schema definition
- `tests/`: unit tests for extraction, filtering, and export behavior
- `skills/`: agent skill documentation for maintaining and extending the plugin
