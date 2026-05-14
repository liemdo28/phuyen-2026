from __future__ import annotations

from app.schemas.workflow import SheetMapping


DEFAULT_MAPPINGS: dict[str, SheetMapping] = {
    "expenses": SheetMapping(
        domain="expenses",
        sheet_name="Chi Tiêu",
        key_columns=["date", "note", "amount"],
        writable_columns=["date", "note", "amount", "category", "group"],
    ),
    "tasks": SheetMapping(
        domain="tasks",
        sheet_name="Tasks",
        key_columns=["entity_name", "deadline", "status"],
        writable_columns=["entity_name", "deadline", "status", "note"],
    ),
    "inventory": SheetMapping(
        domain="inventory",
        sheet_name="Inventory",
        key_columns=["entity_name", "date"],
        writable_columns=["entity_name", "date", "quantity", "note", "status"],
    ),
    "revenue": SheetMapping(
        domain="revenue",
        sheet_name="Revenue",
        key_columns=["date", "amount"],
        writable_columns=["date", "amount", "note", "category"],
    ),
}


def get_sheet_mapping(domain: str) -> SheetMapping | None:
    return DEFAULT_MAPPINGS.get(domain)
