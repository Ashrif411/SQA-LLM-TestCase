from __future__ import annotations

import logging
from collections.abc import Iterable

from bs4 import BeautifulSoup, Tag

from llm_sqa.browser import create_chrome_driver
from llm_sqa.config import get_settings
from llm_sqa.models import FormField, FormMetadata
from llm_sqa.targets import get_target

logger = logging.getLogger(__name__)

IGNORED_TYPES = {"hidden", "submit", "button", "reset", "image"}


def _clean_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = " ".join(str(item) for item in value)
    return " ".join(str(value).split())


def _label_for_element(soup: BeautifulSoup, element: Tag) -> str:
    element_id = element.get("id")
    if element_id:
        label = soup.find("label", attrs={"for": element_id})
        if label:
            return _clean_text(label.get_text(" "))

    parent_label = element.find_parent("label")
    if parent_label:
        return _clean_text(parent_label.get_text(" "))

    previous = element.find_previous(string=True)
    if previous:
        text = _clean_text(str(previous))
        if 1 <= len(text) <= 80:
            return text.rstrip(":")

    return _clean_text(
        element.get("aria-label") or element.get("title") or element.get("name") or ""
    )


def _css_selector_for(element: Tag) -> str:
    if element.get("id"):
        return f"#{element.get('id')}"
    if element.get("name"):
        tag_name = element.name or "input"
        return f"{tag_name}[name='{element.get('name')}']"
    return element.name or "input"


def _is_likely_required(element: Tag, label: str) -> bool:
    return bool(
        element.has_attr("required")
        or element.get("aria-required") == "true"
        or "*" in label
        or "required"
        in _clean_text(
            element.get("class") if isinstance(element.get("class"), str) else ""
        ).lower()
    )


def _iter_form_controls(form: Tag) -> Iterable[Tag]:
    yield from form.find_all(["input", "select", "textarea"])


def parse_form_metadata(html: str, target_key: str) -> FormMetadata:
    target = get_target(target_key)
    soup = BeautifulSoup(html, "html.parser")
    form = soup.select_one(target.form_selector) or soup.find("form")
    if form is None:
        raise RuntimeError(f"Could not find form using selector: {target.form_selector}")

    fields: list[FormField] = []
    seen_keys: set[str] = set()

    for element in _iter_form_controls(form):
        input_type = _clean_text(element.get("type") or element.name or "text").lower()
        if input_type in IGNORED_TYPES:
            continue

        name = _clean_text(element.get("name") or "")
        field_id = _clean_text(element.get("id") or "")
        label = _label_for_element(soup, element)
        key = name or field_id or label
        if not key or key in seen_keys:
            continue
        seen_keys.add(key)

        fields.append(
            FormField(
                label=label,
                input_type=input_type,
                name=name,
                field_id=field_id,
                placeholder=_clean_text(element.get("placeholder") or ""),
                likely_required=_is_likely_required(element, label),
                css_selector=_css_selector_for(element),
            )
        )

    return FormMetadata(
        target_key=target.key,
        target_name=target.name,
        url=target.url,
        form_selector=target.form_selector,
        fields=fields,
    )


def extract_form_metadata(target_key: str, headless: bool | None = None) -> FormMetadata:
    settings = get_settings()
    target = get_target(target_key)
    use_headless = settings.headless if headless is None else headless
    logger.info("Opening target page for metadata extraction: %s", target.url)
    driver = create_chrome_driver(headless=use_headless)
    try:
        driver.get(target.url)
        html = driver.page_source
        metadata = parse_form_metadata(html, target_key)
        logger.info("Extracted %s fields for %s", len(metadata.fields), target_key)
        return metadata
    finally:
        driver.quit()
