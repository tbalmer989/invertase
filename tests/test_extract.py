import pytest
from types import SimpleNamespace

from genkitx_readability import extract_url_content
from genkitx_readability.utils import _filter_text_sections, extract_main_content


SAMPLE_HTML = """
<html lang="en">
  <head>
    <title>Test Article</title>
    <meta property="og:title" content="OG Test Article" />
    <meta property="og:description" content="This is a clean, descriptive excerpt." />
    <meta property="og:image" content="/images/og-hero.jpg" />
  </head>
  <body>
    <nav>Navigation</nav>
    <article>
      <h1>Test Article</h1>
      <p>This is the first paragraph of the article.</p>
      <p>This is the second paragraph.</p>
      <img src="/images/hero.jpg" />
    </article>
    <footer>Footer content</footer>
  </body>
<html>
"""


class DummyResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("HTTP %s" % self.status_code)


def test_extract_from_html_monkeypatch(monkeypatch):
    def fake_get(url, headers=None, timeout=None):
        return DummyResponse(SAMPLE_HTML)

    import requests

    monkeypatch.setattr(requests, "get", fake_get)

    out = extract_url_content("https://example.test/article")
    assert out["title"] == "OG Test Article"
    assert out["language"] == "en"
    assert out["excerpt"] == "This is a clean, descriptive excerpt."
    assert "first paragraph" in out["text"]
    assert out["top_image"] == "https://example.test/images/og-hero.jpg"
    assert out["images"] == ["https://example.test/images/hero.jpg"]


def test_selects_largest_article_tag(monkeypatch):
    html = """
    <html>
      <body>
        <article><p>Short article.</p></article>
        <article><p>Longer article body text with more article content.</p></article>
      </body>
    </html>
    """
    import genkitx_readability.utils as utils
    monkeypatch.setattr(utils, "trafilatura", None, raising=False)

    result = extract_main_content(html)
    assert "Longer article body text" in result["text"]
    assert "Short article." not in result["text"]


def test_filters_advertisements_from_text():
    sample = "Headline\nStory text.\nAdvertisement\nHide Ad\nStory continues."
    filtered = _filter_text_sections(sample, remove_related=True, remove_invite=True)
    assert "Advertisement" not in filtered
    assert "Hide Ad" not in filtered
    assert "Story text." in filtered
    assert "Story continues." in filtered
