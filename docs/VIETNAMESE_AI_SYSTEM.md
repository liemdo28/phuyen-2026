# Vietnamese Conversational AI System

## What is now implemented

### NLP preprocessing

- `backend/app/nlp/vietnamese_normalizer.py`
- `backend/app/nlp/slang_dictionary.py`
- `backend/app/nlp/money_parser.py`
- `backend/app/nlp/relative_date_parser.py`
- `backend/app/nlp/intent_preprocessor.py`

This layer normalizes casual Vietnamese before intent reasoning.

Examples supported now:

- `2tr6`
- `2 triệu 6`
- `2 củ 6`
- `1 tỷ 2`
- `mai`
- `mốt`
- `hôm kia`
- `tuần sau`
- `cafe nào chill gần đây`
- `thêm tiền nước luôn`

### AI reasoning modules

- `backend/app/ai/action_engine.py`
- `backend/app/ai/entity_resolver.py`
- `backend/app/ai/context_resolver.py`
- `backend/app/ai/workflow_reasoner.py`

These modules turn parsed Vietnamese into action-oriented business reasoning.

### Training assets

Training examples live under:

- `training/vietnamese/intents`
- `training/vietnamese/entities`
- `training/vietnamese/business`
- `training/vietnamese/workflow`

### Prompt assets

- `backend/app/prompts/vietnamese/conversational_few_shot.md`
- `backend/app/prompts/vietnamese/slang_examples.md`

## Current limitations

- still heuristic-first, not true model fine-tuning
- no vector retrieval yet
- no live Google Sheets row resolver yet
- OCR provider still stubbed in Python backend

## Recommended next step

Connect these modules to a structured LLM extraction layer so Vietnamese preprocessing becomes the first stage, not the only stage.
