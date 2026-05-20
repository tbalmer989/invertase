import json
import logging
import re
from typing import Optional, List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

try:
    import trafilatura
except Exception:  # pragma: no cover - optional dependency
    trafilatura = None

logger = logging.getLogger(__name__)


def fetch_url(url: str, timeout: int = 10) -> Optional[str]:
    headers = {"User-Agent": "genkitx-readability/0.1 (+https://example.com)"}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def resolve_url(base: Optional[str], link: str) -> str:
    if not link:
        return link
    if base:
        return urljoin(base, link.strip())
    return link.strip()


def _clean_soup(soup: BeautifulSoup):
    for tag in soup(["script", "style", "noscript", "iframe", "header", "footer", "nav", "form", "aside"]):
        tag.decompose()


def _remove_unwanted_sections(soup: BeautifulSoup, *, remove_related: bool = False, remove_invite: bool = False):
    """Heuristic removal of sections such as related-content blocks or
    invitations to comment/get in touch.

    This uses class/id matching and heading text heuristics to remove nodes
    that are unlikely to be part of the main article.
    """
    if not (remove_related or remove_invite):
        return

    # Remove elements by class or id that explicitly mention related, ad, promo, or sidebar content.
    unwanted_keys = (
        "related",
        "related-content",
        "related-topics",
        "related-articles",
        "see-also",
        "more-on",
        "relatedstories",
        "recommend",
        "recommendation",
        "advert",
        "ads",
        "banner",
        "promo",
        "newsletter",
        "subscribe",
        "subscription",
        "sponsored",
        "sidebar",
        "cookie",
        "modal",
        "paywall",
        "overlay",
    )

    def is_unwanted_attr(value: str) -> bool:
        lowercase = value.lower()
        return any(key in lowercase for key in unwanted_keys)

    for tag in list(soup.find_all(attrs={"class": True})):
        classes = " ".join(tag.get("class") or [])
        if is_unwanted_attr(classes):
            tag.decompose()
    for tag in list(soup.find_all(attrs={"id": True})):
        idval = (tag.get("id") or "").lower()
        if is_unwanted_attr(idval):
            tag.decompose()
    for tag in list(soup.find_all(attrs={"aria-label": True})):
        if is_unwanted_attr(tag.get("aria-label", "")):
            tag.decompose()
    for tag in list(soup.find_all(attrs={"role": True})):
        role = (tag.get("role") or "").lower()
        if role in ("complementary", "banner", "navigation", "search", "contentinfo", "dialog"):
            tag.decompose()

    # Remove headings that indicate related content and their nearby containers
    related_heading_re = re.compile(r"^(related|related content|related topics|you may also like|you might also like|more on this|related articles|related stories|see also)$", re.I)
    for h in list(soup.find_all(re.compile(r"^h[1-6]$"))):
        text = (h.get_text(" ", strip=True) or "").strip()
        if related_heading_re.match(text):
            parent = h.find_parent()
            if parent and parent.name not in ("article", "main"):
                parent.decompose()
            else:
                # remove header and its following siblings until next header
                next_sib = h.next_sibling
                h.decompose()
                while next_sib is not None:
                    if getattr(next_sib, "name", "") and re.match(r"^h[1-6]$", getattr(next_sib, "name", "")):
                        break
                    nxt = next_sib.next_sibling
                    try:
                        next_sib.decompose()
                    except Exception:
                        pass
                    next_sib = nxt

    # Invitations / comments heuristics: search for phrases indicating engagement
    if remove_invite:
        invite_phrases = [
            # English
            "get in touch",
            "contact us",
            "share your views",
            "leave a comment",
            "leave a reply",
            "join the conversation",
            "tell us",
            "have your say",
            "add your comment",
            "comment",
            "comments",
            "feedback",
            # Spanish
            "déjanos un comentario",
            "deja tu comentario",
            "comenta abajo",
            "comenta",
            "escribe un comentario",
            # French
            "laissez un commentaire",
            "laisser un commentaire",
            "partagez votre avis",
            "donnez votre avis",
            # German
            "hinterlassen Sie einen Kommentar",
            "hinterlasse einen kommentar",
            "teilen Sie Ihre Meinung",
            "teilen sie ihre meinung",
            # Portuguese
            "deixe um comentário",
            "comente abaixo",
            "compartilhe sua opinião",
        ]
        invite_re = re.compile("|".join(re.escape(s) for s in invite_phrases), re.I)
        for tag in list(soup.find_all(["p", "div", "section", "aside"])):
            text = (tag.get_text(" ", strip=True) or "").strip()
            if text and invite_re.search(text):
                tag.decompose()


