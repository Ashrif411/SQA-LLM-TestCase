# Troubleshooting Guide

## 1. `python` opens Microsoft Store

Cause: Windows App Execution Alias overrides Python.

Diagnosis:

```powershell
where python
```

Fix:

```text
Windows Settings > Apps > Advanced app settings > App execution aliases > disable python.exe and python3.exe
```

Then reinstall Python 3.13.13 and tick `Add python.exe to PATH`.

---

## 2. Virtual environment activation is blocked

Cause: PowerShell execution policy.

Fix:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```

---

## 3. `ModuleNotFoundError: No module named 'llm_sqa'`

Cause: The virtual environment is active, but the local `src/llm_sqa` package was not installed in editable mode.

Diagnosis:

```powershell
where python
python --version
pip --version
dir src\llm_sqa\cli.py
```

Fix:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
python -m llm_sqa.cli doctor
```

---

## 4. ChromeDriver mismatch

Cause: Old manual ChromeDriver in PATH.

Diagnosis:

```powershell
where chromedriver
chrome --version
```

Fix:

Remove old ChromeDriver from PATH. Selenium Manager will manage the driver automatically.

---

## 5. Selenium browser does not open

Cause: Chrome missing, corrupted browser profile, corporate antivirus, or driver cache issue.

Fix:

```powershell
python -m llm_sqa.cli doctor
```

Then:

```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.cache\selenium"
```

Restart PowerShell and retry.

---

## 6. Ollama not reachable

Cause: Ollama service is not running.

Diagnosis:

```powershell
curl http://localhost:11434/api/tags
```

Fix:

```powershell
ollama serve
```

In another terminal:

```powershell
ollama pull llama3.2:3b
```

If you do not want to use Ollama:

```powershell
python -m llm_sqa.cli all --no-llm
```

---

## 7. LLM returns invalid JSON

Cause: Local LLM ignored the strict JSON instruction.

Fix:

The framework automatically falls back to deterministic cases. For better output:

```powershell
ollama pull qwen2.5:7b
```

Then change `.env`:

```env
OLLAMA_MODEL=qwen2.5:7b
```

---

## 8. Public website is down or slow

Cause: Target public demo website unavailable.

Diagnosis:

Open the URL in Chrome manually.

Fix:

Retry later or run unit tests only:

```powershell
pytest tests/unit -q
```

---

## 9. E2E test fails but unit tests pass

Cause: Website selector changed, network delay, or validation message changed.

Diagnosis:

Set `.env`:

```env
HEADLESS=false
```

Run:

```powershell
pytest tests/e2e -q -s
```

Fix:

Update selector in `src/llm_sqa/targets.py`.

---

## 10. pytest HTML report not generated

Cause: Missing `pytest-html` dependency or wrong command.

Fix:

```powershell
pip install pytest-html==4.2.0
pytest tests/e2e --html=reports/e2e_report.html --self-contained-html
```

---

## 11. Permission error writing files

Cause: Project located in protected folder such as `C:\Program Files`.

Fix:

Move project to:

```text
C:\sqa-projects\llm-sqa-form-tester
```

---

## 12. Automation Exercise blocks or changes behavior

Cause: Public demo sites may show ads, change HTML, or rate-limit traffic.

Fix:

Run fewer tests, wait, or document the issue as an external dependency limitation. The framework is still valid because unit and integration artifacts remain reproducible.


---

## 9. `requires a different Python`

Cause: The virtual environment was created with Python 3.12, 3.14, or another unsupported interpreter. This project targets Python 3.13 only.

Diagnosis:

```powershell
python --version
py -0p
```

Fix:

```powershell
deactivate
Remove-Item -Recurse -Force .venv
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
pip install -r requirements.txt
pip install -e .
python -m llm_sqa.cli doctor
```
