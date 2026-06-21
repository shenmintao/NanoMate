---
name: china-express
description: Track China parcel deliveries, courier companies, pickup codes, delivery exceptions, returns, and package reminders in workspace life files.
---

# China Express

Use this skill for packages, express delivery, courier status, pickup codes, returns, and
delivery reminders in China.

## Integrations

Prefer official or user-configured providers:

- Kuaidi100 or Kdniao for multi-carrier tracking.
- SF Express Open Platform for SF packages.
- JD Logistics, Cainiao, or platform order pages when user-authorized.

If no API is configured, save the tracking record and ask the user to provide status manually or
authorize a provider later.

## File

Store package records in `life/express.json` as an array of objects.

Recommended fields:

- `id`: stable id such as `pkg-YYYYMMDD-HHMMSS`.
- `tracking_number`: optional; mask if privacy-sensitive.
- `carrier`: SF, JD, YTO, ZTO, STO, Yunda, EMS, Cainiao, unknown.
- `status`: `created`, `in_transit`, `out_for_delivery`, `pickup_ready`, `delivered`, `returning`, `exception`, or `unknown`.
- `description`: item label.
- `recipient_label`: user, family, office, etc.
- `pickup_code`: optional; avoid exposing in summaries unless needed.
- `last_checked_at`, `expected_at`, `delivered_at`.
- `linked_order_id`: optional shopping record.
- `notes`, `created_at`, `updated_at`.

## Workflow

1. Read `life/express.json` if it exists.
2. Add or update the package record.
3. Query a configured tracking integration if available.
4. Use `life-reminders` for pickup deadlines or delivery windows.
5. Link shopping records in `life/shopping.json` when relevant.
6. Append a short audit entry to `life/audit.md`.

Changing delivery address, contacting courier, refunding, returning, or authorizing pickup is
high risk. Use `life-actions` first.
