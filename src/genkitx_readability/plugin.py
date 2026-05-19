from typing import Optional
from .utils import fetch_url, extract_main_content
from .schema import ReadabilityResult


def extract_url_content(url: str, max_chars: Optional[int] = None) -> dict:
    """Fetch a URL and return structured main content as a dict.

    Args:
        url: The page URL to fetch.
        max_chars: If set, truncate the `text` field to this many characters.

    Returns:
        A serializable dict representing the extracted content.
    """
    html = fetch_url(url)
    data = extract_main_content(html, url=url)
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
    )
    return result.to_dict()


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
            "input": {"type": "object", "properties": {"url": {"type": "string"}, "max_chars": {"type": ["integer", "null"]}}},
            "output": {"type": "object"},
        },
    }
