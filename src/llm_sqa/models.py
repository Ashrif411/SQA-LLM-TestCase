from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class CaseType(StrEnum):
    positive = "positive"
    negative = "negative"


class Severity(StrEnum):
    high = "high"
    medium = "medium"
    low = "low"


class ReviewStatus(StrEnum):
    accepted = "accepted"
    rejected = "rejected"


class ExpectedResultType(StrEnum):
    success = "success"
    validation_error = "validation_error"
    duplicate_error = "duplicate_error"
    blocked_by_browser_validation = "blocked_by_browser_validation"
    unknown = "unknown"


class FormField(BaseModel):
    label: str = ""
    input_type: str = "text"
    name: str = ""
    field_id: str = ""
    placeholder: str = ""
    likely_required: bool = False
    css_selector: str = ""

    @property
    def key(self) -> str:
        return self.name or self.field_id or self.label


class FormMetadata(BaseModel):
    target_key: str
    target_name: str
    url: str
    form_selector: str
    fields: list[FormField]

    @field_validator("fields")
    @classmethod
    def must_have_fields(cls, value: list[FormField]) -> list[FormField]:
        if not value:
            raise ValueError("No fields were extracted from the form.")
        return value


class TestCase(BaseModel):
    target_key: str
    test_id: str
    scenario: str
    case_type: CaseType
    input_data: dict[str, str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)

    @field_validator("test_id", "scenario")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value cannot be empty.")
        return cleaned

    @model_validator(mode="after")
    def must_have_input_data(self) -> TestCase:
        if not self.input_data:
            raise ValueError("input_data cannot be empty.")
        return self


class ReviewedCase(TestCase):
    review_status: ReviewStatus
    review_reason: str = ""


class FinalTestCase(TestCase):
    severity: Severity
    expected_result_type: ExpectedResultType
    expected_behavior: str
    expected_message_category: str
    review_reason: str = "accepted"


class ExecutionResult(BaseModel):
    test_id: str
    target_key: str
    passed: bool
    severity: Severity
    expected_result_type: ExpectedResultType
    observed_url: str
    observed_text_excerpt: str
    browser_validation_messages: list[str] = Field(default_factory=list)
    error: str = ""


class PipelineSummary(BaseModel):
    generated_count: int = 0
    reviewed_accepted_count: int = 0
    rejected_count: int = 0
    final_count: int = 0
    files: dict[str, str] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


JsonDict = dict[str, Any]
