from app.services.memory import MemoryService


async def _exercise_memory() -> str:
    memory = MemoryService()
    context = await memory.get_context(chat_id=1, user_id=2)
    await memory.append_user_turn(context, "thêm bill điện 2tr6")
    await memory.store_entity(context, "expense", "expenses-1", {"amount": 2600000})
    reloaded = await memory.get_context(chat_id=1, user_id=2)
    return memory.summarize(reloaded)


def test_memory_summary_contains_persisted_context() -> None:
    import asyncio

    summary = asyncio.run(_exercise_memory())
    assert "thêm bill điện 2tr6" in summary
    assert "expense:expenses-1" in summary
