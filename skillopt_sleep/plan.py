"""Deterministic validation and resume guidance for structured plan HTML."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
from typing import Any

STATUSES = {"pending", "in_progress", "blocked", "complete"}
EASTERN_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$")


class _PlanParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.plan: dict[str, str] = {}
        self.sections: list[dict[str, str]] = []
        self.signoff: dict[str, str] = {}
        self.history: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "main" and "data-plan-id" in values:
            self.plan = values
        if values.get("data-section-id") == "signoff":
            self.signoff = values
        elif "data-section-id" in values:
            self.sections.append(values)
        if "data-change-id" in values:
            self.history.append(values)


def validate_plan(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    parser = _PlanParser()
    parser.feed(source.read_text(encoding="utf-8"))
    errors: list[str] = []
    overall = parser.plan.get("data-status", "")
    if not parser.plan.get("data-plan-id"):
        errors.append("missing plan id")
    if parser.plan.get("data-timezone") != "America/New_York":
        errors.append("plan timezone must be America/New_York")
    if not EASTERN_TIMESTAMP.match(parser.plan.get("data-updated-at", "")):
        errors.append("missing or invalid plan updated timestamp")
    if overall not in STATUSES:
        errors.append(f"invalid overall status: {overall!r}")
    ids = {section.get("data-section-id", "") for section in parser.sections}
    for section in parser.sections:
        section_id = section.get("data-section-id", "?")
        status = section.get("data-status", "")
        if status not in STATUSES:
            errors.append(f"{section_id}: invalid status {status!r}")
        if not EASTERN_TIMESTAMP.match(section.get("data-updated-at", "")):
            errors.append(f"{section_id}: missing or invalid data-updated-at")
        if status in {"in_progress", "complete"} and not EASTERN_TIMESTAMP.match(section.get("data-started-at", "")):
            errors.append(f"{section_id}: missing data-started-at")
        if status == "complete" and not EASTERN_TIMESTAMP.match(section.get("data-completed-at", "")):
            errors.append(f"{section_id}: missing data-completed-at")
        if status == "blocked" and not EASTERN_TIMESTAMP.match(section.get("data-blocked-at", "")):
            errors.append(f"{section_id}: missing data-blocked-at")
        for field in ("data-test", "data-acceptance"):
            if not section.get(field, "").strip():
                errors.append(f"{section_id}: missing {field}")
        if status == "complete" and not section.get("data-evidence", "").strip():
            errors.append(f"{section_id}: missing data-evidence")
        if status in {"in_progress", "blocked"} and not section.get("data-next-action", "").strip():
            errors.append(f"{section_id}: missing data-next-action")
        for dependency in filter(None, section.get("data-depends-on", "").split()):
            if dependency not in ids:
                errors.append(f"{section_id}: unknown dependency {dependency}")
    if not parser.history:
        errors.append("plan needs change history")
    for change in parser.history:
        if not change.get("data-change-id") or not change.get("data-agent", ""):
            errors.append("history entry needs id and agent")
        if not EASTERN_TIMESTAMP.match(change.get("data-at", "")):
            errors.append("history entry needs valid data-at")
    if overall == "complete":
        if any(section.get("data-status") != "complete" for section in parser.sections):
            errors.append("complete plan has incomplete sections")
        if parser.signoff.get("data-signoff-status") != "approved":
            errors.append("complete plan needs approved sign-off")
        if not EASTERN_TIMESTAMP.match(parser.signoff.get("data-signed-at", "")):
            errors.append("complete plan needs data-signed-at")

    complete = {section.get("data-section-id") for section in parser.sections if section.get("data-status") == "complete"}
    next_section = ""
    for section in parser.sections:
        status = section.get("data-status")
        dependencies = set(filter(None, section.get("data-depends-on", "").split()))
        if status == "in_progress" or (status == "pending" and dependencies <= complete):
            next_section = section.get("data-section-id", "")
            break
    return {
        "path": str(source),
        "plan_id": parser.plan.get("data-plan-id", ""),
        "status": overall,
        "valid": not errors,
        "errors": errors,
        "next_section": next_section,
        "section_count": len(parser.sections),
        "complete_count": len(complete),
    }
