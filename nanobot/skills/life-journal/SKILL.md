---
name: life-journal
description: Write daily reflections, mood notes, companion memories, decision logs, and freeform personal journal entries in workspace life files.
---

# Life Journal

Use this skill when the user wants to journal, reflect, remember a moment, record mood, keep
a diary entry, or preserve a companion-relevant memory.

## File

Store journal entries in `life/journal.md`.
Use `life_data` with `collection: "journal"` and `action: "append"` for normal journal writes.

Recommended format:

```markdown
## YYYY-MM-DD

- HH:MM - <short title>: <entry>
```

For structured mood trends, store optional lightweight records in `life/mood.json` as an array:
Use `life_data` with `collection: "mood"` for structured mood records.

- `id`
- `observed_at`
- `mood`: user-provided or clearly stated emotion
- `intensity`: optional 1-5
- `context`
- `support_needed`: optional
- `source`

## Workflow

1. Use `life_data(action="get", collection="journal")` when existing context matters.
2. Use `life_data(action="append", collection="journal", ...)` to add a concise entry using the user's words where possible.
3. If the entry implies a task, event, preference, or person follow-up, route to the relevant skill.
4. Let `life_data` append the audit entry.
5. Reply naturally, especially when Companion Mode is active.

## Companion Memories

For companion-like moments, store the factual memory without forcing a clinical label. Example:

`21:30 - shared cooking moment: User felt proud after making dinner and wanted the companion to remember it.`

Do not store intimate, medical, or third-party details unless the user explicitly asks.