def _meta_content(soup: BeautifulSoup, keys: List[str]) -> Optional[str]:
    for key in keys:
        tag = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
        if tag and tag.get("content"):
            return tag["content"].strip()
    return None


def _extract_json_ld(soup: BeautifulSoup) -> List[dict]:
    json_ld = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            content = script.string
            if not content:
                continue
            parsed = json.loads(content)
            if isinstance(parsed, list):
                json_ld.extend(parsed)
            else:
                json_ld.append(parsed)
        except Exception:
            continue
    return json_ld


def _get_json_ld_field(json_ld: List[dict], field: str) -> Optional[str]:
    for entry in json_ld:
        if field in entry and entry[field]:
            value = entry[field]
            if isinstance(value, dict):
                return value.get("name")
            if isinstance(value, list):
                return value[0]
            return str(value)
    return None


def _extract_metadata(soup: BeautifulSoup) -> dict:
    json_ld = _extract_json_ld(soup)
    title = _meta_content(soup, ["og:title", "twitter:title"]) or (soup.title.string.strip() if soup.title else None)
    description = _meta_content(soup, ["og:description", "twitter:description", "description"])
    author = _meta_content(soup, ["article:author", "author"])
    publish_date = _meta_content(soup, ["article:published_time", "og:updated_time", "date", "publication_date"])
    language = (soup.html.attrs.get("lang") if soup.html and soup.html.attrs.get("lang") else None)

    if json_ld:
        author = author or _get_json_ld_field(json_ld, "author")
        publish_date = publish_date or _get_json_ld_field(json_ld, "datePublished")
        title = title or _get_json_ld_field(json_ld, "headline")
        description = description or _get_json_ld_field(json_ld, "description")

    if not language:
        locale = _meta_content(soup, ["og:locale", "dc.language"])
        language = locale.split("_")[0] if locale else None

    return {
        "title": title,
        "description": description,
        "author": author,
        "publish_date": publish_date,
        "language": language,
        "top_image": _meta_content(soup, ["og:image", "twitter:image"]),
        "json_ld": json_ld,
    }


def _score_candidate_block(block: BeautifulSoup) -> int:
    text = block.get_text(" ", strip=True) or ""
    if len(text) < 50:
        return 0

    score = len(text)
    if block.find(re.compile(r"^h[1-6]$")):
        score += 2000
    score += len(block.find_all("p")) * 400

    prefix = text[:200]
    if re.search(r"\b(function\s*\(|document\.querySelector|googletag|window\.location|var\s+\w+|const\s+\w+|let\s+\w+)\b", prefix):
        score -= 10000

    return score


def _select_main_content(soup: BeautifulSoup) -> Optional[BeautifulSoup]:
    # Prefer the highest-scoring semantic block, favoring real article text over code
    # or navigation containers.
    article_elements = soup.find_all("article")
    if article_elements:
        return max(article_elements, key=_score_candidate_block)

    main_elements = soup.find_all("main")
    if main_elements:
        return max(main_elements, key=_score_candidate_block)

    blocks = soup.find_all(["section", "div"])
    if not blocks:
        return soup
    return max(blocks, key=_score_candidate_block)


def _filter_text_sections(text: str, *, remove_related: bool = False, remove_invite: bool = False) -> str:
    # Always remove low-value page chrome such as advertisement blocks.
    ad_header_re = re.compile(r"^(advertisement|hide ad|sponsored|sponsored content|read more|sign up|newsletter|subscribe|subscription|follow us)$", re.I)
    ad_phrase_re = re.compile(r"(advertisement|hide ad|sponsored|subscribe|newsletter|sign up|read more)", re.I)
    related_header_re = re.compile(r"^(related|related content|related topics|you may also like|you might also like|more on this|related articles|related stories|see also)$", re.I)
    invite_phrases = [
        # English
        "get in touch",
        "contact us",
        "share your views",
        "leave a comment",
        "leave a reply",
        "join the conversation",
        "tell us",
        "have your say",
        "add your comment",
        "comment",
        "comments",
        "feedback",
        # Spanish
        "déjanos un comentario",
        "deja tu comentario",
        "comenta abajo",
        "comenta",
        "escribe un comentario",
        # French
        "laissez un commentaire",
        "laisser un commentaire",
        "partagez votre avis",
        "donnez votre avis",
        # German
        "hinterlassen Sie einen Kommentar",
        "hinterlasse einen kommentar",
        "teilen Sie Ihre Meinung",
        "teilen sie ihre meinung",
        # Portuguese
        "deixe um comentário",
        "comente abaixo",
        "compartilhe sua opinião",
    ]
    invite_re = re.compile("|".join(re.escape(s) for s in invite_phrases), re.I)

    lines = text.splitlines()
    out_lines: list[str] = []
    skip = False
    for line in lines:
        stripped = line.strip()
        if ad_header_re.match(stripped) or (len(stripped.split()) <= 5 and ad_phrase_re.search(stripped)):
            skip = True
            continue
        if remove_related and related_header_re.match(stripped):
            skip = True
            continue
        if remove_invite and invite_re.search(stripped):
            skip = True
            continue
        if skip:
            if stripped == "":
                skip = False
                continue
            if ad_header_re.match(stripped) or (len(stripped.split()) <= 5 and ad_phrase_re.search(stripped)):
                continue
            skip = False
        out_lines.append(line)
    return "\n".join(out_lines).strip()


