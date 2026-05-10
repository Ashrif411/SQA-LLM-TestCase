import pytest

from llm_sqa.fallback_rules import (
    build_metadata_from_target_defaults,
    enrich_cases_deterministically,
    generate_deterministic_cases,
    review_cases_deterministically,
)
from llm_sqa.models import Severity


@pytest.mark.unit
def test_fallback_generation_review_enrichment_pipeline() -> None:
    metadata_items = build_metadata_from_target_defaults()
    generated = []
    for metadata in metadata_items:
        generated.extend(generate_deterministic_cases(metadata))

    accepted, rejected = review_cases_deterministically(generated)
    final_cases = enrich_cases_deterministically(accepted)

    assert len(generated) >= 10
    assert len(accepted) >= 10
    assert len(rejected) == 0
    assert len(final_cases) == len(accepted)
    assert final_cases[0].severity in {Severity.high, Severity.medium, Severity.low}


@pytest.mark.unit
def test_high_risk_cases_are_sorted_first() -> None:
    metadata = build_metadata_from_target_defaults()[0]
    generated = generate_deterministic_cases(metadata)
    accepted, _ = review_cases_deterministically(generated)
    final_cases = enrich_cases_deterministically(accepted)

    severity_rank = {Severity.high: 0, Severity.medium: 1, Severity.low: 2}
    ranks = [severity_rank[case.severity] for case in final_cases]
    assert ranks == sorted(ranks)
