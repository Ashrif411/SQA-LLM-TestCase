from __future__ import annotations

import logging
from pathlib import Path

from pydantic import ValidationError

from llm_sqa.config import ensure_project_directories, get_settings
from llm_sqa.extractor import extract_form_metadata
from llm_sqa.fallback_rules import (
    build_metadata_from_target_defaults,
    deduplicate_cases,
    enrich_cases_deterministically,
    generate_deterministic_cases,
    review_cases_deterministically,
)
from llm_sqa.io_utils import model_list_to_json, read_json, write_json
from llm_sqa.llm_client import OllamaClient
from llm_sqa.models import FinalTestCase, FormMetadata, ReviewedCase, ReviewStatus, TestCase
from llm_sqa.prompts import enrichment_prompt, generation_prompt, review_prompt
from llm_sqa.targets import TARGETS

logger = logging.getLogger(__name__)


def metadata_path(target_key: str) -> Path:
    return get_settings().metadata_dir / f"{target_key}.json"


def generated_cases_path() -> Path:
    return get_settings().test_case_dir / "generated_cases.json"


def reviewed_cases_path() -> Path:
    return get_settings().test_case_dir / "reviewed_cases.json"


def rejected_cases_path() -> Path:
    return get_settings().test_case_dir / "rejected_cases.json"


def final_cases_path() -> Path:
    return get_settings().test_case_dir / "final_test_cases.json"


def summary_path() -> Path:
    return get_settings().report_dir / "pipeline_summary.json"


def extract_all_metadata(use_browser: bool = True) -> list[FormMetadata]:
    ensure_project_directories()
    metadata_items: list[FormMetadata] = []
    if use_browser:
        for target_key in TARGETS:
            try:
                metadata = extract_form_metadata(target_key)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Browser metadata extraction failed for %s: %s", target_key, exc)
                continue
            write_json(metadata_path(target_key), metadata.model_dump(mode="json"))
            metadata_items.append(metadata)

    if not metadata_items:
        logger.warning(
            "Using deterministic metadata fallback because browser extraction returned no metadata."
        )
        metadata_items = build_metadata_from_target_defaults()
        for metadata in metadata_items:
            write_json(metadata_path(metadata.target_key), metadata.model_dump(mode="json"))

    return metadata_items


def load_metadata() -> list[FormMetadata]:
    settings = get_settings()
    items: list[FormMetadata] = []
    for path in sorted(settings.metadata_dir.glob("*.json")):
        items.append(FormMetadata.model_validate(read_json(path)))
    if not items:
        items = extract_all_metadata(use_browser=False)
    return items


def _cases_from_llm_payload(payload: dict, source: str) -> list[TestCase]:
    raw_cases = payload.get("cases", [])
    if not isinstance(raw_cases, list):
        raise ValueError(f"{source} payload must contain a list under 'cases'.")
    return [TestCase.model_validate(item) for item in raw_cases]


def generate_cases(use_llm: bool = True) -> list[TestCase]:
    ensure_project_directories()
    metadata_items = load_metadata()
    client = OllamaClient()
    all_cases: list[TestCase] = []

    for metadata in metadata_items:
        cases: list[TestCase]
        if use_llm:
            try:
                payload = client.generate_json(generation_prompt(metadata))
                cases = _cases_from_llm_payload(payload, "generation")
            except Exception as exc:  # noqa: BLE001
                logger.warning("LLM generation failed for %s: %s", metadata.target_key, exc)
                cases = generate_deterministic_cases(metadata)
        else:
            cases = generate_deterministic_cases(metadata)
        all_cases.extend(cases)

    all_cases = deduplicate_cases(all_cases)
    write_json(generated_cases_path(), model_list_to_json(all_cases))
    return all_cases


def load_generated_cases() -> list[TestCase]:
    path = generated_cases_path()
    if not path.exists():
        return generate_cases(use_llm=False)
    return [TestCase.model_validate(item) for item in read_json(path)]