def extract_main_content(html: str, url: Optional[str] = None, *, remove_related: bool = False, remove_invite: bool = False) -> dict:
    """Extract main content and metadata from HTML."""
    soup = BeautifulSoup(html, "html5lib")
    has_semantic = bool(soup.find(["article", "main"]))

    if trafilatura:
        try:
            downloaded = trafilatura.extract(html, include_comments=False, include_tables=False, url=url)
            if downloaded:
                metadata = _extract_metadata(soup)
                text = downloaded.strip()
                content = _select_main_content(soup)
                fallback_text = content.get_text("\n", strip=True) if content else None
                # If semantic HTML is present and the trafilatura output looks like
                # page chrome rather than the article body, use the DOM-based fallback.
                bad_output_re = re.compile(r"(advertisement|hide ad|document\.querySelector|googletag|Search if)", re.I)
                if has_semantic and (
                    bad_output_re.search(text)
                    or (fallback_text and len(fallback_text) > 200 and len(text) > len(fallback_text) * 1.8)
                ):
                    raise ValueError("trafilatura output appears to contain page chrome")
                # Apply simple text filters when requested (trafilatura output is plain text)
                text = _filter_text_sections(text, remove_related=remove_related, remove_invite=remove_invite)
                if metadata.get("description"):
                    excerpt = metadata.get("description")
                elif len(text) > 512:
                    excerpt = text[:512] + "..."
                else:
                    excerpt = text
                images: List[str] = []
                if content:
                    for img in content.find_all("img"):
                        src = img.get("src") or img.get("data-src")
                        if src:
                            images.append(resolve_url(url, src))
                top_image = metadata.get("top_image")
                if top_image:
                    top_image = resolve_url(url, top_image)
                elif images:
                    top_image = images[0]
                return {
                    "title": metadata.get("title"),
                    "text": text,
                    "html": None,
                    "author": metadata.get("author"),
                    "publish_date": metadata.get("publish_date"),
                    "language": metadata.get("language"),
                    "top_image": top_image,
                    "images": images,
                    "excerpt": excerpt,
                }
        except Exception:
            logger.debug("trafilatura extraction failed, falling back", exc_info=True)

    _clean_soup(soup)
    # Apply DOM-level removals before metadata/content selection
    _remove_unwanted_sections(soup, remove_related=remove_related, remove_invite=remove_invite)
    metadata = _extract_metadata(soup)
    content = _select_main_content(soup)
    text = content.get_text("\n", strip=True) if content else soup.get_text("\n", strip=True)

    images: List[str] = []
    if content:
        for img in content.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src:
                images.append(resolve_url(url, src))

    top_image = metadata.get("top_image")
    if top_image:
        top_image = resolve_url(url, top_image)
    elif images:
        top_image = images[0]

    # Apply text-level filtering for fallbacks as well
    text = _filter_text_sections(text, remove_related=remove_related, remove_invite=remove_invite)

    if metadata.get("description"):
        excerpt = metadata.get("description")
    elif len(text) > 512:
        excerpt = text[:512] + "..."
    else:
        excerpt = text

    return {
        "title": metadata.get("title"),
        "text": text,
        "html": str(content) if content else None,
        "author": metadata.get("author"),
        "publish_date": metadata.get("publish_date"),
        "language": metadata.get("language"),
        "top_image": top_image,
        "images": images,
        "excerpt": excerpt,
    }
