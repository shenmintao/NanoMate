---
name: life-goals
description: Track personal goals, habits, projects, progress checkpoints, motivation context, and next actions in workspace life files.
---

# Life Goals

Use this skill when the user discusses goals, habits, long-term plans, routines, self-improvement,
study, fitness, finances, career, or projects.

## File

Store goals in `life/goals.json` as an array of objects.
Use `life_data` with `collection: "goals"` for normal reads and writes.

Recommended fields:

- `id`: stable id such as `goal-YYYYMMDD-short-name`.
- `title`: concise goal.
- `status`: `active`, `paused`, `completed`, or `cancelled`.
- `area`: health, career, study, finance, relationship, home, travel, creative, etc.
- `why`: optional motivation in the user's words.
- `target`: optional outcome or metric.
- `cadence`: daily, weekly, monthly, one-time, or custom.
- `next_action_task_id`: optional task id.
- `checkpoints`: optional array of dated progress notes.
- `support_style`: optional, such as gentle, direct, playful, or companion-like.
- `created_at` and `updated_at`.

## Workflow

1. Use `life_data(action="list", collection="goals")` when existing context matters.
2. Use `life_data(action="add"|"update", collection="goals", ...)` for the relevant goal.
3. Convert concrete next actions into `life-tasks`.
4. Convert scheduled check-ins into `life-reminders`.
5. Add meaningful reflections to `life/journal.md` when appropriate.
6. Let `life_data` append the audit entry.
7. Reply with the goal id and the next action.

## Sustained Work

For a goal that requires multi-turn execution by NanoMate, use the long-goal mechanism when
available. Keep the life goal record as durable user-facing state; keep the long-goal marker as
runtime execution state.
