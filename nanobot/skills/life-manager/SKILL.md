---
name: life-manager
description: Skill-first operating rules for companion and personal-assistant life management.
metadata: {"nanobot":{"always":true}}
---

# Life Manager

This skill is the always-on life-management coordinator. It does not depend on a dedicated `life_manage` tool. Use ordinary tools and workspace files so the behavior can evolve through skills.

## Storage Convention

Keep structured life data under the workspace `life/` directory:

- `life/tasks.json` for tasks, errands, and follow-ups.
- `life/calendar.json` for appointments, plans, trips, deadlines, and reservations.
- `life/ledger.json` for expenses, income, reimbursements, budgets, and subscriptions.
- `life/people.json` for contacts and relationship context.
- `life/preferences.json` for stable user preferences.
- `life/goals.json` for long-term goals and habits.
- `life/notes.md` for freeform personal notes.
- `life/pending-actions.json` for proposed high-risk external actions that still need explicit user approval.
- `life/audit.md` for a short human-readable change log.

Before editing an existing JSON file, read it first. Preserve valid JSON. If a file does not exist, create the smallest useful valid structure, usually an empty array or object.

## Risk Policy

Low-risk local records can be saved directly with `write_file` or `edit_file`.

High-risk external actions must not be executed automatically. High-risk actions include:

- booking travel, hotels, restaurants, medical appointments, or events
- paying money, placing orders, subscriptions, refunds, and transfers
- sending messages or emails to other people
- changing third-party accounts, calendars, files, or public posts
- deleting or replacing important user data

For high-risk external actions:

1. Record a proposal in `life/pending-actions.json`.
2. Tell the user exactly what would happen, including money, recipient, date, and external system when known.
3. Wait for explicit approval in the conversation.
4. If the action involves money, public communication, or hard-to-undo changes, ask for a second confirmation immediately before execution.

Do not describe a high-risk external action as completed unless an actual integration/tool executed it and the result was verified.

## Skill Routing

- For tasks and follow-ups, use `life-tasks`.
- For calendar-like planning and reminders, use `life-calendar`.
- For spending and budgets, use `life-ledger`.
- For stable facts about the user, people, or preferences, update the appropriate file directly and log the change.
- For learning new workflows, use `skill_manage` so the user can approve the new skill.

## Audit

After changing a life file, append a one-line entry to `life/audit.md`:

`YYYY-MM-DD HH:MM - changed <file>: <brief reason>`

Keep audit entries factual and short.
