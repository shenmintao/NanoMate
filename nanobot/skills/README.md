# nanobot Skills

This directory contains built-in skills that extend nanobot's capabilities.

## Skill Format

Each skill is a directory containing a `SKILL.md` file with:
- YAML frontmatter (name, description, metadata)
- Markdown instructions for the agent

When skills reference large local documentation or logs, prefer nanobot's built-in
`grep` tool to narrow the search space before loading full files.
Use `grep(output_mode="count")` / `files_with_matches` for broad searches first,
use `head_limit` / `offset` to page through large result sets,
and `grep(glob="*.md")` to filter by file name pattern.

## Attribution

These skills are adapted from [OpenClaw](https://github.com/openclaw/openclaw)'s skill system.
The skill format and metadata structure follow OpenClaw's conventions to maintain compatibility.

## Available Skills

| Skill | Description |
|-------|-------------|
| `github` | Interact with GitHub using the `gh` CLI |
| `weather` | Get weather info using wttr.in and Open-Meteo |
| `summarize` | Summarize URLs, files, and YouTube videos |
| `tmux` | Remote-control tmux sessions |
| `clawhub` | Search and install skills from ClawHub registry |
| `skill-creator` | Create new skills |
| `long-goal` | Sustained objectives: `long_task`, `complete_goal`, idempotent goals, modular project work, early research |
| `life-manager` | Always-on coordinator for companion-compatible life management |
| `life-companion-bridge` | Connect Companion Mode with life records, reminders, and approvals without changing companion templates |
| `life-actions` | Stage and approve high-risk external actions |
| `life-tasks` | Track personal tasks, errands, promises, and follow-ups |
| `life-calendar` | Track appointments, deadlines, trips, and reservations |
| `life-reminders` | Manage cron-backed reminders and companion check-ins |
| `life-ledger` | Track expenses, budgets, reimbursements, and financial records |
| `life-subscriptions` | Track renewals, trials, memberships, and recurring bills |
| `life-people` | Track contacts, relationship context, and follow-ups |
| `life-preferences` | Store stable preferences, boundaries, and defaults |
| `life-goals` | Track goals, habits, checkpoints, and next actions |
| `life-journal` | Store reflections, mood notes, and companion memories |
| `life-review` | Produce daily, weekly, monthly, task, mood, and financial reviews |
| `life-documents` | Track IDs, warranties, contracts, insurance, and renewals |
| `china-maps` | Handle China maps, route planning, POI, and errands |
| `china-weather` | Handle China weather, air quality, and weather-aware reminders |
| `china-express` | Track China parcel delivery and pickup reminders |
| `china-office` | Coordinate Feishu, DingTalk, and WeCom workflows |
| `china-travel` | Plan China trains, flights, hotels, trips, and approval-gated bookings |
| `china-shopping` | Manage China shopping lists, price watches, orders, and food delivery |
| `china-local-services` | Help with restaurants, reservations, events, repairs, and local errands |
| `china-smart-home` | Coordinate Home Assistant, Mi Home, scenes, and device safety |
| `china-health` | Manage health admin, reminders, appointments, and medical workflow boundaries |
