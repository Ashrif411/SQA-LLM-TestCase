from __future__ import annotations

from collections import OrderedDict

from llm_sqa.models import (
    CaseType,
    ExpectedResultType,
    FinalTestCase,
    FormField,
    FormMetadata,
    ReviewedCase,
    ReviewStatus,
    Severity,
    TestCase,
)
from llm_sqa.targets import TARGETS, get_target


def generate_deterministic_cases(metadata: FormMetadata) -> list[TestCase]:
    target = get_target(metadata.target_key)
    base = dict(target.default_valid_data)

    if metadata.target_key == "parabank_register":
        return [
            TestCase(
                target_key=metadata.target_key,
                test_id="PB_REG_001",
                scenario="Register with all valid required data",
                case_type=CaseType.positive,
                input_data=base,
                tags=["smoke", "registration", "positive"],
            ),
            TestCase(
                target_key=metadata.target_key,
                test_id="PB_REG_002",
                scenario="Reject registration when first name is empty",
                case_type=CaseType.negative,
                input_data={**base, "customer.firstName": ""},
                tags=["required-field", "negative"],
            ),
            TestCase(
                target_key=metadata.target_key,
                test_id="PB_REG_003",
                scenario="Reject registration when username is empty",
                case_type=CaseType.negative,
                input_data={**base, "customer.username": ""},
                tags=["required-field", "identity", "negative"],
            ),
            TestCase(
                target_key=metadata.target_key,
                test_id="PB_REG_004",
                scenario="Reject registration when password is empty",
                case_type=CaseType.negative,
                input_data={**base, "customer.password": "", "repeatedPassword": ""},
                tags=["required-field", "password", "negative"],
            ),
            TestCase(
                target_key=metadata.target_key,
                test_id="PB_REG_005",
                scenario="Reject registration when password and confirm password do not match",
                case_type=CaseType.negative,
                input_data={
                    **base,
                    "customer.password": "SecurePass123",
                    "repeatedPassword": "DifferentPass123",
                },
                tags=["password", "mismatch", "negative"],
            ),
            TestCase(
                target_key=metadata.target_key,
                test_id="PB_REG_006",
                scenario="Submit alphabetic phone number and verify validation behavior",
                case_type=CaseType.negative,
                input_data={**base, "customer.phoneNumber": "invalid-phone"},
                tags=["format", "phone", "negative"],
            ),
            TestCase(
                target_key=metadata.target_key,
                test_id="PB_REG_007",
                scenario="Submit overly long username and verify validation behavior",
                case_type=CaseType.negative,
                input_data={**base, "customer.username": "u" * 80},
                tags=["boundary", "username", "negative"],
            ),
        ]

    if metadata.target_key == "automation_exercise_signup":
        return [
            TestCase(
                target_key=metadata.target_key,
                test_id="AE_SIGNUP_001",
                scenario="Start signup with valid name and unique email",
                case_type=CaseType.positive,
                input_data=base,
                tags=["smoke", "signup", "positive"],
            ),
            TestCase(
                target_key=metadata.target_key,
                test_id="AE_SIGNUP_002",
                scenario="Reject signup when name is empty",
                case_type=CaseType.negative,
                input_data={**base, "name": ""},
                tags=["required-field", "negative"],
            ),
            TestCase(
                target_key=metadata.target_key,
                test_id="AE_SIGNUP_003",
                scenario="Reject signup when email is empty",
                case_type=CaseType.negative,
                input_data={**base, "email": ""},
                tags=["required-field", "email", "negative"],
            ),
            TestCase(
                target_key=metadata.target_key,
                test_id="AE_SIGNUP_004",
                scenario="Reject signup when email format is invalid",
                case_type=CaseType.negative,
                input_data={**base, "email": "not-an-email"},
                tags=["format", "email", "negative"],
            ),
            TestCase(
                target_key=metadata.target_key,
                test_id="AE_SIGNUP_005",
                scenario="Reject signup when email already exists",
                case_type=CaseType.negative,
                input_data={**base, "email": "test@example.com"},
                tags=["duplicate", "email", "negative"],
            ),
        ]

    raise ValueError(f"No deterministic cases configured for {metadata.target_key}")


