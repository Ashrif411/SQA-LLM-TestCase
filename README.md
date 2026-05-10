# LLM-Assisted SQA Test Case Generation for Web Forms

A Python-based Software Quality Assurance automation framework that uses a local LLM to generate, review, prioritize, enrich, and execute web-form test cases.

The system extracts form metadata, generates positive and negative test cases, filters weak or duplicate cases, assigns risk severity, enriches expected results, and executes final test cases using Selenium and pytest.

## Target Forms

- ParaBank Register for Free Online Account Access
- Automation Exercise Signup / Login

## Tech Stack

| Purpose | Tool |
|---|---|
| Language | Python 3.13 |
| Browser Automation | Selenium WebDriver |
| Test Runner | pytest |
| HTML Parsing | BeautifulSoup4 |
| Data Validation | Pydantic |
| Local LLM Runtime | Ollama |
| LLM Model | llama3.2:3b |
| Reporting | pytest-html, pytest-cov |
| Code Quality | Ruff, mypy |

## Project Structure

```text
llm-sqa-form-tester/
├── src/llm_sqa/          # Main framework source code
├── tests/unit/           # Unit tests
├── tests/e2e/            # Selenium browser tests
├── data/                 # Generated metadata and test case JSON files
├── reports/              # HTML test and coverage reports
├── docs/                 # Test plan, workflow, and troubleshooting docs
├── scripts/              # Windows setup and run scripts
├── postman/              # Ollama API testing collection
├── .github/workflows/    # CI workflow
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Project configuration
├── pytest.ini            # pytest configuration
└── README.md
```

## Setup on Windows

### 1. Open the project folder

```powershell
cd C:\sqa-projects\llm-sqa-form-tester
```

### 2. Create and activate virtual environment

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
```

Expected:

```text
Python 3.13.x
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip==25.1.1 setuptools==80.9.0 wheel==0.45.1
pip install -r requirements.txt
pip install -e .
```

### 4. Create environment file

```powershell
copy .env.example .env
```

Default `.env`:

```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
HEADLESS=true
DEFAULT_TIMEOUT_SECONDS=15
DATA_DIR=data
REPORT_DIR=reports
```

Set `HEADLESS=false` to watch the browser during execution.

## Ollama Setup

Install Ollama, then pull the model:

```powershell
ollama pull llama3.2:3b
ollama list
```

Check the local API:

```powershell
curl http://localhost:11434/api/tags
```

If Ollama is unavailable, use fallback mode:

```powershell
python -m llm_sqa.cli all --no-llm
```

## Main Commands

### Health check

```powershell
python -m llm_sqa.cli doctor
```

### Run full LLM-assisted pipeline

```powershell
python -m llm_sqa.cli all
```

### Run without Ollama

```powershell
python -m llm_sqa.cli all --no-llm
```

### Run pipeline step by step

```powershell
python -m llm_sqa.cli extract
python -m llm_sqa.cli generate
python -m llm_sqa.cli review
python -m llm_sqa.cli enrich
```

## Run Tests

### Unit tests

```powershell
pytest tests/unit -q
```

### Browser tests with HTML report

```powershell
pytest tests/e2e -q --html=reports/e2e_report.html --self-contained-html
```

### Coverage report

```powershell
pytest tests/unit --cov=src/llm_sqa --cov-report=term-missing --cov-report=html:reports/coverage
```

### Code quality checks

```powershell
ruff check .
ruff format .
mypy src
```

## Generated Outputs

```text
data/metadata/*.json
data/test_cases/generated_cases.json
data/test_cases/reviewed_cases.json
data/test_cases/rejected_cases.json
data/test_cases/final_test_cases.json
reports/e2e_report.html
reports/coverage/index.html
logs/app.log
```

These outputs provide traceability from form extraction to final test execution.

## Testing Strategy

- **Unit testing:** validates internal logic, schema validation, parsing, token replacement, and fallback generation.
- **Integration testing:** verifies that extraction, generation, review, and enrichment work together.
- **End-to-end testing:** executes final approved test cases in a real browser using Selenium.
- **Regression testing:** reruns unit and browser tests before submission or showcase.
- **Risk-based testing:** prioritizes high-severity cases before medium and low-severity cases.

## Demo Workflow

Recommended showcase sequence:

```powershell
python -m llm_sqa.cli doctor
python -m llm_sqa.cli all --no-llm
pytest tests/e2e -q --html=reports/e2e_report.html --self-contained-html
```

Then open:

```text
reports/e2e_report.html
data/test_cases/final_test_cases.json
```

Explain:

1. Metadata is extracted from real web forms.
2. Test cases are generated and reviewed.
3. Weak or duplicate cases are rejected.
4. Final cases include severity and expected results.
5. Selenium executes the approved cases.
6. pytest generates the HTML report.

## Known Limitations

- Public demo websites may change their HTML structure.
- Public websites may be slow or temporarily unavailable.
- Local LLM output quality depends on the selected model.
- Browser validation messages may differ by browser or system language.
- The framework tests web-form behavior, not backend database correctness.

## Future Improvements

- Add more target websites.
- Add screenshot capture for failed Selenium tests.
- Add a dashboard for test results.
- Store execution history in a database.
- Add CI-based scheduled browser tests.
- Improve prompt templates for higher-quality LLM output.
