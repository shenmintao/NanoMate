---
name: life-subscriptions
description: Track subscriptions, trials, memberships, recurring bills, renewals, cancellation windows, and recurring ledger entries in workspace life files.
---

# Life Subscriptions

Use this skill when the user mentions recurring payments, memberships, renewals, trials,
auto-renewal, cancellation dates, or bills.

## File

Store subscriptions in `life/subscriptions.json` as an array of objects.
Use `life_data` with `collection: "subscriptions"` for normal reads and writes.

Recommended fields:

- `id`: stable id such as `sub-merchant-plan`.
- `name`: subscription or bill name.
- `merchant`: optional.
- `status`: `active`, `trial`, `paused`, `cancelled`, or `unknown`.
- `amount`: optional number.
- `currency`: default `CNY` unless stated otherwise.
- `billing_cycle`: monthly, yearly, weekly, one-time-renewal, or custom.
- `next_billing_at`: optional.
- `cancel_by`: optional.
- `payment_method`: optional label only.
- `linked_reminder_id`: optional.
- `linked_ledger_ids`: optional array.
- `notes`: optional.
- `created_at` and `updated_at`.

## Workflow

1. Use `life_data(action="list", collection="subscriptions")` when existing context matters.
2. Use `life_data(action="add"|"update", collection="subscriptions", ...)` for the subscription.
3. Add or update a ledger record with `life-ledger` when a payment happened.
4. Add a reminder before renewal or cancellation deadlines with `life-reminders`.
5. Let `life_data` append the audit entry.
6. Reply with next billing/cancel date and subscription id.

Cancelling, upgrading, downgrading, paying, or changing a subscription in an external system is
high risk. Use `life-actions` first.
