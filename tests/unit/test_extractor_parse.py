import pytest

from llm_sqa.extractor import parse_form_metadata


@pytest.mark.unit
def test_parse_form_metadata_from_sample_html() -> None:
    html = """
    <html><body>
      <form>
        <label for="email">Email</label>
        <input id="email" name="email" type="email" required placeholder="Enter email" />
        <label for="password">Password</label>
        <input id="password" name="password" type="password" />
        <input type="submit" value="Submit" />
      </form>
    </body></html>
    """
    metadata = parse_form_metadata(html, "automation_exercise_signup")
    assert metadata.target_key == "automation_exercise_signup"
    assert len(metadata.fields) == 2
    assert metadata.fields[0].name == "email"
    assert metadata.fields[0].likely_required is True
