from app.core import config as config_module
from app.schemas.telegram import TelegramMessage
from app.services.orchestrator import TelegramOrchestrator


def build_message(text: str) -> TelegramMessage:
    return TelegramMessage.model_validate(
        {
            "message_id": 1,
            "date": 1_778_000_000,
            "chat": {"id": 8654136346, "type": "private"},
            "from": {
                "id": 8654136346,
                "is_bot": False,
                "first_name": "Liem",
                "username": None,
            },
            "text": text,
        }
    )


def test_start_command_has_welcome_reply() -> None:
    object.__setattr__(config_module.settings, "app_env", "production")
    orchestrator = TelegramOrchestrator()
    reply = orchestrator._command_reply(build_message("/start"), "/start")
    assert reply is not None
    assert "Xin chào Liem" in reply
    assert "build railway-production" in reply


def test_id_command_returns_user_info() -> None:
    orchestrator = TelegramOrchestrator()
    reply = orchestrator._command_reply(build_message("/id"), "/id")
    assert reply is not None
    assert "User ID: 8654136346" in reply
    assert "@(chưa có)" in reply
