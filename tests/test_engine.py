from datetime import date

import pytest

from intelforge.committees import CommitteeRegistry, MandateResolver
from intelforge.core.errors import ValidationError
from intelforge.core.models import Incident, LegalFramework, MandateFit, POICandidate, ResearchSettings, Source
from intelforge.poi import EvidenceBoundPOIGenerator, NoveltyEngine, POIValidator
from intelforge.poi.scoring import score
from intelforge.ratelimit import RateLimitManager


def candidate(incident_id="INC-1"):
    source = Source("S-1", "https://example.test/doc", "Official record", "PRIMARY_DOCUMENT", True, date(2025, 1, 2))
    incident = Incident(incident_id, "Example State", "Port seizure", "seized controlled equipment", date(2025, 1, 1), "Example Port", ["Customs authority"], [source], .95)
    legal = LegalFramework("L-1", "Example Convention", "Article 4", "prevent prohibited transfers", "https://example.test/law", True, "State is party", .95)
    return POICandidate("Example State", incident, legal, "Failure to prevent prohibited transfers", "treaty obligation vs conduct", mandate_fit=MandateFit.WITHIN_MANDATE)


def test_registry_alias_and_unknown_committee():
    resolver = MandateResolver(CommitteeRegistry())
    assert resolver.resolve("DISEC")["committeeId"] == "UNGA_FIRST"
    with pytest.raises(ValidationError): resolver.resolve("not-a-committee")


def test_generator_is_specific_and_not_yes_no():
    item = candidate(); item.question = EvidenceBoundPOIGenerator().generate(item, ResearchSettings("DISEC", "security technology", "Singapore"))
    assert not POIValidator().validate(item, date(2026, 1, 1))
    assert "Article 4" in item.question and item.question.endswith("?")


def test_freeze_and_novelty_reject_unsafe_reuse():
    first, second = candidate(), candidate()
    novelty = NoveltyEngine()
    assert novelty.is_novel(first)
    assert not novelty.is_novel(second)
    first.question = EvidenceBoundPOIGenerator().generate(first, ResearchSettings("DISEC", "security", "Singapore"))
    assert any("post-freeze" in error for error in POIValidator().validate(first, date(2024, 1, 1)))


def test_scores_are_evidence_derived():
    item = candidate(); item.scores = score(item, novel=True)
    assert item.scores.evidence_strength > 0 and item.scores.legal_strength > 0
    assert item.scores.genericity < 70


def test_rate_limit_manager_has_bounded_retries():
    calls = 0
    def fail():
        nonlocal calls; calls += 1; raise RuntimeError("429 busy")
    with pytest.raises(Exception): RateLimitManager(max_retries=1, base_delay=0).execute("test", fail)
    assert calls == 2
