#!/usr/bin/env python3
"""Parses a BRD (PDF or Markdown) into candidate user stories with Salesforce component mapping.

Token-efficient by design: the script extracts and pre-structures requirements locally, so the LLM only
reviews a compact table instead of reading a 40-page document.

Usage:  python brd_to_stories.py brd.pdf --out stories.xlsx
"""
import argparse
import re
from pathlib import Path

COMPONENT_RULES = [
    (r"\b(field|picklist|checkbox|lookup)\b", "Custom Field", "admin", 1),
    (r"\b(validation|must not|prevent|required)\b", "Validation Rule", "admin", 1),
    (r"\b(automatically|when .* (created|updated)|notify|email alert)\b", "Record-Triggered Flow", "admin", 3),
    (r"\b(permission|access|visible to|profile)\b", "Permission Set", "admin", 1),
    (r"\b(report|dashboard)\b", "Report / Dashboard", "admin", 2),
    (r"\b(integrat|api|callout|webhook|external system)\w*", "Apex Integration", "dev", 5),
    (r"\b(batch|nightly|schedule|bulk)\b", "Batch / Scheduled Apex", "dev", 5),
    (r"\b(component|screen|ui|page)\b", "Lightning Web Component", "dev", 5),
    (r"\b(ai|llm|summar|predict|classif)\w*", "AI Integration (LLM)", "dev", 8),
]

REQ_LINE = re.compile(r"^\s*(?:FR|BR|REQ)?[-\s]?\d+[.)]?\s+(.+)$|^\s*[-*•]\s+(.+)$", re.IGNORECASE)


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    return path.read_text(encoding="utf-8")


def extract_requirements(text: str) -> list[str]:
    reqs = []
    for line in text.splitlines():
        m = REQ_LINE.match(line)
        if m:
            req = (m.group(1) or m.group(2)).strip()
            if len(req.split()) >= 5:
                reqs.append(req)
    return reqs


def map_requirement(req: str) -> dict:
    lowered = req.lower()
    matches = [(c, w, p) for pattern, c, w, p in COMPONENT_RULES if re.search(pattern, lowered)]
    components = sorted({c for c, _, _ in matches}) or ["Needs analysis"]
    work_types = {w for _, w, _ in matches}
    work_type = "mixed" if len(work_types) > 1 else (work_types.pop() if work_types else "tbd")
    points = min(13, sum(p for _, _, p in matches) or 2)
    return {
        "story": f"As a user, I want {req[0].lower() + req[1:].rstrip('.')}, so that the business process is supported.",
        "components": ", ".join(components),
        "workType": work_type,
        "points": points,
        "source": req,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("brd")
    parser.add_argument("--out", default="stories.xlsx")
    args = parser.parse_args()

    stories = [map_requirement(r) for r in extract_requirements(read_text(Path(args.brd)))]

    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    wb = Workbook()
    ws = wb.active
    ws.title = "Stories"
    headers = ["#", "User Story", "Components", "Work Type", "Points", "Source Requirement"]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="0B3D91")
    for i, s in enumerate(stories, start=1):
        ws.append([i, s["story"], s["components"], s["workType"], s["points"], s["source"]])
    for col, width in zip("ABCDEF", (5, 70, 35, 12, 8, 70)):
        ws.column_dimensions[col].width = width
    wb.save(args.out)
    print(f"{len(stories)} stories -> {args.out}")


if __name__ == "__main__":
    main()
