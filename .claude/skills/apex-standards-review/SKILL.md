---
name: apex-standards-review
description: Reviews Apex classes and triggers against Salesforce best practices and team standards. Use when the code-review agent reviews a branch or merge request.
---

# Apex standards review

1. Run the deterministic scanner (fast, free, repeatable):
   ```bash
   python .claude/skills/apex-standards-review/scripts/scan_apex.py force-app/main/default/classes --json
   ```
2. Run Salesforce Code Analyzer (MCP `run_code_analyzer`, or `sf code-analyzer run` as fallback).
3. Merge both result sets, de-duplicate by `file:line`, and rank by severity.
4. Read `references/standards.md` and check the items scripts can't judge (naming, design, test quality).
5. Write `output/<slug>/code-review.md` with a findings table (`id · severity · file:line · issue · fix`).
6. Verdict: any **Critical** → `CHANGES REQUIRED`; only Minor/Major with mitigations → `APPROVED WITH WARNINGS`.
