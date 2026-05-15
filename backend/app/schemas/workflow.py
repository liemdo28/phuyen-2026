from __future__ import annotations

from pydantic import BaseModel, Field


class SheetMapping(BaseModel):
    domain: str
    spreadsheet_id: str | None = None
    sheet_name: str
    gid: str | None = None
    key_columns: list[str] = Field(default_factory=list)
    writable_columns: list[str] = Field(default_factory=list)
