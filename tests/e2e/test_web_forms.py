from pathlib import Path

import pytest

from llm_sqa.browser import create_chrome_driver
from llm_sqa.config import get_settings
from llm_sqa.executor import execute_case
from llm_sqa.io_utils import read_json
from llm_sqa.models import FinalTestCase, Severity
from llm_sqa.pipeline import final_cases_path, seed_deterministic_final_cases


def _load_final_cases() -> list[FinalTestCase]:
    path = final_cases_path()
    if not Path(path).exists():
        seed_deterministic_final_cases()
    raw_cases = read_json(path)
    cases = [FinalTestCase.model_validate(item) for item in raw_cases]
    severity_order = {Severity.high: 0, Severity.medium: 1, Severity.low: 2}
    return sorted(cases, key=lambda item: (severity_order[item.severity], item.test_id))


@pytest.fixture(scope="session")
def driver():
    settings = get_settings()
    web_driver = create_chrome_driver(headless=settings.headless)
    yield web_driver
    web_driver.quit()


@pytest.mark.e2e
@pytest.mark.network
@pytest.mark.parametrize("case", _load_final_cases(), ids=lambda case: case.test_id)
def test_web_form_case_execution(driver, case: FinalTestCase) -> None:
    result = execute_case(driver, case, timeout=get_settings().default_timeout_seconds)
    assert result.passed, result.model_dump_json(indent=2)
