$ErrorActionPreference = "Stop"
. .\.venv\Scripts\Activate.ps1

python --version
pip install -e .
python -m llm_sqa.cli all
pytest tests/unit -q
pytest tests/e2e -q --html=reports/e2e_report.html --self-contained-html
