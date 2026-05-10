from __future__ import annotations

import importlib.util
import platform
import sys
from typing import Any

import requests

from llm_sqa.browser import create_chrome_driver
from llm_sqa.config import get_settings
from llm_sqa.llm_client import OllamaClient
from llm_sqa.targets import TARGETS

REQUIRED_IMPORTS = [
    "selenium",
    "pytest",
    "bs4",
    "pydantic",
    "dotenv",
    "requests",
]


def run_doctor(check_browser: bool = True) -> dict[str, Any]:
    settings = get_settings()
    result: dict[str, Any] = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "python_ok": sys.version_info[:2] == (3, 13),
        "imports": {},
        "imports_ok": True,
        "ollama_host": settings.ollama_host,
        "ollama_model": settings.ollama_model,
        "ollama_available": False,
        "browser_session_ok": None,
        "targets_reachable": {},
    }

    for module in REQUIRED_IMPORTS:
        available = importlib.util.find_spec(module) is not None
        result["imports"][module] = available
        if not available:
            result["imports_ok"] = False

    client = OllamaClient()
    result["ollama_available"] = client.is_available()

    for key, target in TARGETS.items():
        try:
            response = requests.get(target.url, timeout=10)
            result["targets_reachable"][key] = response.status_code < 500
        except requests.RequestException:
            result["targets_reachable"][key] = False

    if check_browser:
        try:
            driver = create_chrome_driver(headless=True)
            driver.get("data:text/html,<h1>driver-ok</h1>")
            result["browser_session_ok"] = "driver-ok" in driver.page_source
            driver.quit()
        except Exception as exc:  # noqa: BLE001
            result["browser_session_ok"] = False
            result["browser_error"] = str(exc)

    return result
