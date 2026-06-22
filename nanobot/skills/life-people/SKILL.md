---
name: life-people
description: Maintain contacts, relationship context, promises, communication preferences, birthdays, and follow-ups in workspace life files.
---

# Life People

Use this skill when the user mentions a person, relationship, contact detail, birthday,
preference, promise, conflict, or follow-up involving someone else.

## File

Store people records in `life/people.json` as an array of objects.
Use `life_data` with `collection: "people"` for normal reads and writes.

Recommended fields:

- `id`: stable id such as `person-name-or-alias`.
- `name`: display name.
- `aliases`: optional array.
- `relationship`: friend, family, coworker, vendor, doctor, landlord, etc.
- `contact_methods`: optional array; avoid storing secrets.
- `important_dates`: optional array of birthday, anniversary, appointment, or deadline records.
- `preferences`: optional notes about communication style, gifts, food, or boundaries.
- `open_loops`: optional promises, replies owed, or follow-ups.
- `last_contacted_at`: optional.
- `notes`: optional.
- `created_at` and `updated_at`.

## Workflow

1. Use `life_data(action="list", collection="people")` when existing context matters.
2. Use `life_data(action="add"|"update", collection="people", ...)` for facts the user clearly provided or confirmed.
3. Link promised follow-ups to `life/tasks.json`.
4. Link birthdays or appointments to `life/calendar.json` and `life/reminders.json` when useful.
5. Let `life_data` append the audit entry.
6. Reply with what was remembered and any follow-up id.

## Privacy

Do not infer sensitive attributes. Do not store private contact details, health details, conflict
details, or intimate relationship facts unless the user explicitly asks you to remember them.

Sending a message to another person is high risk. Drafting is low risk; sending requires
`life-actions` and approval.
