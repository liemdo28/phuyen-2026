from __future__ import annotations

from app.models.domain import UserContext


def resolve_entity_reference(context: UserContext, extracted_fields: dict[str, object]) -> dict[str, object]:
    reference = str(extracted_fields.get("entity_reference") or "")
    if not reference:
        return extracted_fields
    latest = context.entities[-1] if context.entities else None
    if latest:
        extracted_fields.setdefault("resolved_entity_id", latest.entity_id)
        extracted_fields.setdefault("resolved_entity_type", latest.entity_type)
        for key, value in latest.payload.items():
            extracted_fields.setdefault(f"previous_{key}", value)
    return extracted_fields

