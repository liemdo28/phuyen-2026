from __future__ import annotations

from dataclasses import dataclass, field

from app.nlp.money_parser import parse_money_amount, strip_money_phrases
from app.nlp.relative_date_parser import parse_relative_date
from app.nlp.vietnamese_normalizer import normalize_vietnamese_text


@dataclass
class PreprocessedIntent:
    original_text: str
    normalized_text: str
    money_amount: int | None = None
    iso_date: str | None = None
    stripped_text: str = ""
    hints: dict[str, object] = field(default_factory=dict)


def preprocess_intent_text(text: str) -> PreprocessedIntent:
    normalized_text = normalize_vietnamese_text(text)
    money_amount = parse_money_amount(normalized_text)
    iso_date = parse_relative_date(normalized_text)
    stripped_text = strip_money_phrases(normalized_text)
    hints: dict[str, object] = {}
    if "cung mot ngu canh" in normalized_text:
        hints["continue_previous_flow"] = True
    if any(token in normalized_text for token in ["luon", "luôn", "bo sung", "bổ sung"]):
        hints["continue_previous_flow"] = True
    if "ban ghi truoc do" in normalized_text:
        hints["entity_reference"] = "previous_record"
    if "ban ghi hom qua" in normalized_text:
        hints["entity_reference"] = "yesterday_record"
    return PreprocessedIntent(
        original_text=text,
        normalized_text=normalized_text,
        money_amount=money_amount,
        iso_date=iso_date,
        stripped_text=stripped_text,
        hints=hints,
    )
