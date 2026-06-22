---
name: life-tasks
description: Capture, update, review, defer, complete, and prioritize personal tasks, errands, promises, and follow-ups in workspace life files.
---

# Life Tasks

Use this skill when the user asks to remember, track, plan, defer, review, or complete a task.
Use it for errands, chores, promises, waiting-for items, and personal admin.

## File

Store tasks in `life/tasks.json` as an array of objects.
Use `life_data` with `collection: "tasks"` for normal reads and writes.

Recommended fields:

- `id`: stable id such as `task-YYYYMMDD-HHMMSS`.
- `title`: short task title.
- `status`: `open`, `waiting`, `done`, or `cancelled`.
- `priority`: `low`, `normal`, `high`, or `urgent`.
- `due_at`: user-provided date/time text or ISO timestamp when known.
- `project`: optional grouping.
- `context`: optional, such as home, work, phone, online, travel, or errand.
- `waiting_for`: optional person or system blocking progress.
- `source`: optional source such as chat, email, manual, or companion-follow-up.
- `notes`: optional details.
- `created_at` and `updated_at`.

## Workflow

1. Use `life_data(action="list", collection="tasks")` when existing context matters.
2. Use `life_data(action="add"|"update", collection="tasks", ...)` for the relevant task.
3. Archive completed-obsolete records with `life_data(action="archive")`; do not hard-delete.
4. If the task has a time-sensitive reminder, use `life-reminders`.
5. If the task requires an external action, use `life-actions` before execution.
6. Let `life_data` append the audit entry.
7. Reply with the task id, status, priority, and important date if present.

Ask one short clarification only when the task cannot be represented safely, such as a
missing recipient for a promised follow-up.

## Reviews

When asked for a task review, order by:

1. overdue or due soon
2. urgent/high priority
3. waiting-for items that need nudges
4. active projects
5. everything else

Do not invent due dates. If the user asks "what should I do now", choose a small next action
from the highest-impact open item and explain the reason briefly.
