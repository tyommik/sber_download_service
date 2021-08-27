import asyncio
from loguru import logger
import websockets


async def consumer_handler(websocket) -> None:
    async for message in websocket:
        log_message(message)


async def consume(hostname: str, port: int) -> None:
    websocket_resource_url = f"ws://{hostname}:{port}"
    async with websockets.connect(websocket_resource_url) as websocket:
        await consumer_handler(websocket)


def log_message(message: str) -> None:
    logger.info(message)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(consume(hostname="localhost", port=8123))
    loop.run_until_complete()