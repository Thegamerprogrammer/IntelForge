"""Evidence-first incident extraction from retrieved primary documents."""
from __future__ import annotations

import hashlib
import re
from datetime import date

from ..core.models import Incident, Source
from .acquisition import RetrievedDocument

_EVENT = re.compile(r"(?P<sentence>[^.]{30,500}\b(?:investigat(?:ed|ion)|seized|sanctioned|violat(?:ed|ion)|procure(?:d|ment)|export(?:ed| controls?)|incident|operation|arrested)\b[^.]{0,300}\.)", re.I)

class IncidentExtractor:
    def extract(self, documents: list[RetrievedDocument], target: str, freeze_date: date | None) -> list[Incident]:
        incidents: dict[str, Incident] = {}
        for document in documents:
            if freeze_date and document.publication_date and document.publication_date > freeze_date:
                continue
            for match in _EVENT.finditer(document.content):
                conduct = " ".join(match.group("sentence").split())
                if target.casefold() not in conduct.casefold():
                    continue
                key = hashlib.sha256(re.sub(r"\W+", "", conduct.casefold()).encode()).hexdigest()[:12]
                source = Source(document.source_id, document.url, document.title, "RETRIEVED_DOCUMENT", urlparse_official(document.url), document.publication_date, usable=True, content=conduct)
                if key in incidents:
                    incidents[key].sources.append(source)
                else:
                    event_id = f"INC-{len(incidents) + 1:06d}"
                    incidents[key] = Incident(event_id, target, conduct[:120], conduct, document.publication_date, None, [target], [source], .55)
        return list(incidents.values())

def urlparse_official(url: str) -> bool:
    return any(host in url.casefold() for host in (".un.org", ".int", ".gov", ".europa.eu"))
