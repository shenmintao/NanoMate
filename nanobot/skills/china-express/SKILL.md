---
name: china-express
description: Track China parcel deliveries, courier companies, pickup codes, delivery exceptions, returns, and package reminders in workspace life files.
---

# China Express

Use this skill for packages, express delivery, courier status, pickup codes, returns, and
delivery reminders in China.

## Integrations

Prefer official or user-configured providers:

- `china_life` tool for tracking:
  - no reliable free/no-registration multi-carrier express API is assumed.
  - `provider: "kuaidi100"` works when `tools.chinaLife.kuaidi100Key` and
    `tools.chinaLife.kuaidi100Customer` are configured.
- Kdniao for multi-carrier tracking when separately configured.
- SF Express Open Platform for SF packages.
- JD Logistics, Cainiao, or platform order pages when user-authorized.

If no API is configured, save the tracking record and ask the user to provide status manually or
authorize a provider later.

If the user gives Kuaidi100 credentials in conversation, use `config_manage` to set
`tools.chinaLife.kuaidi100Key` and `tools.chinaLife.kuaidi100Customer`; wait for approval before
writing them.

## File

Store package records in `life/express.json` as an array of objects.
Use `life_data` with `collection: "express"` for normal reads and writes.

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

1. Use `life_data(action="list", collection="express")` when existing context matters.
2. Use `life_data(action="add"|"update", collection="express", ...)` for the package record.
3. Query `china_life` if a configured tracking integration is available.
4. Use `life-reminders` for pickup deadlines or delivery windows.
5. Link shopping records in `life/shopping.json` when relevant.
6. Let `life_data` append the audit entry.

Changing delivery address, contacting courier, refunding, returning, or authorizing pickup is
high risk. Use `life-actions` first.
