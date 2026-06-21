---
name: life-ledger
description: Track expenses, income, reimbursements, budgets, subscriptions, bills, and financial summaries in workspace life files without making payments automatically.
---

# Life Ledger

Use this skill when the user mentions spending, income, reimbursements, budgets,
subscriptions, bills, refunds, price comparisons, or financial tracking.

## File

Store ledger records in `life/ledger.json` as an array of objects.

Recommended fields:

- `id`: stable id such as `txn-YYYYMMDD-HHMMSS`.
- `type`: `expense`, `income`, `transfer`, `refund`, `budget`, or `adjustment`.
- `amount`: number when known.
- `currency`: default to `CNY` unless the user states otherwise.
- `category`: concise category.
- `merchant`: optional.
- `occurred_at`: user-provided date/time text or ISO timestamp.
- `payment_method`: optional.
- `reimbursable`: optional boolean.
- `linked_subscription_id`: optional id from `life/subscriptions.json`.
- `linked_trip_id`: optional id from `life/trips.json`.
- `source`: optional, such as manual, screenshot, csv, email, or notification.
- `notes`: optional.
- `created_at` and `updated_at`.

## Workflow

1. Read `life/ledger.json` if it exists.
2. Add or update the relevant record.
3. Preserve valid JSON and existing entries.
4. If the record is recurring, also use `life-subscriptions`.
5. Append a short audit entry to `life/audit.md`.
6. Reply with amount, currency, category, and transaction id.

If amount or direction is unclear, ask one short clarification. Do not guess money values.

## Payments

Recording a ledger entry is low risk. Making a payment, transfer, purchase, refund, or
subscription change is high risk. Use `life-actions` first and require explicit approval.
Money movement, public communication, and hard-to-undo financial changes need second confirmation.
