import json
import asyncio

import websockets
from loguru import logger

OPCODE_PING         = 0x9
OPCODE_PONG         = 0xA


class ClientProtocolError(Exception):
    pass


class Client:
    def __init__(self, client_id, ip_address, handler):
        self.client_id = client_id
        self.ip_address, self.port = ip_address
        self.handler = handler

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash(f"{self.client_id}:{self.ip_address}")

    async def _ping_received_(self, msg=None):
        payload = json.dumps({
            "type": OPCODE_PONG,
        })
        await self.handler.send(json.dumps(payload))

    async def write_message(self, msg=None):
        try:
            while True:
                message = await self.say_hello()
                await self.handler.send(message)
        except websockets.ConnectionClosedError as err:
            logger.error(f"{str(err)}")
            return
        except websockets.ConnectionClosedOK as err:
            return

    async def say_hello(self):
        msg = f"Hello {self.client_id}:{self.port}"
        await asyncio.sleep(0.1)
        return msg

    async def read_message(self, ws) -> None:
        try:
            async for message in ws:
                message = json.loads(message)
                try:
                    opcode = message.get('type', None)
                except AttributeError:
                    raise ClientProtocolError("Client use incorrect protocol")
                if opcode == OPCODE_PING:
                    logger.info(f"{ws.remote_address} ping")
                    opcode_handler = self._ping_received_
                else:
                    raise NotImplementedError
                await opcode_handler(ws)
        except websockets.ConnectionClosedError as err:
            logger.error(f"err")
            return
        finally:
            await ws.close()
        return

    async def run(self):
        read_task = asyncio.ensure_future(
            self.read_message(self.handler))
        write_task = asyncio.ensure_future(
            self.write_message(self.handler))
        done, pending = await asyncio.wait(
            [read_task, write_task],
            return_when=asyncio.ALL_COMPLETED,
        )
        for task in pending:
            task.cancel()