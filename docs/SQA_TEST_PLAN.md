# SQA Test Plan

## Scope

This test plan covers the LLM-assisted SQA web-form testing framework.

## Test Items

- Metadata extractor
- LLM client
- Deterministic fallback generator
- LLM review and deterministic review
- Risk severity assignment
- Expected result enrichment
- Selenium execution layer
- pytest reporting

## Features to Test

1. Form fields are extracted correctly.
2. Generated test cases follow the required schema.
3. Duplicate or weak cases are rejected.
4. Accepted cases receive severity labels.
5. Expected result fields are precise enough for execution.
6. Final cases execute in browser sessions.
7. High-severity cases are executed first.
8. Reports are generated after execution.

## Features Not Tested

- Internal database state of public demo websites
- Email delivery
- Payment flows
- Cross-browser execution beyond Chrome stable

## Entry Criteria

- Python virtual environment created
- Dependencies installed
- Chrome installed
- Target websites reachable
- `python -m llm_sqa.cli doctor` passes critical checks

## Exit Criteria

- Unit tests pass
- Browser tests produce an HTML report
- Final test case JSON exists
- Failed tests are documented with reason

## Test Levels

### Unit Tests

- Schema validation
- Token replacement
- Rule-based severity mapping
- HTML parsing

### Integration Tests

- Metadata to generated cases
- Generated cases to reviewed cases
- Reviewed cases to final cases

### System Tests

- Execute final cases against real browser targets

### Regression Tests

Run after any code/prompt/selector change:

```powershell
pytest tests/unit -q
pytest tests/e2e -q --html=reports/regression_report.html --self-contained-html
```

## Bug Report Format

```text
Bug ID:
Title:
Environment:
Build/Commit:
Severity: High/Medium/Low
Priority: P1/P2/P3
Preconditions:
Steps to Reproduce:
Expected Result:
Actual Result:
Evidence/Screenshot:
Root Cause:
Suggested Fix:
Status:
```

## QA Checklist

- [ ] `.env` exists and has no real secrets
- [ ] Ollama is running or fallback mode is used
- [ ] Chrome opens normally
- [ ] `doctor` command passes imports
- [ ] Metadata files generated
- [ ] Generated cases valid JSON
- [ ] Rejected cases have reasons
- [ ] Final cases contain severity and expected result
- [ ] pytest report generated
- [ ] Logs checked after failures
