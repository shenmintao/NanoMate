---
name: life-calendar
description: Track plans, appointments, reminders, trips, and calendar-like commitments in workspace life files.
---

# Life Calendar

Use this skill when the user mentions appointments, trips, deadlines, reminders, reservations, or time-based plans.

## File

Store calendar-like records in `life/calendar.json` as an array of objects.

Recommended fields:

- `id`: stable id such as `event-YYYYMMDD-HHMMSS`.
- `title`: short event title.
- `starts_at`: user-provided date/time text or ISO timestamp.
- `ends_at`: optional.
- `location`: optional.
- `participants`: optional array.
- `source`: optional, such as chat, email, booking site, or manual.
- `status`: `planned`, `tentative`, `confirmed`, `cancelled`, or `done`.
- `notes`: optional.
- `created_at` and `updated_at`.

## Workflow

1. Read `life/calendar.json` if it exists.
2. Add or update the relevant record.
3. Preserve valid JSON and existing entries.
4. Append a short audit entry to `life/audit.md`.
5. Confirm what was recorded, including date/time uncertainty if any.

## External Calendars And Bookings

Adding a local plan is low risk. Changing a third-party calendar, making a reservation, buying a ticket, or cancelling a booking is high risk. For high-risk actions, follow the `life-manager` approval policy and record the proposal in `life/pending-actions.json` first.

Never claim that an external booking or calendar change is complete unless a real integration/tool executed it and returned a verified result.
