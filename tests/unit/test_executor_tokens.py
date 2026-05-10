import re

import pytest

from llm_sqa.executor import resolve_tokens


@pytest.mark.unit
def test_unique_token_replacement() -> None:
    result = resolve_tokens({"email": "qa_${UNIQUE}@example.com", "username": "u_${TIMESTAMP}"})
    assert "${" not in result["email"]
    assert "${" not in result["username"]
    assert re.match(r"qa_\d+@example\.com", result["email"])
