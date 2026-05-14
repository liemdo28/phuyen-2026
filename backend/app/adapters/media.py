from __future__ import annotations


class MediaAdapter:
    async def transcribe_voice(self, file_id: str) -> str:
        return f"[voice transcription pending for {file_id}]"

    async def extract_receipt(self, file_id: str) -> dict[str, object]:
        return {
            "vendor": "unknown",
            "amount": None,
            "date": None,
            "raw_text": f"[ocr pending for {file_id}]",
        }

