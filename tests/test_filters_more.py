import types

from genkitx_readability import extract_url_content


SIMPLE_HTML_TEMPLATE = """
<html lang="en">
  <head><title>Test</title></head>
  <body>
    {body}
  </body>
</html>
"""


class DummyResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("HTTP %s" % self.status_code)


def _fake_get_factory(html):
    def fake_get(url, headers=None, timeout=None):
        return DummyResponse(html)

    return fake_get


def test_remove_related_by_id_and_heading(monkeypatch):
    body = """
    <article>
      <h1>Title</h1>
      <p>Main content.</p>
      <div id="related-articles">
        <h2>Related articles</h2>
        <p>Topic A</p>
      </div>
    </article>
    """
    html = SIMPLE_HTML_TEMPLATE.format(body=body)

    import requests
    import genkitx_readability.utils as utils

    monkeypatch.setattr(utils, "trafilatura", None, raising=False)
    monkeypatch.setattr(requests, "get", _fake_get_factory(html))

    out = extract_url_content("https://example.test/article")
    assert "Related articles" in out["text"]

    out2 = extract_url_content("https://example.test/article", exclude_related=True)
    assert "Related articles" not in out2["text"]


def test_remove_invite_variants(monkeypatch):
    body = """
    <article>
      <h1>Title</h1>
      <p>Main content.</p>
      <section>
        <p>Contact us to learn more about this story.</p>
      </section>
    </article>
    """
    html = SIMPLE_HTML_TEMPLATE.format(body=body)

    import requests
    import genkitx_readability.utils as utils

    monkeypatch.setattr(utils, "trafilatura", None, raising=False)
    monkeypatch.setattr(requests, "get", _fake_get_factory(html))

    out = extract_url_content("https://example.test/article")
    assert "Contact us" in out["text"]

    out2 = extract_url_content("https://example.test/article", exclude_invite=True)
    assert "Contact us" not in out2["text"]


def test_trafilatura_text_filtering(monkeypatch):
    # Simulate trafilatura returning a combined text containing related and invite lines
    plain_text = "Title\nMain paragraph.\nRelated topics\nTopic A\nLeave a comment below to share your views.\n"
    html = SIMPLE_HTML_TEMPLATE.format(body="<article><h1>Title</h1></article>")

    import requests
    import genkitx_readability.utils as utils

    fake_traf = types.SimpleNamespace()
    fake_traf.extract = lambda html_arg, **kwargs: plain_text
    monkeypatch.setattr(utils, "trafilatura", fake_traf, raising=False)
    monkeypatch.setattr(requests, "get", _fake_get_factory(html))

    out = extract_url_content("https://example.test/article")
    assert "Related topics" in out["text"]
    assert "Leave a comment" in out["text"]

    out2 = extract_url_content("https://example.test/article", exclude_related=True, exclude_invite=True)
    assert "Related topics" not in out2["text"]
    assert "Leave a comment" not in out2["text"]


def test_do_not_remove_similar_but_not_heading(monkeypatch):
    # Heading that contains 'related' but is not an exact match should be preserved
    body = """
    <article>
      <h1>Title</h1>
      <h2>More related research</h2>
      <p>This paragraph should remain.</p>
    </article>
    """
    html = SIMPLE_HTML_TEMPLATE.format(body=body)

    import requests
    import genkitx_readability.utils as utils

    monkeypatch.setattr(utils, "trafilatura", None, raising=False)
    monkeypatch.setattr(requests, "get", _fake_get_factory(html))

    out = extract_url_content("https://example.test/article", exclude_related=True)
    assert "More related research" in out["text"]
    assert "This paragraph should remain." in out["text"]
