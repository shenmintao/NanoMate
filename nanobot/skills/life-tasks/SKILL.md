---
name: life-tasks
description: Capture, update, review, and complete personal tasks and follow-ups in workspace life files.
---

# Life Tasks

Use this skill when the user asks to remember, track, plan, defer, review, or complete a task.

## File

Store tasks in `life/tasks.json` as an array of objects.

Recommended fields:

- `id`: stable id such as `task-YYYYMMDD-HHMMSS`.
- `title`: short task title.
- `status`: `open`, `waiting`, `done`, or `cancelled`.
- `priority`: `low`, `normal`, `high`, or `urgent`.
- `due_at`: user-provided date/time text or ISO timestamp when known.
- `project`: optional grouping.
- `notes`: optional details.
- `created_at` and `updated_at`.

## Workflow

1. Read `life/tasks.json` if it exists.
2. Create or update the relevant task.
3. Preserve valid JSON and existing entries.
4. Append a short audit entry to `life/audit.md`.
5. In the reply, state the task id and the important date/priority if present.

Ask one short clarification only when the task cannot be represented safely, such as a missing recipient for a promised follow-up.

## Reviews

When asked for a task review, sort mentally by overdue, due soon, high priority, then everything else. Do not invent due dates.