def _reviewed_from_llm_payload(payload: dict) -> tuple[list[ReviewedCase], list[ReviewedCase]]:
    raw_cases = payload.get("cases", [])
    if not isinstance(raw_cases, list):
        raise ValueError("review payload must contain a list under 'cases'.")
    reviewed = [ReviewedCase.model_validate(item) for item in raw_cases]
    accepted = [case for case in reviewed if case.review_status == ReviewStatus.accepted]
    rejected = [case for case in reviewed if case.review_status == ReviewStatus.rejected]
    return accepted, rejected


def review_cases(use_llm: bool = True) -> tuple[list[ReviewedCase], list[ReviewedCase]]:
    cases = load_generated_cases()
    client = OllamaClient()
    if use_llm:
        try:
            payload = client.generate_json(review_prompt(cases))
            accepted, rejected = _reviewed_from_llm_payload(payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM review failed: %s", exc)
            accepted, rejected = review_cases_deterministically(cases)
    else:
        accepted, rejected = review_cases_deterministically(cases)

    write_json(reviewed_cases_path(), model_list_to_json(accepted))
    write_json(rejected_cases_path(), model_list_to_json(rejected))
    return accepted, rejected


def load_reviewed_cases() -> list[ReviewedCase]:
    path = reviewed_cases_path()
    if not path.exists():
        accepted, _ = review_cases(use_llm=False)
        return accepted
    return [ReviewedCase.model_validate(item) for item in read_json(path)]


def _final_from_llm_payload(payload: dict) -> list[FinalTestCase]:
    raw_cases = payload.get("cases", [])
    if not isinstance(raw_cases, list):
        raise ValueError("enrichment payload must contain a list under 'cases'.")
    return [FinalTestCase.model_validate(item) for item in raw_cases]


def enrich_cases(use_llm: bool = True) -> list[FinalTestCase]:
    accepted = load_reviewed_cases()
    client = OllamaClient()
    if use_llm:
        try:
            payload = client.generate_json(enrichment_prompt(accepted))
            final_cases = _final_from_llm_payload(payload)
        except (ValidationError, ValueError, RuntimeError, Exception) as exc:  # noqa: BLE001
            logger.warning("LLM enrichment failed: %s", exc)
            final_cases = enrich_cases_deterministically(accepted)
    else:
        final_cases = enrich_cases_deterministically(accepted)

    write_json(final_cases_path(), model_list_to_json(final_cases))
    return final_cases


def seed_deterministic_final_cases() -> list[FinalTestCase]:
    metadata_items = build_metadata_from_target_defaults()
    all_cases: list[TestCase] = []
    for metadata in metadata_items:
        write_json(metadata_path(metadata.target_key), metadata.model_dump(mode="json"))
        all_cases.extend(generate_deterministic_cases(metadata))
    write_json(generated_cases_path(), model_list_to_json(all_cases))
    accepted, rejected = review_cases_deterministically(all_cases)
    write_json(reviewed_cases_path(), model_list_to_json(accepted))
    write_json(rejected_cases_path(), model_list_to_json(rejected))
    final_cases = enrich_cases_deterministically(accepted)
    write_json(final_cases_path(), model_list_to_json(final_cases))
    return final_cases


def run_full_pipeline(use_llm: bool = True) -> dict[str, object]:
    extract_all_metadata(use_browser=True)
    generated = generate_cases(use_llm=use_llm)
    accepted, rejected = review_cases(use_llm=use_llm)
    final = enrich_cases(use_llm=use_llm)
    summary = {
        "generated_count": len(generated),
        "reviewed_accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "final_count": len(final),
        "generated_cases": str(generated_cases_path()),
        "reviewed_cases": str(reviewed_cases_path()),
        "rejected_cases": str(rejected_cases_path()),
        "final_cases": str(final_cases_path()),
    }
    write_json(summary_path(), summary)
    return summary
