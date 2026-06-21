---
name: life-actions
description: Stage, approve, reject, execute, and verify high-risk external life actions such as bookings, payments, messages, account changes, purchases, and smart-home operations.
---

# Life Actions

Use this skill before any high-risk external action. It is the safety layer between planning
and execution.

## File

Store proposed actions in `life/pending-actions.json` as an array of objects.

Recommended fields:

- `id`: stable id such as `action-YYYYMMDD-HHMMSS`.
- `title`: short action title.
- `status`: `proposed`, `approved`, `rejected`, `executing`, `executed`, `failed`, or `cancelled`.
- `risk`: `medium`, `high`, or `critical`.
- `action_type`: `booking`, `payment`, `message`, `purchase`, `account-change`, `calendar-write`, `smart-home`, `health`, `delete-data`, or `other`.
- `external_system`: target system such as Feishu, WeCom, AMap, 12306, Ctrip, Alipay, WeChat Pay, JD, Meituan, Home Assistant, or Mi Home.
- `summary`: exact human-readable action.
- `payload_summary`: concise fields that would be submitted; never store secrets.
- `money`: optional amount/currency.
- `recipient`: optional recipient or merchant.
- `scheduled_for`: optional date/time.
- `requires_second_confirmation`: boolean.
- `approval_text`: exact user approval quote when approved.
- `second_confirmation_text`: exact second confirmation quote when required.
- `result`: verified outcome or failure reason.
- `created_at`, `updated_at`, and optional `executed_at`.

## Proposal Workflow

1. Read `life/pending-actions.json` if it exists.
2. Add a `proposed` action with enough detail for the user to audit.
3. Tell the user what would happen, which external system is involved, and what risk exists.
4. Ask for explicit approval.
5. Append a short audit entry to `life/audit.md`.

Do not execute the action while its status is `proposed`.

## Approval Workflow

When the user approves:

1. Match approval to the intended pending action. If ambiguous, ask which action id.
2. Update `status` to `approved` and record the approval quote.
3. If `requires_second_confirmation` is true, ask for a second confirmation immediately before execution.
4. Execute only through a real integration/tool.
5. Verify the returned result.
6. Update `status`, `result`, and the relevant life file.
7. Append an audit entry.

The words "approve" or "approved" are not enough if several actions are pending. Ask for the id.

## Critical Actions

Always require second confirmation for:

- payment, transfer, refund, subscription purchase, or order placement
- public or third-party messages
- travel or medical booking/cancellation
- identity, account, privacy, or document changes
- smart-home locks, cameras, alarms, gas, heat, or safety devices
- destructive file/data changes

Never self-approve. Never treat previous user intent as approval for a new or changed action.
