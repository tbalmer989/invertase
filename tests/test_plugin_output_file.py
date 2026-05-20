from genkitx_readability import extract_url_content


SAMPLE_HTML = """
<html lang="en">
  <head>
    <title>Test Article</title>
    <meta property="og:title" content="OG Test Article" />
    <meta property="og:description" content="This is a clean, descriptive excerpt." />
  </head>
  <body>
    <article>
      <h1>Test Article</h1>
      <p>This is the first paragraph of the article.</p>
      <p>This is the second paragraph.</p>
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
            raise Exception(f"HTTP {self.status_code}")


def _fake_get_factory(html):
    def fake_get(url, headers=None, timeout=None):
        return DummyResponse(html)

    return fake_get


def test_extract_url_content_writes_text_file(tmp_path, monkeypatch):
    import requests

    monkeypatch.setattr(requests, "get", _fake_get_factory(SAMPLE_HTML))

    out_file = tmp_path / "article.txt"
    result = extract_url_content(
        "https://example.test/article",
        output="text",
        output_file=str(out_file),
    )

    assert result["title"] == "OG Test Article"
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "title: OG Test Article" in content
    assert "text: Test Article" in content


def test_extract_url_content_writes_json_file(tmp_path, monkeypatch):
    import requests

    monkeypatch.setattr(requests, "get", _fake_get_factory(SAMPLE_HTML))

    out_file = tmp_path / "article.json"
    result = extract_url_content(
        "https://example.test/article",
        output="json",
        output_file=str(out_file),
    )

    assert result["title"] == "OG Test Article"
    assert out_file.exists()
    json_text = out_file.read_text(encoding="utf-8")
    assert "\"title\": \"OG Test Article\"" in json_text
    assert "\"text\": \"Test Article" in json_text
