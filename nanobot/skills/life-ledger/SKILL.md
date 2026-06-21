---
name: life-ledger
description: Track expenses, income, reimbursements, budgets, and subscriptions in workspace life files.
---

# Life Ledger

Use this skill when the user mentions spending, income, reimbursements, budgets, subscriptions, bills, or financial tracking.

## File

Store ledger records in `life/ledger.json` as an array of objects.

Recommended fields:

- `id`: stable id such as `txn-YYYYMMDD-HHMMSS`.
- `type`: `expense`, `income`, `transfer`, `refund`, or `budget`.
- `amount`: number when known.
- `currency`: default to `CNY` unless the user states otherwise.
- `category`: concise category.
- `merchant`: optional.
- `occurred_at`: user-provided date/time text or ISO timestamp.
- `payment_method`: optional.
- `reimbursable`: optional boolean.
- `notes`: optional.
- `created_at` and `updated_at`.

## Workflow

1. Read `life/ledger.json` if it exists.
2. Add or update the relevant record.
3. Preserve valid JSON and existing entries.
4. Append a short audit entry to `life/audit.md`.
5. Reply with amount, currency, category, and transaction id.

If amount or direction is unclear, ask one short clarification. Do not guess money values.

## Payments

Recording a ledger entry is low risk. Making a payment, transfer, purchase, refund, or subscription change is high risk. For high-risk actions, follow the `life-manager` approval policy and record the proposal in `life/pending-actions.json` first.
