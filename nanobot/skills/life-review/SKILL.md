---
name: life-review
description: Produce daily, weekly, monthly, financial, task, mood, and life-admin reviews from workspace life files and write concise review summaries.
---

# Life Review

Use this skill when the user asks for a day review, week review, month review, life summary,
task review, spending review, mood review, or "what should I focus on".

## Inputs

Read only the files needed for the requested review:
Use `life_data(action="list"|"get", ...)` for these standard collections when possible.

- `life/tasks.json`
- `life/calendar.json`
- `life/reminders.json`
- `life/ledger.json`
- `life/subscriptions.json`
- `life/goals.json`
- `life/journal.md`
- `life/mood.json`
- `life/pending-actions.json`

## Output Files

When the user wants the review saved, write to:

- `life/reviews/YYYY-MM-DD.md` for daily reviews.
- `life/reviews/YYYY-WW.md` for weekly reviews.
- `life/reviews/YYYY-MM.md` for monthly reviews.

Create the directory if needed.

## Review Shape

Keep reviews compact:

- completed or meaningful progress
- overdue or upcoming items
- money highlights when relevant
- mood or energy pattern when relevant
- pending approvals
- next 1-3 recommended actions

Do not over-medicalize emotions. Do not invent patterns from one data point.

## Workflow

1. Read relevant life files, preferring `life_data` for standard collections.
2. Summarize evidence-backed facts.
3. Identify gaps or stale records.
4. Save the review only if requested or if it is part of a scheduled review workflow.
5. Use `life_data(action="append", collection="audit", ...)` for the audit entry if a review file was written.
6. Reply in the tone appropriate to the active context; use `life-companion-bridge` if Companion Mode is involved.
