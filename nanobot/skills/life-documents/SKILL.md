---
name: life-documents
description: Track personal documents, IDs, warranties, insurance, contracts, renewals, storage locations, and document-related reminders in workspace life files.
---

# Life Documents

Use this skill when the user mentions IDs, passports, licenses, certificates, insurance,
contracts, warranties, invoices, receipts, renewals, or where important documents are stored.

## File

Store document inventory in `life/documents.json` as an array of objects.

Recommended fields:

- `id`: stable id such as `doc-passport` or `doc-YYYYMMDD-short-name`.
- `title`: document name.
- `type`: id, passport, license, contract, warranty, insurance, receipt, invoice, certificate, other.
- `issuer`: optional.
- `storage_location`: optional human-readable location; avoid full secrets.
- `expires_at`: optional.
- `renewal_required`: optional boolean.
- `linked_reminder_id`: optional.
- `notes`: optional.
- `created_at` and `updated_at`.

## Workflow

1. Read `life/documents.json` if it exists.
2. Add or update the document record.
3. If expiry or renewal exists, use `life-reminders`.
4. If the document relates to a subscription, trip, purchase, or health appointment, link to that record.
5. Append a short audit entry to `life/audit.md`.
6. Reply with the document id and renewal reminder if created.

## Privacy

Do not store full ID numbers, passwords, one-time codes, bank card numbers, or private keys.
Use labels and last-four-style hints only if the user explicitly asks.

Uploading, submitting, deleting, or changing documents in external systems is high risk. Use
`life-actions` first.
