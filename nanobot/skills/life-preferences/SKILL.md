---
name: life-preferences
description: Store and apply stable user preferences, routines, boundaries, defaults, favorites, dislikes, and assistant behavior settings in workspace life files.
---

# Life Preferences

Use this skill when the user states a stable preference, routine, boundary, default choice,
favorite, dislike, or assistant behavior rule.

## File

Store preferences in `life/preferences.json` as an object grouped by domain.

Recommended top-level keys:

- `assistant`: tone, verbosity, approval expectations, proactive behavior.
- `companion`: emotional boundaries, check-in style, visual-memory preferences.
- `schedule`: wake/sleep windows, work hours, timezone, reminder preferences.
- `food`: dietary limits, favorite cuisines, allergies if explicitly provided.
- `travel`: seat, hotel, route, budget, and document preferences.
- `shopping`: brands, sizes, addresses by label only, budget defaults.
- `finance`: categories, budget targets, reimbursement defaults.
- `health`: reminder preferences and care boundaries, not diagnosis.
- `privacy`: data the user does or does not want remembered.

Each preference can include:

- `value`
- `source`
- `confidence`: `confirmed` or `inferred`
- `updated_at`

## Workflow

1. Read `life/preferences.json` if it exists.
2. Save explicit user preferences as `confirmed`.
3. Save inferences only when useful and label them `inferred`; ask before using them for high-impact decisions.
4. Apply relevant preferences when using other life skills.
5. Append a short audit entry to `life/audit.md`.
6. Reply briefly with what changed.

## Boundaries

If a preference affects money, health, identity, relationships, or safety, ask for confirmation
before treating it as a standing rule.
