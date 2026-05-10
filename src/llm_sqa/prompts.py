from __future__ import annotations

import json
from collections.abc import Sequence

from llm_sqa.models import FormMetadata, TestCase


def generation_prompt(metadata: FormMetadata) -> str:
    field_summary = [field.model_dump(mode="json") for field in metadata.fields]
    return f"""
You are a senior Software Quality Assurance engineer.
Generate practical web-form test cases for this target form.

Rules:
- Return JSON only.
- Do not include markdown.
- Use this exact JSON shape: {{"cases": [{{"target_key": string, "test_id": string, "scenario": string, "case_type": "positive" or "negative", "input_data": object, "tags": array}}]}}
- Generate 8 to 12 cases.
- Include positive and negative cases.
- Do not generate vague, impossible, or security-harmful cases.
- input_data keys must match the field name values when available.
- Use synthetic data only.
- Use ${{UNIQUE}} where a username or email must be unique.

Target key: {metadata.target_key}
Target name: {metadata.target_name}
URL: {metadata.url}
Fields:
{json.dumps(field_summary, indent=2)}
""".strip()


def review_prompt(cases: Sequence[TestCase]) -> str:
    payload = [case.model_dump(mode="json") for case in cases]
    return f"""
You are reviewing LLM-generated SQA test cases.
Classify each case as accepted or rejected.

Reject cases that are duplicate, weak, vague, unrealistic, not relevant to actual web-form behavior, or impossible to verify with Selenium.

Return JSON only with this exact shape:
{{"cases": [{{"target_key": string, "test_id": string, "scenario": string, "case_type": "positive" or "negative", "input_data": object, "tags": array, "review_status": "accepted" or "rejected", "review_reason": string}}]}}

Cases:
{json.dumps(payload, indent=2)}
""".strip()


def enrichment_prompt(cases: Sequence[TestCase]) -> str:
    payload = [case.model_dump(mode="json") for case in cases]
    return f"""
You are a senior SQA engineer assigning risk and expected results for web-form tests.

Return JSON only with this exact shape:
{{"cases": [{{"target_key": string, "test_id": string, "scenario": string, "case_type": "positive" or "negative", "input_data": object, "tags": array, "severity": "high" or "medium" or "low", "expected_result_type": "success" or "validation_error" or "duplicate_error" or "blocked_by_browser_validation" or "unknown", "expected_behavior": string, "expected_message_category": string, "review_reason": string}}]}}

Severity guidance:
- high: required authentication/identity fields, password mismatch, missing password, missing username/email, duplicate account identifier.
- medium: invalid email, invalid phone/zip/numeric format, boundary length.
- low: optional text variation, harmless formatting variation.

Cases:
{json.dumps(payload, indent=2)}
""".strip()
