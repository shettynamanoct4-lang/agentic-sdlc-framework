"""Generates the specialist agent definitions in .claude/agents/ from one declarative spec.

Keeping agents in a single spec makes it easy to keep tool access, verdicts and handoffs consistent.
"""
from pathlib import Path

AGENTS = [
    ("business-analyst", "Turns discovery notes or call notes into a structured BRD draft.",
     "Discovery notes, meeting transcript, rough ask", "output/<slug>/brd.md",
     ["APPROVED", "CHANGES"], "product-owner",
     ["Capture objective, scope, actors, business rules, acceptance criteria, open questions.",
      "Never invent requirements; list assumptions explicitly.",
      "Publish the draft to the wiki only after human approval."]),
    ("product-owner", "Converts an approved BRD into epics, user stories and a component sheet.",
     "Approved BRD", "Story spreadsheet (via brd-to-stories skill); Jira issues after approval",
     ["APPROVED", "CHANGES", "NEEDS BRD CLARIFICATION"], "solution-architect",
     ["Each story: As a / I want / So that + Given-When-Then acceptance criteria.",
      "Tag every story with workType = admin | dev | mixed and a story-point estimate.",
      "Create Jira issues only after explicit approval."]),
    ("solution-architect", "Analyzes org impact / blast radius and recommends an approach.",
     "Approved stories", "output/<slug>/impact-analysis.md",
     ["APPROVED", "NEEDS RESCOPE", "BLOCKED"], "design",
     ["Query the live org (MCP) for existing objects, fields, flows, triggers and dependencies.",
      "Prefer reuse and declarative solutions; justify any code.",
      "Surface governance risks (new objects, limits, security) as a human decision."]),
    ("design", "Turns the approved approach into a buildable design split into admin vs developer work.",
     "Approved impact analysis", "output/<slug>/design.md",
     ["CONFIRMED", "CHANGES", "APPROACH WRONG"], "admin / developer",
     ["List every component with API names, field types, automation and security changes.",
      "Produce a ready-to-run prompt for the admin agent and for the developer agent.",
      "Ask clarifying questions instead of guessing."]),
    ("admin", "Builds declarative metadata: objects, fields, flows, validation rules, permission sets.",
     "Design (admin section)", "SFDX metadata in force-app/",
     ["BUILD COMPLETE", "BLOCKED"], "code-review",
     ["Generate metadata XML, validate with a check-only deploy, never deploy to production.",
      "Grant access through permission sets, not profiles."]),
    ("developer", "Builds Apex, triggers, LWC, integrations and their tests.",
     "Design (developer section)", "Apex/LWC source + tests",
     ["BUILD COMPLETE", "BLOCKED"], "code-review",
     ["Bulkified, with sharing, WITH USER_MODE, handler-pattern triggers, no SOQL/DML in loops.",
      "Tests: positive, negative, bulk (200+), permission scenarios; 90%+ coverage.",
      "Run Code Analyzer before handing off."]),
    ("code-review", "Reviews the change against Salesforce best practice and team coding standards.",
     "Branch / merge request", "output/<slug>/code-review.md",
     ["APPROVED", "APPROVED WITH WARNINGS", "CHANGES REQUIRED"], "qa",
     ["Run the apex-standards-review skill (static scan + Code Analyzer).",
      "Every finding cites file:line, severity and a concrete fix."]),
    ("qa", "Writes and runs Apex and end-to-end tests derived from acceptance criteria.",
     "Reviewed code + acceptance criteria", "output/<slug>/qa-report.md",
     ["PASS", "FAIL"], "devops",
     ["Map every acceptance criterion to at least one test.",
      "Use Playwright for UI journeys; attach screenshots as evidence.",
      "FAIL includes a defect list routed back to the developer."]),
    ("devops", "Prepares and promotes the release through environments.",
     "QA-approved change", "Release branch, merge request, validation and deploy results",
     ["VALIDATED", "DEPLOYED", "VALIDATION FAILED", "MERGE CONFLICT"], "next environment",
     ["Cherry-pick feature commits to a release branch; open a merge request.",
      "Always run a check-only validation with specified tests first.",
      "Production requires the typed phrase CONFIRM PRODUCTION."]),
    ("documentation", "Files each approved gate document and maintains a live project tracker.",
     "Any approved artifact", "Drive folder + wiki tracker page",
     ["FILED"], "—",
     ["Run after every gate; never alter the content of an approved document.",
      "Keep one tracker page per project linking every stage and its status."]),
]


def render(name, purpose, inputs, output, verdicts, nxt, rules):
    rule_lines = "\n".join(f"- {r}" for r in rules)
    return f"""---
name: {name}
description: {purpose}
---

# {name.replace('-', ' ').title()} agent

**Purpose:** {purpose}

| | |
|---|---|
| **Input** | {inputs} |
| **Output** | {output} |
| **Allowed verdicts** | {', '.join(verdicts)} |
| **Hands off to** | {nxt} |

## Rules
{rule_lines}
- Use MCP tools first; fall back to the `sf` CLI only when MCP is unavailable, and state why.
- Read and update your memory file in `.claude/agent-memory/{name}/` with durable lessons.

## End every response with
```
VERDICT: <one of: {' | '.join(verdicts)}>
REASON: <one line>
FINDINGS: []
RECOMMENDED_NEXT: {nxt}
```
"""


def main():
    root = Path(__file__).resolve().parent.parent
    for spec in AGENTS:
        agent_file = root / ".claude" / "agents" / f"{spec[0]}.md"
        agent_file.parent.mkdir(parents=True, exist_ok=True)
        agent_file.write_text(render(*spec))
        memory = root / ".claude" / "agent-memory" / spec[0] / "MEMORY.md"
        memory.parent.mkdir(parents=True, exist_ok=True)
        if not memory.exists():
            memory.write_text(f"# {spec[0]} memory\n\nDurable, project-agnostic lessons learned go here.\n")
    print(f"Generated {len(AGENTS)} agents")


if __name__ == "__main__":
    main()
