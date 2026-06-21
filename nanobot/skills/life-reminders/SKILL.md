---
name: life-reminders
description: Create, update, review, and remove reminders, recurring nudges, heartbeat check-ins, and cron-backed scheduled tasks in workspace life files.
---

# Life Reminders

Use this skill when the user asks to be reminded, nudged, checked in on, woken, warned, or
notified later.

## File

Store reminder metadata in `life/reminders.json` as an array of objects.

Recommended fields:

- `id`: stable id such as `reminder-YYYYMMDD-HHMMSS`.
- `title`: short reminder.
- `message`: exact message or task prompt.
- `status`: `active`, `paused`, `done`, or `cancelled`.
- `schedule_text`: user-provided schedule.
- `cron_job_id`: id returned by the cron tool when created.
- `linked_task_id`, `linked_event_id`, `linked_goal_id`, or `linked_subscription_id`.
- `channel`: optional target channel if known.
- `tone`: practical, gentle, companion, urgent, etc.
- `created_at` and `updated_at`.

## Workflow

1. Clarify date/time only if it is ambiguous enough to cause a wrong reminder.
2. Read `life/reminders.json` if it exists.
3. Use the `cron` tool for actual scheduled reminders when available.
4. Record the cron job id and reminder metadata.
5. Link the reminder to tasks, calendar, goals, subscriptions, health, or companion care when relevant.
6. Append a short audit entry to `life/audit.md`.
7. Reply with the reminder id and scheduled time.

Do not claim a reminder is scheduled unless the cron tool succeeded or the reminder was otherwise
stored as a local unscheduled record with that limitation stated.

## Companion Check-Ins

For proactive care, use the user's preferences and `life-companion-bridge`. Keep check-ins sparse
and context-aware. Respect sleep windows, quiet hours, and any "do not bother me" preference.
