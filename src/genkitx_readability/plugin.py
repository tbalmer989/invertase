import json
from typing import Optional
from .utils import fetch_url, extract_main_content
from .schema import ReadabilityResult


def _format_result(result: dict, output: str = "text") -> str:
    if output == "json":
        return json.dumps(result, indent=2, default=str)

    lines = []
    for key, value in result.items():
        if value is None:
            continue
        if isinstance(value, list):
            value = ", ".join(str(item) for item in value)
        lines.append(f"{key}: {value}")
    return "\n".join(lines)


def extract_url_content(
    url: str,
    max_chars: Optional[int] = None,
    exclude_related: bool = False,
    exclude_invite: bool = False,
    output: str = "text",
    output_file: Optional[str] = None,
) -> dict:
    """Fetch a URL and return structured main content as a dict.

    Args:
        url: The page URL to fetch.
        max_chars: If set, truncate the `text` field to this many characters.
        output: Output format for the final result, either 'text' or 'json'.
        output_file: Optional path to write the formatted output to.

    Returns:
        A serializable dict representing the extracted content.
    """
    html = fetch_url(url)
    data = extract_main_content(html, url=url, remove_related=exclude_related, remove_invite=exclude_invite)
    text = data.get("text", "") or ""
    if max_chars is not None and len(text) > max_chars:
        text = text[:max_chars]

    result = ReadabilityResult(
        url=url,
        title=data.get("title"),
        author=data.get("author"),
        publish_date=data.get("publish_date"),
        language=data.get("language"),
        text=text,
        html=data.get("html"),
        excerpt=data.get("excerpt"),
        top_image=data.get("top_image"),
        images=list(data.get("images") or []),
    ).to_dict()

    if output_file:
        formatted = _format_result(result, output=output)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(formatted)

    return result


def register():
    """Return a simple descriptor used by Genkit hosts to discover the tool.

    The descriptor is a dictionary with `name`, `description`, and `callable` keys.
    Host apps may expect a different shape; adjust as needed.
    """
    return {
        "name": "genkitx.readability.extract_url",
        "description": "Extracts main readable content from a web URL and returns a structured dict.",
        "callable": extract_url_content,
        "schema": {
            "input": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "max_chars": {"type": ["integer", "null"]},
                    "exclude_related": {"type": "boolean"},
                    "exclude_invite": {"type": "boolean"},
                    "output": {"type": "string", "enum": ["text", "json"]},
                    "output_file": {"type": ["string", "null"]},
                },
            },
            "output": {"type": "object"},
        },
    }
