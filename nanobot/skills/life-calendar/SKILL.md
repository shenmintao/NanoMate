---
name: life-calendar
description: Track appointments, plans, deadlines, reminders, trips, reservations, and calendar-like commitments in workspace life files.
---

# Life Calendar

Use this skill when the user mentions appointments, trips, deadlines, reminders, reservations,
time blocks, routines, or time-based plans.

## File

Store calendar-like records in `life/calendar.json` as an array of objects.

Recommended fields:

- `id`: stable id such as `event-YYYYMMDD-HHMMSS`.
- `title`: short event title.
- `starts_at`: user-provided date/time text or ISO timestamp.
- `ends_at`: optional.
- `timezone`: optional IANA timezone when known.
- `location`: optional.
- `participants`: optional array.
- `source`: optional, such as chat, email, booking site, office calendar, or manual.
- `status`: `planned`, `tentative`, `confirmed`, `cancelled`, or `done`.
- `external_ref`: optional third-party calendar/event id when a real integration produced one.
- `notes`: optional.
- `created_at` and `updated_at`.

## Workflow

1. Read `life/calendar.json` if it exists.
2. Add or update the relevant record.
3. Preserve valid JSON and existing entries.
4. If the event needs a reminder, use `life-reminders`.
5. If the event belongs to travel, local services, office work, or health, also update the matching skill file.
6. Append a short audit entry to `life/audit.md`.
7. Confirm what was recorded, including date/time uncertainty if any.

## External Calendars And Bookings

Adding a local plan is low risk. Changing a third-party calendar, making a reservation,
buying a ticket, or cancelling a booking is high risk. For high-risk actions, use
`life-actions` first and wait for approval.

Never claim that an external booking or calendar change is complete unless a real
integration/tool executed it and returned a verified result.
