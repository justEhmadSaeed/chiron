from __future__ import annotations

import asyncio

import structlog

from chiron_backend.common.config import get_settings
from chiron_backend.common.logging import configure_logging

logger = structlog.get_logger(__name__)


async def worker_loop() -> None:
    settings = get_settings()
    logger.info(
        "agent_worker_started",
        redis_url=settings.redis_url,
        note="Replace this loop with a queue consumer such as Redis streams, Arq, or Celery.",
    )
    while True:
        await asyncio.sleep(5)
        logger.info("agent_worker_heartbeat")


def main() -> None:
    configure_logging()
    asyncio.run(worker_loop())


if __name__ == "__main__":
    main()