def review_cases_deterministically(
    cases: list[TestCase],
) -> tuple[list[ReviewedCase], list[ReviewedCase]]:
    seen_signatures: set[tuple[str, str, tuple[tuple[str, str], ...]]] = set()
    accepted: list[ReviewedCase] = []
    rejected: list[ReviewedCase] = []

    for case in cases:
        normalized_inputs = tuple(
            sorted((k, str(v).strip().lower()) for k, v in case.input_data.items())
        )
        signature = (case.target_key, case.scenario.strip().lower(), normalized_inputs)
        is_vague = len(case.scenario.split()) < 4
        is_duplicate = signature in seen_signatures
        seen_signatures.add(signature)

        if is_duplicate:
            rejected.append(
                ReviewedCase(
                    **case.model_dump(mode="json"),
                    review_status=ReviewStatus.rejected,
                    review_reason="duplicate",
                )
            )
        elif is_vague:
            rejected.append(
                ReviewedCase(
                    **case.model_dump(mode="json"),
                    review_status=ReviewStatus.rejected,
                    review_reason="weak or vague scenario",
                )
            )
        else:
            accepted.append(
                ReviewedCase(
                    **case.model_dump(mode="json"),
                    review_status=ReviewStatus.accepted,
                    review_reason="accepted by deterministic review rules",
                )
            )
    return accepted, rejected


def severity_for_case(case: TestCase) -> Severity:
    text = " ".join([case.scenario, *case.tags, *case.input_data.keys()]).lower()
    if any(word in text for word in ["password", "username", "required", "empty", "duplicate"]):
        return Severity.high
    if any(word in text for word in ["email", "phone", "zip", "format", "boundary", "long"]):
        return Severity.medium
    return Severity.low


def expected_type_for_case(case: TestCase) -> ExpectedResultType:
    if case.case_type == CaseType.positive:
        return ExpectedResultType.success
    text = " ".join([case.scenario, *case.tags]).lower()
    if "duplicate" in text or "already exists" in text:
        return ExpectedResultType.duplicate_error
    if "invalid email" in text or "email format" in text:
        return ExpectedResultType.blocked_by_browser_validation
    return ExpectedResultType.validation_error


def enrich_cases_deterministically(cases: list[ReviewedCase]) -> list[FinalTestCase]:
    final_cases: list[FinalTestCase] = []
    for case in cases:
        if case.review_status != ReviewStatus.accepted:
            continue
        expected_type = expected_type_for_case(case)
        if expected_type == ExpectedResultType.success:
            expected_behavior = (
                "The form should accept the input and move to the success or next-step page."
            )
            message_category = "success_state"
        elif expected_type == ExpectedResultType.blocked_by_browser_validation:
            expected_behavior = (
                "The browser or page should block submission because the field format is invalid."
            )
            message_category = "client_side_validation"
        elif expected_type == ExpectedResultType.duplicate_error:
            expected_behavior = "The page should show a duplicate account identifier error."
            message_category = "duplicate_validation"
        else:
            expected_behavior = "The page should reject submission and show validation behavior or stay on the form."
            message_category = "server_or_client_validation"

        final_cases.append(
            FinalTestCase(
                **case.model_dump(
                    mode="json",
                    exclude={
                        "review_status",
                        "review_reason",
                        "severity",
                        "expected_result_type",
                        "expected_behavior",
                        "expected_message_category",
                    },
                ),
                severity=severity_for_case(case),
                expected_result_type=expected_type,
                expected_behavior=expected_behavior,
                expected_message_category=message_category,
                review_reason=case.review_reason,
            )
        )

    severity_order = {Severity.high: 0, Severity.medium: 1, Severity.low: 2}
    return sorted(final_cases, key=lambda item: (severity_order[item.severity], item.test_id))


def build_metadata_from_target_defaults() -> list[FormMetadata]:
    metadata_items: list[FormMetadata] = []
    for target in TARGETS.values():
        fields: list[FormField] = []
        for field_name in target.default_valid_data:
            fields.append(
                FormField(
                    label=field_name,
                    input_type="text",
                    name=field_name,
                    field_id="",
                    placeholder="",
                    likely_required=True,
                    css_selector=f"input[name='{field_name}']",
                )
            )
        metadata_items.append(
            FormMetadata(
                target_key=target.key,
                target_name=target.name,
                url=target.url,
                form_selector=target.form_selector,
                fields=fields,
            )
        )
    return metadata_items


def deduplicate_cases(cases: list[TestCase]) -> list[TestCase]:
    ordered: OrderedDict[str, TestCase] = OrderedDict()
    for case in cases:
        ordered[case.test_id] = case
    return list(ordered.values())
