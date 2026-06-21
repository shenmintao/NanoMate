---
name: china-local-services
description: Help with China local life services such as restaurants, reservations, events, errands, repairs, salons, tickets, and nearby service planning with approval-gated bookings.
---

# China Local Services

Use this skill for restaurants, cafes, salons, repairs, housekeeping, local tickets, event
planning, nearby errands, and service reservations.

## File

Store local-service records in `life/local-services.json` as an array of objects.

Recommended fields:

- `id`: stable id such as `local-YYYYMMDD-HHMMSS`.
- `type`: restaurant, cafe, repair, salon, cleaning, event, ticket, errand, other.
- `title`
- `location`
- `platform`: AMap, Dianping, Meituan, phone, WeChat, offline, unknown.
- `status`: `candidate`, `planned`, `reserved`, `completed`, `cancelled`.
- `time_window`: optional.
- `price_estimate`: optional.
- `notes`
- `linked_event_id`, `linked_task_id`, `linked_action_id`.
- `created_at`, `updated_at`.

## Workflow

1. Clarify city/area, time, budget, people count, and constraints when needed.
2. Use `china-maps`, web search, or available local-service integrations for options.
3. Present a short ranked list with tradeoffs.
4. Save selected candidates or plans.
5. Use `life-actions` before booking, paying deposits, cancelling, or sending messages/calls.
6. Add calendar and reminder records when plans are chosen.

## Boundaries

Public ratings can be stale or biased; present them as signals, not truth. Avoid over-optimizing
for fake precision.

Reservations, deposits, ticket purchases, calls, and messages are high risk.
