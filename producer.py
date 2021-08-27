import asyncio
import websockets
import json
import time
from loguru import logger


class Client:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    def init(self):
        pass

    async def say_hello(self):
        msg = json.dumps({"type": 0x9, "msg": "Hello! It's client message!"})
        await asyncio.sleep(1)
        return msg

    async def read_message(self, ws) -> None:
        try:
            async for message in ws:
                print(message)
        except websockets.ConnectionClosedError as err:
            logger.error(f"err")
            return
        finally:
            await ws.close()
        return

    async def write_message(self, ws):
        try:
            while True:
                message = await self.say_hello()
                await ws.send(message)
        except websockets.ConnectionClosedError as err:
            logger.error(f"{str(err)}")
            return
        except websockets.ConnectionClosedOK as err:
            return
        except Exception as err:
            print(err)

    async def run(self):
        async with websockets.connect(f"ws://{self.ip}:{self.port}") as ws:
            try:
                read_task = asyncio.ensure_future(
                    self.read_message(ws))
                write_task = asyncio.ensure_future(
                    self.write_message(ws))
                done, pending = await asyncio.wait(
                    [read_task, write_task],
                    return_when=asyncio.ALL_COMPLETED,
                )
                for task in pending:
                    task.cancel()
            finally:
                ws.close()

if __name__ == '__main__':
    service = Client(ip='127.0.0.1', port=8123)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(service.run())
    try:
        loop.run_forever()
    except KeyboardInterrupt as err:
        logger.info(f"Received exit signal stop...")
        tasks = [t for t in asyncio.all_tasks(loop) if t is not
                 asyncio.current_task(loop)]

        for task in tasks:
            task.cancel()

        logger.info(f"Cancelling {len(tasks)} outstanding tasks")
        group = asyncio.gather(*tasks, return_exceptions=True)
        loop.run_until_complete(group)
        loop.stop()
        loop.close()

