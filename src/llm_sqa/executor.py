from __future__ import annotations

import logging
import re
import time
from datetime import UTC, datetime

from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from llm_sqa.models import ExecutionResult, ExpectedResultType, FinalTestCase
from llm_sqa.targets import get_target

logger = logging.getLogger(__name__)


def unique_suffix() -> str:
    return datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")


def resolve_tokens(input_data: dict[str, str]) -> dict[str, str]:
    suffix = unique_suffix()
    resolved: dict[str, str] = {}
    for key, value in input_data.items():
        resolved[key] = str(value).replace("${UNIQUE}", suffix).replace("${TIMESTAMP}", suffix)
    return resolved


def _find_input(driver: Chrome, field_name: str) -> WebElement:
    selectors = [
        (By.NAME, field_name),
        (By.ID, field_name),
        (By.CSS_SELECTOR, f"input[name='{field_name}']"),
        (By.CSS_SELECTOR, f"textarea[name='{field_name}']"),
        (By.CSS_SELECTOR, f"select[name='{field_name}']"),
    ]
    last_error: Exception | None = None
    for by, selector in selectors:
        try:
            return driver.find_element(by, selector)
        except NoSuchElementException as exc:
            last_error = exc
    raise NoSuchElementException(f"Could not locate field: {field_name}") from last_error


def _safe_fill(element: WebElement, value: str) -> None:
    element.clear()
    if value:
        element.send_keys(value)


def _click_submit(driver: Chrome, submit_selector: str, timeout: int) -> None:
    wait = WebDriverWait(driver, timeout)
    button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, submit_selector)))
    button.click()


def collect_browser_validation_messages(driver: Chrome) -> list[str]:
    script = """
    const fields = Array.from(document.querySelectorAll('input, textarea, select'));
    return fields
      .filter(el => el.willValidate && !el.validity.valid)
      .map(el => `${el.name || el.id || el.type}: ${el.validationMessage}`)
      .filter(Boolean);
    """
    try:
        messages = driver.execute_script(script)
        return [str(message) for message in messages if str(message).strip()]
    except WebDriverException:
        return []


def _contains_any(text: str, indicators: list[str]) -> bool:
    text_lower = text.lower()
    return any(indicator.lower() in text_lower for indicator in indicators)


def _page_excerpt(text: str, max_len: int = 600) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned[:max_len]


def execute_case(driver: Chrome, case: FinalTestCase, timeout: int = 15) -> ExecutionResult:
    target = get_target(case.target_key)
    input_data = resolve_tokens(case.input_data)
    logger.info("Executing %s against %s", case.test_id, target.key)

    try:
        driver.get(target.url)
        wait = WebDriverWait(driver, timeout)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, target.form_selector)))

        for field_name, value in input_data.items():
            element = _find_input(driver, field_name)
            _safe_fill(element, value)

        before_url = driver.current_url
        _click_submit(driver, target.submit_selector, timeout)
        time.sleep(1.0)

        validation_messages = collect_browser_validation_messages(driver)
        page_text = driver.find_element(By.TAG_NAME, "body").text
        observed_url = driver.current_url
        success_seen = _contains_any(page_text, target.success_indicators)
        error_seen = _contains_any(page_text, target.error_indicators)
        stayed_on_same_url = observed_url == before_url

        if case.expected_result_type == ExpectedResultType.success:
            passed = success_seen and not error_seen
        elif case.expected_result_type == ExpectedResultType.blocked_by_browser_validation:
            passed = bool(validation_messages) or stayed_on_same_url or error_seen
        elif case.expected_result_type in {
            ExpectedResultType.validation_error,
            ExpectedResultType.duplicate_error,
        }:
            passed = error_seen or bool(validation_messages) or stayed_on_same_url
        else:
            passed = success_seen or error_seen or bool(validation_messages)

        return ExecutionResult(
            test_id=case.test_id,
            target_key=case.target_key,
            passed=passed,
            severity=case.severity,
            expected_result_type=case.expected_result_type,
            observed_url=observed_url,
            observed_text_excerpt=_page_excerpt(page_text),
            browser_validation_messages=validation_messages,
        )
    except (NoSuchElementException, TimeoutException, WebDriverException) as exc:
        return ExecutionResult(
            test_id=case.test_id,
            target_key=case.target_key,
            passed=False,
            severity=case.severity,
            expected_result_type=case.expected_result_type,
            observed_url=getattr(driver, "current_url", ""),
            observed_text_excerpt="",
            browser_validation_messages=[],
            error=str(exc),
        )
