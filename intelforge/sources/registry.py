from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SourceCapability:
    source_id: str
    organization: str
    type: str
    capabilities: tuple[str, ...]
    date_fields: tuple[str, ...]
    official: bool
    access_method: str
    base_url: str


class SourceCapabilityRegistry:
    def __init__(self) -> None:
        specs = [
            ("UN_TREATY_COLLECTION", "United Nations", "TREATY_DATABASE", ("treaty_text", "ratification", "signature", "status", "entry_into_force"), ("signature_date", "ratification_date", "entry_into_force"), "OFFICIAL_SEARCHABLE_WEBSITE", "https://treaties.un.org"),
            ("UN_DIGITAL_LIBRARY", "United Nations", "DOCUMENT_REPOSITORY", ("documents", "resolutions", "statements"), ("publication_date",), "OFFICIAL_SEARCHABLE_WEBSITE", "https://digitallibrary.un.org"),
            ("UN_COMTRADE", "United Nations", "DATASET", ("trade_statistics",), ("reference_period", "publication_date"), "API", "https://comtradeapi.un.org"),
            ("ICJ", "International Court of Justice", "COURT_RECORD", ("judgments", "orders", "cases"), ("decision_date",), "OFFICIAL_SEARCHABLE_WEBSITE", "https://www.icj-cij.org"),
            ("IAEA", "International Atomic Energy Agency", "DOCUMENT_REPOSITORY", ("safeguards", "reports"), ("publication_date",), "OFFICIAL_SEARCHABLE_WEBSITE", "https://www.iaea.org"),
            ("WHO", "World Health Organization", "OFFICIAL_DATABASE", ("health_statistics", "reports"), ("publication_date",), "OFFICIAL_SEARCHABLE_WEBSITE", "https://www.who.int"),
            ("ILO", "International Labour Organization", "OFFICIAL_DATABASE", ("labour_statistics", "standards"), ("publication_date",), "OFFICIAL_SEARCHABLE_WEBSITE", "https://www.ilo.org"),
            ("FAO", "Food and Agriculture Organization", "DATASET", ("food_statistics",), ("reference_period",), "OFFICIAL_DOWNLOADABLE_DATASET", "https://www.fao.org/faostat"),
            ("WTO", "World Trade Organization", "DOCUMENT_REPOSITORY", ("trade_policy", "disputes"), ("publication_date",), "OFFICIAL_SEARCHABLE_WEBSITE", "https://www.wto.org"),
            ("UNFCCC", "UNFCCC Secretariat", "DOCUMENT_REPOSITORY", ("climate_commitments", "decisions"), ("publication_date",), "OFFICIAL_SEARCHABLE_WEBSITE", "https://unfccc.int"),
            ("INTERPOL", "INTERPOL", "OFFICIAL_SEARCHABLE_WEBSITE", ("notices", "crime_reports"), ("publication_date",), "OFFICIAL_SEARCHABLE_WEBSITE", "https://www.interpol.int"),
        ]
        self._items = {s[0]: SourceCapability(s[0], s[1], s[2], s[3], s[4], True, s[5], s[6]) for s in specs}

    def for_need(self, need: str) -> list[SourceCapability]:
        return [item for item in self._items.values() if need in item.capabilities]

    def all(self) -> list[dict]:
        return [asdict(item) for item in self._items.values()]
