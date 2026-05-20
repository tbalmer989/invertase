from genkitx_readability import extract_url_content


SAMPLES = {
    "spanish": (
        "<article><h1>Título</h1><p>Contenido principal.</p><p>Deja tu comentario abajo.</p></article>"
    ),
    "french": (
        "<article><h1>Titre</h1><p>Contenu principal.</p><p>Laissez un commentaire ci-dessous.</p></article>"
    ),
    "german": (
        "<article><h1>Titel</h1><p>Hauptinhalt.</p><p>Hinterlassen Sie einen Kommentar unten.</p></article>"
    ),
    "portuguese": (
        "<article><h1>Título</h1><p>Conteúdo principal.</p><p>Deixe um comentário abaixo.</p></article>"
    ),
    "plural_english": (
        "<article><h1>Title</h1><p>Main content.</p><p>Comments are welcome below.</p></article>"
    ),
}


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


def test_i18n_invite_phrases(monkeypatch):
    import requests
    import genkitx_readability.utils as utils

    monkeypatch.setattr(utils, "trafilatura", None, raising=False)

    for lang, body in SAMPLES.items():
        monkeypatch.setattr(requests, "get", _fake_get_factory(f"<html>{body}</html>"))
        out = extract_url_content("https://example.test/article")
        # ensure invite phrase shows by default
        assert out and isinstance(out.get("text"), str)
        assert len(out["text"]) > 0

        out_filtered = extract_url_content("https://example.test/article", exclude_invite=True)
        # ensure invite phrase removed
        assert out_filtered["text"] != out["text"]
        # basic check: the invite fragments should be absent
        lower = out_filtered["text"].lower()
        if lang == "spanish":
            assert "deja" not in lower and "comentario" not in lower
        if lang == "french":
            assert "laissez" not in lower and "commentaire" not in lower
        if lang == "german":
            assert "hinterlassen" not in lower and "kommentar" not in lower
        if lang == "portuguese":
            assert "deixe" not in lower and "comentário" not in lower or "comentario" not in lower
        if lang == "plural_english":
            assert "comments" not in lower
