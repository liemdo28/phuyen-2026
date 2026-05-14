import asyncio

from app.services.job_queue import JobQueue
from app.services.orchestrator import TelegramOrchestrator


async def main() -> None:
    queue = JobQueue()
    orchestrator = TelegramOrchestrator()
    await queue.run_worker(orchestrator.handle_update)


if __name__ == "__main__":
    asyncio.run(main())
