---
name: life-manager
description: Always-on coordinator for companion-compatible personal life management, routing tasks, calendar, money, people, preferences, goals, reminders, China services, and high-risk approvals through workspace life files.
metadata: {"nanobot":{"always":true}}
---

# Life Manager

This skill is the always-on coordinator for life-assistant behavior. It does not replace
SillyTavern, character cards, companion templates, or the user's chosen personality preset.
Use it as the factual and operational layer: records, plans, proposals, reminders, and approval
boundaries.

## Companion Boundary

Do not edit `nanobot/templates/skills/living-together` or
`nanobot/templates/skills/emotional-companion` as part of normal life-assistant work.

When Companion Mode is enabled:

- Let the SillyTavern character card and preset control identity, tone, intimacy level, and roleplay style.
- Let `living-together` control visual shared-moment behavior.
- Let `emotional-companion` control proactive emotional care.
- Use life skills only to provide facts, continuity, reminders, and safe action proposals.
- Keep replies natural for the active companion persona; do not turn companion conversations into a rigid checklist.
- If a life skill conflicts with the active persona's expression style, preserve the factual life operation but adapt the wording to the persona.

Use `life-companion-bridge` when a request mixes companion behavior with errands, records,
follow-ups, memories, or proactive care.

## Storage Convention

Keep structured life data under the workspace `life/` directory:

- `life/tasks.json` for tasks, errands, and follow-ups.
- `life/calendar.json` for appointments, plans, deadlines, and reservations.
- `life/reminders.json` for reminder definitions and cron-backed reminder metadata.
- `life/ledger.json` for expenses, income, budgets, reimbursements, and subscriptions.
- `life/subscriptions.json` for recurring bills, renewals, memberships, and trials.
- `life/people.json` for contacts and relationship context.
- `life/preferences.json` for stable user preferences.
- `life/goals.json` for goals, habits, and progress checkpoints.
- `life/journal.md` for daily reflections, mood notes, and companion-relevant memories.
- `life/notes.md` for freeform personal notes.
- `life/documents.json` for document inventories, warranties, IDs, contracts, and renewal dates.
- `life/trips.json` for travel plans, ticket candidates, hotels, and itinerary state.
- `life/express.json` for package tracking records.
- `life/shopping.json` for shopping lists, price watches, orders, and wish lists.
- `life/local-services.json` for restaurants, services, reservations, and local errands.
- `life/smart-home.json` for home devices, scenes, and safety notes.
- `life/health.json` for medication reminders, appointment records, and health admin notes.
- `life/pending-actions.json` for proposed high-risk external actions that still need approval.
- `life/audit.md` for a short human-readable change log.

Before editing an existing JSON file, read it first. Preserve valid JSON and existing records.
If a file does not exist, create the smallest useful valid structure, usually an empty array
or object.

Use the `life_data` tool for normal life-file reads and writes. It provides whitelisted
collections, stable ids, `created_at`/`updated_at`, soft archive instead of hard delete, and
automatic `life/audit.md` entries. Use raw file tools only when `life_data` cannot represent the
needed format.

## Delegation Levels

Classify each requested action before acting:

- `record`: local notes, tasks, events, ledger entries, and preferences. Save directly.
- `research`: search, compare, summarize, or draft options. Save findings when useful.
- `propose`: prepare an external action but do not execute it. Use `life-actions`.
- `execute`: perform an approved external action through a real integration/tool, then verify.

Never describe an external action as completed unless an actual integration/tool executed it
and the result was verified.

## Risk Policy

Low-risk local records can be saved directly with file tools.

High-risk external actions must not be executed automatically. High-risk actions include:

- booking, changing, or cancelling travel, hotels, restaurants, medical appointments, or events
- paying money, placing orders, subscriptions, refunds, and transfers
- sending messages or emails to other people
- changing third-party accounts, calendars, documents, files, smart-home devices, or public posts
- deleting or replacing important user data
- operating locks, cameras, alarms, gas, heat, medical, or other safety-sensitive devices

For high-risk external actions:

1. Use `life-actions` to record a proposal in `life/pending-actions.json`.
2. Tell the user exactly what would happen, including money, recipient, date, and external system when known.
3. Wait for explicit approval in the conversation.
4. If the action involves money, public communication, identity, health, security, or hard-to-undo changes, ask for a second confirmation immediately before execution.
5. Record the verified result or failure in the relevant life file and `life/audit.md`.

## Skill Routing

- Tasks and follow-ups: `life-tasks`.
- Calendar-like plans and appointments: `life-calendar`.
- Reminders and recurring nudges: `life-reminders`.
- Spending, budgets, reimbursements, and money records: `life-ledger`.
- Subscriptions and recurring bills: `life-subscriptions`.
- Contacts and relationship context: `life-people`.
- Stable preferences: `life-preferences`.
- Goals and habits: `life-goals`.
- Daily notes, memories, and mood logs: `life-journal`.
- Daily, weekly, or monthly summaries: `life-review`.
- Documents, IDs, warranties, insurance, and renewals: `life-documents`.
- Approval and external action proposals: `life-actions`.
- Companion/SillyTavern coordination: `life-companion-bridge`.
- China maps, commute, POI, and routing: `china-maps`.
- China weather and alerts: `china-weather`.
- China parcel tracking: `china-express`.
- Feishu, DingTalk, and WeCom workflows: `china-office`.
- China trains, flights, hotels, and trip planning: `china-travel`.
- Shopping, food delivery, and price watch workflows: `china-shopping`.
- Restaurants, local services, tickets, and errands: `china-local-services`.
- Home Assistant, Mi Home, and device scenes: `china-smart-home`.
- Health admin, medication reminders, and appointments: `china-health`.
- Structured life-file reads and writes: `life_data`.
- High-risk life action approval staging: `life_action`.
- Learning or importing new workflows: `skill_manage`, with user approval.
- Auditing or pruning agent-created workspace skills: `skill_curator`, with user approval
  for archive/pin changes.
- Configuring API keys or provider settings from conversation: `config_manage`, with user
  approval and masked secret summaries.

## Learning New Skills

Use `skill_manage` only when the user asks to add/update a reusable workflow or points to a
trusted `SKILL.md` source. Prefer patching an existing relevant skill over creating a narrow
near-duplicate. Do not learn secrets into skills; use `config_manage`, config files, or
environment variables.

Before creating a new skill, check whether an existing built-in or workspace skill already covers
the workflow. If the requested behavior is an extension of an existing skill, patch that skill
instead of creating a new one.

Use `skill_curator(action="audit")` when similar generated skills may be accumulating. It may
only soft-archive skills marked as agent-created; never use it to alter companion templates or
manual workspace skills.

## Audit

After changing a life file, append one concise entry to `life/audit.md`:

`YYYY-MM-DD HH:MM - changed <file>: <brief reason>`

Keep audit entries factual and short. Do not log private details that are not needed for
future review.
