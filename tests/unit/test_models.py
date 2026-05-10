import pytest
from pydantic import ValidationError

from llm_sqa.models import CaseType, TestCase


@pytest.mark.unit
def test_test_case_requires_input_data() -> None:
    with pytest.raises(ValidationError):
        TestCase(
            target_key="demo",
            test_id="T001",
            scenario="Missing input data should fail validation",
            case_type=CaseType.negative,
            input_data={},
        )


@pytest.mark.unit
def test_valid_test_case_model() -> None:
    case = TestCase(
        target_key="demo",
        test_id="T002",
        scenario="Valid case should pass validation",
        case_type=CaseType.positive,
        input_data={"email": "qa@example.com"},
    )
    assert case.test_id == "T002"
    assert case.input_data["email"] == "qa@example.com"
