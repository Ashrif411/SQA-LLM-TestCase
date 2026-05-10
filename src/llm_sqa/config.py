from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    root_dir: Path
    data_dir: Path
    metadata_dir: Path
    test_case_dir: Path
    report_dir: Path
    log_dir: Path
    ollama_host: str
    ollama_model: str
    headless: bool
    default_timeout_seconds: int


def get_settings() -> Settings:
    data_dir = ROOT_DIR / os.getenv("DATA_DIR", "data")
    report_dir = ROOT_DIR / os.getenv("REPORT_DIR", "reports")
    log_dir = ROOT_DIR / "logs"
    return Settings(
        root_dir=ROOT_DIR,
        data_dir=data_dir,
        metadata_dir=data_dir / "metadata",
        test_case_dir=data_dir / "test_cases",
        report_dir=report_dir,
        log_dir=log_dir,
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
        headless=_as_bool(os.getenv("HEADLESS"), True),
        default_timeout_seconds=int(os.getenv("DEFAULT_TIMEOUT_SECONDS", "15")),
    )


def ensure_project_directories() -> None:
    settings = get_settings()
    for path in [
        settings.data_dir,
        settings.metadata_dir,
        settings.test_case_dir,
        settings.report_dir,
        settings.log_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)
