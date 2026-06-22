---
name: china-health
description: Manage health admin, medication reminders, appointment notes, hospital visit planning, and approval-gated China registration workflows without providing medical diagnosis.
---

# China Health

Use this skill for medication reminders, appointment records, hospital visit planning, checkup
admin, documents to bring, follow-up tasks, and health-related life organization.

## Scope

This skill is for administration and reminders, not diagnosis or medical treatment decisions.
Encourage professional care for symptoms, medication changes, emergencies, or uncertainty.

## File

Store health admin records in `life/health.json` as an array of objects.
Use `life_data` with `collection: "health"` for normal reads and writes.

Recommended fields:

- `id`: stable id such as `health-YYYYMMDD-HHMMSS`.
- `type`: medication-reminder, appointment, symptom-note, checkup, insurance, document, follow-up.
- `title`
- `status`: `planned`, `active`, `done`, `cancelled`, or `unknown`.
- `time_window`: optional.
- `hospital_or_clinic`: optional.
- `doctor_or_department`: optional.
- `linked_event_id`, `linked_task_id`, `linked_reminder_id`, `linked_document_id`.
- `notes`, `created_at`, `updated_at`.

## Workflow

1. Determine whether the request is admin, reminder, record keeping, or medical advice.
2. For admin/reminder tasks, use `life_data(action="add"|"update", collection="health", ...)` and related life files.
3. For medical advice, keep the response non-diagnostic and recommend qualified professionals.
4. For appointments, use `life-calendar` and `life-reminders`.
5. For ID/insurance/documents, use `life-documents`.
6. Use `life-actions` before hospital registration, cancellation, payment, message sending, or identity submission.

## Safety

Never change medication instructions, dosage, or treatment plans. Never claim emergency guidance
is complete. For urgent symptoms, advise contacting emergency services or local medical providers.

Health bookings, payments, cancellations, and identity submissions require approval plus second
confirmation.
