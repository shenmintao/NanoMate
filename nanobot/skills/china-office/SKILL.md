---
name: china-office
description: Coordinate Feishu, DingTalk, and WeCom office workflows for calendars, todos, messages, docs, meetings, and approvals with explicit external-action approval.
---

# China Office

Use this skill for domestic office platforms: Feishu/Lark, DingTalk, and WeCom/Enterprise
WeChat. Typical tasks include calendar planning, todos, meeting notes, docs, reminders,
message drafts, and approval tracking.

## Integration Levels

- `local`: record office tasks/events in `life/` files only.
- `connected`: use configured OAuth/app credentials, MCP server, or tool integration.
- `draft-only`: prepare text or payload for the user to paste.

Assume `local` unless a real integration is available in the current tool list or config.

## Files

- `life/tasks.json`: todos, follow-ups, approvals to chase.
- `life/calendar.json`: meetings and deadlines.
- `life/documents.json`: docs, contracts, links, and renewals.
- `life/people.json`: coworkers and external contacts.
- `life/pending-actions.json`: external calendar writes, messages, or approval submissions.

## Workflow

1. Identify platform: Feishu, DingTalk, or WeCom.
2. Decide whether the request is record, draft, search, or external write.
3. Use local files for durable state.
4. Use a real integration only if configured.
5. Use `life-actions` before sending messages, creating external calendar events, modifying docs, or submitting approvals.
6. Verify external results and store returned ids when available.

## Messages

Drafting a message is low risk. Sending it is high risk. Before sending, show:

- recipient or group
- exact message
- platform
- attachments or links
- timing

Then wait for approval.

## Companion Fusion

If Companion Mode is active, keep office stress support warm, but do not hide professional
constraints. Practical office outputs should remain clear and auditable.
