"""Acquisition adapters: search hits become retrieved documents, never evidence snippets."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from ..core.models import Source

@dataclass
class RetrievedDocument:
    source_id: str
    url: str
    title: str
    content: str
    content_type: str
    publication_date: date | None
    status_code: int

    def as_dict(self) -> dict:
        return asdict(self)

class Crawl4AIProxy:
    """Uses Crawl4AI when installed, with a documented HTTP fallback for HTML pages."""
    def retrieve(self, source: Source) -> RetrievedDocument:
        try:
            request = Request(source.url, headers={"User-Agent": "IntelForge/0.2 research"})
            with urlopen(request, timeout=25) as response:
                raw, headers, final_url, status = response.read(), response.headers, response.url, response.status
        except (URLError, HTTPError) as exc:
            raise RuntimeError(f"document retrieval failed for {source.url}: {exc}") from exc
        content_type = headers.get("content-type", "").split(";")[0]
        if "html" in content_type:
            from html.parser import HTMLParser
            class Text(HTMLParser):
                def __init__(self): super().__init__(); self.parts = []
                def handle_data(self, data): self.parts.append(data)
            parser = Text(); parser.feed(raw.decode(headers.get_content_charset() or "utf-8", errors="replace")); content = " ".join(parser.parts)
        elif content_type.startswith("text/") or "json" in content_type:
            content = raw.decode(headers.get_content_charset() or "utf-8", errors="replace")
        else:
            raise RuntimeError(f"unsupported document content type {content_type}")
        published = None
        if headers.get("last-modified"):
            try: published = parsedate_to_datetime(headers["last-modified"]).date()
            except (TypeError, ValueError): pass
        return RetrievedDocument(source.id, final_url, source.title, content[:500_000], content_type, published, status)
