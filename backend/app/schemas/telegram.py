from __future__ import annotations

from pydantic import BaseModel, Field


class TelegramUser(BaseModel):
    id: int
    is_bot: bool = False
    first_name: str = ""
    username: str | None = None
    language_code: str | None = None


class TelegramChat(BaseModel):
    id: int
    type: str


class TelegramPhoto(BaseModel):
    file_id: str
    file_unique_id: str
    width: int
    height: int


class TelegramVoice(BaseModel):
    file_id: str
    duration: int
    mime_type: str | None = None


class TelegramLocation(BaseModel):
    latitude: float
    longitude: float


class TelegramMessage(BaseModel):
    message_id: int
    date: int
    chat: TelegramChat
    from_user: TelegramUser = Field(alias="from")
    text: str | None = None
    caption: str | None = None
    photo: list[TelegramPhoto] | None = None
    voice: TelegramVoice | None = None
    location: TelegramLocation | None = None
    via_bot: TelegramUser | None = None
    new_chat_members: list[TelegramUser] | None = None
    left_chat_member: TelegramUser | None = None
    group_chat_created: bool | None = None
    supergroup_chat_created: bool | None = None
    channel_chat_created: bool | None = None


class TelegramUpdate(BaseModel):
    update_id: int
    message: TelegramMessage | None = None
    edited_message: TelegramMessage | None = None
