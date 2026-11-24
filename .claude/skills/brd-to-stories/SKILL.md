---
name: brd-to-stories
description: Converts an approved BRD (PDF or Markdown) into user stories with Salesforce component mapping, work type and story points. Use when the product-owner agent builds a backlog.
---

# BRD to stories

1. Run the parser (requires `pypdf` and `openpyxl`):
   ```bash
   python .claude/skills/brd-to-stories/scripts/brd_to_stories.py <brd.pdf> --out output/<slug>/stories.xlsx
   ```
2. Review the generated table: rewrite story text into proper *As a / I want / So that* form and add
   Given-When-Then acceptance criteria for each story.
3. Merge or split stories so each is independently deliverable within a sprint.
4. Present the backlog for approval. Create Jira issues only after the human approves.
