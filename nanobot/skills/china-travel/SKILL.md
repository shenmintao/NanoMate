---
name: china-travel
description: Plan China travel, trains, flights, hotels, itinerary candidates, ticket watch, packing, and approval-gated bookings across 12306, airlines, Ctrip, Fliggy, and similar services.
---

# China Travel

Use this skill for domestic travel planning: 12306 trains, flights, hotels, itineraries,
packing, travel documents, price watches, and trip reminders.

## File

Store travel state in `life/trips.json` as an array of objects.
Use `life_data` with `collection: "trips"` for normal reads and writes.

Recommended fields:

- `id`: stable id such as `trip-YYYYMMDD-city`.
- `destination`
- `date_range`
- `status`: `idea`, `researching`, `planned`, `booked`, `completed`, or `cancelled`.
- `travellers`: optional labels only.
- `transport_candidates`: train/flight/bus options.
- `hotel_candidates`: hotel options.
- `itinerary`: optional daily outline.
- `budget`: optional.
- `linked_event_ids`, `linked_task_ids`, `linked_document_ids`.
- `booking_refs`: verified booking refs only after real execution.
- `notes`, `created_at`, `updated_at`.

## Workflow

1. Clarify destination, dates, people, budget, and constraints only when needed.
2. Search or use available integrations for candidate trains/flights/hotels.
3. Compare options by time, cost, transfer risk, location, refund/change policy, and user preferences.
4. Store selected candidates with `life_data(action="add"|"update", collection="trips", ...)`.
5. Add calendar items, packing tasks, weather checks, and document reminders as needed.
6. Use `life-actions` before booking, paying, cancelling, or changing tickets/hotels.

## Booking Boundary

Planning and price watching are allowed. Actual booking, payment, cancellation, seat selection,
identity submission, or passenger changes are high risk and require approval plus second
confirmation.

Do not claim 12306, airline, or OTA booking success without verified output from a real tool or
integration.

## Companion Fusion

When the user frames travel as "go with me" or a shared moment, use the companion voice and
`life-companion-bridge`; still keep booking facts and approval boundaries explicit.
