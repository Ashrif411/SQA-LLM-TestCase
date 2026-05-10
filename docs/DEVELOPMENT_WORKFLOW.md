# Development Workflow

## Phase 1: Environment Setup

1. Install Chrome.
2. Install Python 3.13.13.
3. Install Git 2.54.0.
4. Install VS Code.
5. Install Ollama.
6. Create virtual environment using `py -3.13 -m venv .venv`.
7. Activate the environment using `.\.venv\Scripts\Activate.ps1`.
8. Install dependencies using `pip install -r requirements.txt`.
9. Install the local package using `pip install -e .`.
10. Run doctor check.

Validation:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
pip install -r requirements.txt
pip install -e .
copy .env.example .env
python -m llm_sqa.cli doctor
```

## Phase 2: Project Initialization

```powershell
git init
git add .
git commit -m "Initial SQA automation framework"
```

## Phase 3: Metadata Extraction

```powershell
python -m llm_sqa.cli extract
```

Expected output:

```json
{"metadata_files_created": 2}
```

## Phase 4: LLM Generation

```powershell
python -m llm_sqa.cli generate
```

Fallback-only mode:

```powershell
python -m llm_sqa.cli generate --no-llm
```

## Phase 5: Review and Filtering

```powershell
python -m llm_sqa.cli review
```

Check:

```text
data/test_cases/reviewed_cases.json
data/test_cases/rejected_cases.json
```

## Phase 6: Risk and Expected Result Enrichment

```powershell
python -m llm_sqa.cli enrich
```

Check:

```text
data/test_cases/final_test_cases.json
```

## Phase 7: Test Execution

```powershell
pytest tests/e2e -q --html=reports/e2e_report.html --self-contained-html
```

## Phase 8: Quality Gates

```powershell
ruff check .
ruff format .
mypy src
pytest tests/unit --cov=src/llm_sqa --cov-report=term-missing
```

## Phase 9: Submission Packaging

Include:

- Source code
- README
- SQA test plan
- Troubleshooting guide
- final_test_cases.json
- pytest HTML report
- coverage report
- screenshots or short demo recording
