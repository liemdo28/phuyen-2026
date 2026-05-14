# AI Training and Prompt Tuning Guide

## Goal

Train the assistant to understand natural Vietnamese while keeping internal orchestration and prompts in English.

## Prompting principles

1. User-facing output should feel like a helpful human operator.
2. Internal extraction should return structured English keys.
3. The model should infer intent before asking a question.
4. A follow-up question is only allowed when a write action is unsafe without clarification.

## Recommended fine-tuning / eval dataset buckets

- Expense creation from short Vietnamese phrases
- Task updates from incomplete references
- Inventory and revenue queries
- Travel assistant questions with location and time context
- OCR cleanup from messy receipt text
- Mixed English/Vietnamese office chat

## Sample training pairs

### Expense

User:
`Thêm bill điện 2 triệu 6`

Expected extraction:

```json
{
  "intent_type": "create",
  "domain": "expense",
  "extracted_fields": {
    "amount": 2600000,
    "category": "utilities_electricity"
  }
}
```

### Task update

User:
`Dời deadline task kitchen sang thứ 6`

Expected extraction:

```json
{
  "intent_type": "update",
  "domain": "task",
  "extracted_fields": {
    "entity_name": "kitchen",
    "deadline_relative": "Friday"
  }
}
```

### Context carry-over

Conversation:

1. `Thêm chi phí sơn 700k`
2. `Update cái trên thêm 500k`

Expected behavior:

- message 2 resolves to the latest expense entity
- final amount delta is interpreted against the previous record

## Eval checklist

- Can the model parse compact money formats like `2tr6`, `650k`, `1,2tr`?
- Can it resolve `hôm qua`, `mai`, `thứ 6`, `cuối tuần` correctly?
- Can it avoid over-asking when intent is obvious?
- Can it separate chat intent from sheet-write intent?
- Can it maintain the correct domain between turns?

