$ErrorActionPreference = "Stop"
. .\.venv\Scripts\Activate.ps1
ruff check .
ruff format .
mypy src
pytest tests/unit --cov=src/llm_sqa --cov-report=term-missing --cov-report=html:reports/coverage
