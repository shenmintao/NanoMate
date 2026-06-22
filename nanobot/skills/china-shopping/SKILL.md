---
name: china-shopping
description: Manage China shopping lists, price watches, food delivery, orders, returns, coupons, and approval-gated purchases across Taobao, JD, Pinduoduo, Meituan, Ele.me, and similar services.
---

# China Shopping

Use this skill for shopping, groceries, food delivery, coupons, price comparisons, wish lists,
orders, returns, and platform-specific purchase planning.

## File

Store shopping records in `life/shopping.json` as an array of objects.
Use `life_data` with `collection: "shopping"` for normal reads and writes.

Recommended fields:

- `id`: stable id such as `shop-YYYYMMDD-HHMMSS`.
- `type`: `shopping-list`, `price-watch`, `candidate`, `order`, `return`, `food-delivery`, or `wish`.
- `title`
- `platform`: Taobao, Tmall, JD, Pinduoduo, Meituan, Eleme, Douyin, Xiaohongshu, offline, unknown.
- `status`: `idea`, `watching`, `candidate`, `ordered`, `delivered`, `returned`, `cancelled`.
- `target_price`: optional.
- `current_price`: optional.
- `merchant`: optional.
- `quantity`: optional.
- `linked_express_id`: optional.
- `linked_ledger_id`: optional.
- `notes`, `created_at`, `updated_at`.

## Workflow

1. Identify whether the user wants a list, comparison, watch, order status, or purchase.
2. Use web/search/integrations for current price or product info when available.
3. Save selected items or watches with `life_data(action="add"|"update", collection="shopping", ...)`.
4. Link delivery to `china-express` and payments to `life-ledger`.
5. Use `life-actions` before placing orders, paying, returning, cancelling, messaging sellers, or changing addresses.

## Purchase Boundary

Comparing products and drafting cart choices is low risk. Placing an order or paying is high risk
and requires approval plus second confirmation.

Do not store full addresses, payment credentials, ID numbers, or one-time codes.

## Food Delivery

For food delivery, show restaurant, items, price, delivery address label, estimated time, and
platform before requesting approval. Never auto-order from a casual craving unless explicitly
approved.
