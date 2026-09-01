from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CommitteeRecord:
    id: str
    aliases: tuple[str, ...]
    official_name: str
    parent_body: str
    type: str
    mandate: str
    jurisdiction: tuple[str, ...]
    topics_within: tuple[str, ...]
    topics_outside: tuple[str, ...]
    powers: tuple[str, ...]
    limitations: tuple[str, ...]
    legal_frameworks: tuple[str, ...]
    official_sources: tuple[str, ...]
    research_capabilities: tuple[str, ...]
    dataset_identifiers: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return asdict(self)


def _record(id: str, aliases: tuple[str, ...], name: str, parent: str, kind: str, mandate: str, topics: tuple[str, ...] = ()) -> CommitteeRecord:
    return CommitteeRecord(id, aliases, name, parent, kind, mandate, topics, topics, (), ("deliberate", "recommend"), ("no independent enforcement unless specified",), ("UN Charter",), ("UN_DIGITAL_LIBRARY", "UN_OFFICIAL_DOCUMENTS"), ("official_documents", "resolutions", "statements"))


class CommitteeRegistry:
    """Data-driven committee lookup; callers can register custom records."""
    def __init__(self, records: list[CommitteeRecord] | None = None) -> None:
        self._records = {r.id: r for r in (records or default_committees())}
        self._aliases = {alias.casefold(): r.id for r in self._records.values() for alias in (r.id, *r.aliases, r.official_name)}

    def resolve_id(self, value: str) -> str | None:
        return self._aliases.get(value.strip().casefold())

    def get(self, value: str) -> CommitteeRecord | None:
        identifier = self.resolve_id(value)
        return self._records.get(identifier) if identifier else None

    def register(self, record: CommitteeRecord) -> None:
        self._records[record.id] = record
        for alias in (record.id, *record.aliases, record.official_name):
            self._aliases[alias.casefold()] = record.id

    def all(self) -> list[CommitteeRecord]:
        return list(self._records.values())

    def register_crisis(self, *, identifier: str, name: str, aliases: tuple[str, ...] = (), simulation_date: str | None = None, historical_period: str | None = None, authority: tuple[str, ...] = (), directive_power: bool = True, fictional_rules: tuple[str, ...] = ()) -> CommitteeRecord:
        """Register a custom modern or historical crisis body without UN assumptions."""
        record = CommitteeRecord(identifier, aliases, name, "Custom MUN", "CRISIS", "Configurable crisis mandate.", authority, authority, (), (("issue directives" if directive_power else "deliberate"),), fictional_rules, (), (), ("simulation_date", "historical_period", "information_model"), tuple(filter(None, (simulation_date, historical_period))))
        self.register(record)
        return record


def default_committees() -> list[CommitteeRecord]:
    specs = [
        ("UNGA_FIRST", ("DISEC", "First Committee", "GA1"), "UN General Assembly First Committee", "UNGA", "UNGA_COMMITTEE", "Disarmament and international security.", ("disarmament", "security", "weapons", "technology")),
        ("UNGA_SECOND", ("ECOFIN", "Second Committee", "GA2"), "UN General Assembly Second Committee", "UNGA", "UNGA_COMMITTEE", "Economic and financial affairs.", ("development", "trade", "finance")),
        ("UNGA_THIRD", ("SOCHUM", "Third Committee", "GA3"), "UN General Assembly Third Committee", "UNGA", "UNGA_COMMITTEE", "Social, humanitarian and human rights affairs.", ("human rights", "humanitarian", "social")),
        ("UNGA_FOURTH", ("SPECPOL", "Fourth Committee", "GA4"), "UN General Assembly Fourth Committee", "UNGA", "UNGA_COMMITTEE", "Special political and decolonization affairs.", ("decolonization", "political")),
        ("UNGA_FIFTH", ("Fifth Committee", "GA5"), "UN General Assembly Fifth Committee", "UNGA", "UNGA_COMMITTEE", "Administrative and budgetary affairs.", ("budget", "administration")),
        ("UNGA_SIXTH", ("Sixth Committee", "GA6"), "UN General Assembly Sixth Committee", "UNGA", "UNGA_COMMITTEE", "Legal affairs.", ("international law", "legal")),
        ("UNGA_PLENARY", ("General Assembly", "GA Plenary"), "United Nations General Assembly Plenary", "UNGA", "UN_ORGAN", "General deliberative organ.", ("general",)),
        ("UNSC", ("Security Council",), "United Nations Security Council", "United Nations", "UN_ORGAN", "International peace and security.", ("peace", "security", "sanctions")),
        ("ECOSOC", ("Economic and Social Council",), "United Nations Economic and Social Council", "United Nations", "UN_ORGAN", "Economic, social and related work.", ("economic", "social", "development")),
        ("UNHRC", ("Human Rights Council",), "United Nations Human Rights Council", "United Nations", "UN_ORGAN", "Promotion and protection of human rights.", ("human rights",)),
    ]
    agencies = [("UNDP", "UN Development Programme"), ("UNICEF", "UNICEF"), ("UNHCR", "UN Refugee Agency"), ("UN_WOMEN", "UN Women"), ("UNFPA", "UNFPA"), ("WFP", "World Food Programme"), ("UNCTAD", "UN Trade and Development"), ("UNEP", "UN Environment Programme"), ("WHO", "World Health Organization"), ("UNESCO", "UNESCO"), ("ILO", "International Labour Organization"), ("FAO", "Food and Agriculture Organization"), ("ICAO", "International Civil Aviation Organization"), ("IMO", "International Maritime Organization"), ("ITU", "International Telecommunication Union"), ("WIPO", "World Intellectual Property Organization"), ("IAEA", "International Atomic Energy Agency"), ("WTO", "World Trade Organization"), ("UNFCCC", "UN Framework Convention on Climate Change"), ("ICJ", "International Court of Justice"), ("UNODC", "UN Office on Drugs and Crime")]
    records = [_record(*s) for s in specs]
    records.extend(_record(i, (name,), name, "International system", "AGENCY_OR_BODY", f"Institutional mandate of {name}.") for i, name in agencies)
    return records
