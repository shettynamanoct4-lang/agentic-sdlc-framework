#!/usr/bin/env python3
"""Fast, deterministic Apex standards scanner used by the code-review agent.

Why a script instead of asking the LLM? Pattern checks are cheaper, faster and 100% repeatable in code.
The agent then reasons over the findings (and Salesforce Code Analyzer output) to write the review.

Usage:  python scan_apex.py force-app/main/default/classes [--json]
"""
import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Finding:
    rule: str
    severity: str
    file: str
    line: int
    message: str


LOOP_START = re.compile(r"^\s*(for|while)\s*\(")
SOQL = re.compile(r"\[\s*SELECT\b", re.IGNORECASE)
DML = re.compile(r"\b(insert|update|upsert|delete|undelete)\s+\w+\s*;|Database\.(insert|update|upsert|delete)\(", re.IGNORECASE)


def scan_file(path: Path) -> list[Finding]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    findings: list[Finding] = []
    name = str(path)
    is_test = "@istest" in text.lower()

    header = "\n".join(lines[:40]).lower()
    if re.search(r"\bclass\b", header) and not is_test and "with sharing" not in header \
            and "inherited sharing" not in header and "without sharing" not in header:
        findings.append(Finding("SHARING", "Major", name, 1, "Class should declare 'with sharing' (or justify otherwise)."))

    depth_stack: list[int] = []
    brace_depth = 0
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        if LOOP_START.match(line):
            depth_stack.append(brace_depth)
        in_loop = bool(depth_stack)

        if in_loop and SOQL.search(line):
            findings.append(Finding("SOQL_IN_LOOP", "Critical", name, idx, "SOQL inside a loop - bulkify with a Map/Set."))
        if in_loop and DML.search(line):
            findings.append(Finding("DML_IN_LOOP", "Critical", name, idx, "DML inside a loop - collect records and DML once."))
        if SOQL.search(line) and not is_test:
            window = " ".join(lines[idx - 1: idx + 8]).upper()
            if "WITH USER_MODE" not in window and "WITH SECURITY_ENFORCED" not in window:
                findings.append(Finding("SOQL_USER_MODE", "Major", name, idx, "Add WITH USER_MODE to enforce CRUD/FLS."))
        if re.search(r"Database\.query\(\s*['\"].*\+", line):
            findings.append(Finding("SOQL_INJECTION", "Critical", name, idx, "Dynamic SOQL concatenation - use binds/queryWithBinds."))
        if re.search(r"['\"]00[0-9a-zA-Z]{13}(?:[0-9a-zA-Z]{3})?['\"]", line):
            findings.append(Finding("HARDCODED_ID", "Major", name, idx, "Hard-coded record Id."))
        if re.search(r"catch\s*\([^)]*\)\s*\{\s*\}", line):
            findings.append(Finding("EMPTY_CATCH", "Major", name, idx, "Empty catch block swallows errors."))
        if "System.debug" in line and not is_test:
            findings.append(Finding("DEBUG", "Minor", name, idx, "Remove or level-gate System.debug in production code."))

        brace_depth += line.count("{") - line.count("}")
        while depth_stack and brace_depth <= depth_stack[-1] and "}" in line:
            depth_stack.pop()

    if is_test and "Assert." not in text and "System.assert" not in text:
        findings.append(Finding("TEST_NO_ASSERT", "Major", name, 1, "Test class has no assertions."))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    files = [p for p in Path(args.path).rglob("*") if p.suffix in (".cls", ".trigger")]
    findings = [f for p in files for f in scan_file(p)]
    order = {"Critical": 0, "Major": 1, "Minor": 2}
    findings.sort(key=lambda f: (order[f.severity], f.file, f.line))

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        for f in findings:
            print(f"[{f.severity:8}] {f.rule:16} {f.file}:{f.line}  {f.message}")
        print(f"\n{len(files)} files scanned, {len(findings)} findings")
    return 1 if any(f.severity == "Critical" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
