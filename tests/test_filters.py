from genkitx_readability import extract_url_content


SAMPLE_HTML_WITH_REL = """
<html lang="en">
  <head>
    <title>Filter Test</title>
  </head>
  <body>
    <article>
      <h1>Article Title</h1>
      <p>Intro paragraph of the article.</p>
      <p>Main content paragraph.</p>
      <div class="related">
        <h2>Related topics</h2>
        <ul>
          <li><a href="/a">Topic A</a></li>
          <li><a href="/b">Topic B</a></li>
        </ul>
      </div>
      <div class="invite">
        <p>Leave a comment below to share your views.</p>
      </div>
    </article>
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


def test_exclude_related_and_invite(monkeypatch):
    def fake_get(url, headers=None, timeout=None):
      return DummyResponse(SAMPLE_HTML_WITH_REL)

    import requests
    import genkitx_readability.utils as utils

    # Force the fallback path to ensure aside/invite content is included
    monkeypatch.setattr(utils, "trafilatura", None, raising=False)
    monkeypatch.setattr(requests, "get", fake_get)

    out = extract_url_content("https://example.test/article")
    # By default related content and invites appear in extracted text
    assert "Related topics" in out["text"] or "Topic A" in out["text"]
    assert "Leave a comment" in out["text"] or "share your views" in out["text"]

    out_filtered = extract_url_content("https://example.test/article", exclude_related=True, exclude_invite=True)
    # With flags enabled, related and invite content should be removed
    assert "Related topics" not in out_filtered["text"]
    assert "Topic A" not in out_filtered["text"]
    assert "Leave a comment" not in out_filtered["text"]
