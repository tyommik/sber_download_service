"""
Download service
"""

import http
import asyncio
import json
import time

import websockets.server
from loguru import logger

from client import Client


async def health_check(path, request_headers):
    if path == "/health":
        return http.HTTPStatus.OK, [], b"OK\n"


class Service:
    def __init__(self, ip='127.0.0.1', port='8123', loglevel="WARNING"):
        self.ip = ip
        self.port = port
        self.id_counter = 0
        self.clients = []

    def handler_to_client(self, handler):
        for client in self.clients:
            if client.handler == handler:
                return client

    async def _register_new_client_(self, ws) -> Client:
        self.id_counter += 1
        client = Client(client_id=self.id_counter,
                        ip_address=ws.remote_address,
                        handler=ws
                        )
        self.clients.append(client)
        logger.info(f'{ws.remote_address} connects.')
        return client

    async def unregister(self, client) -> None:
        if client in self.clients:
            self.clients.remove(client)
        logger.info(f'{client.ip_address} disconnects.')

    async def send_to_clients(self, message: str) -> None:
        if self.clients:
            await asyncio.wait([client.handler.send(message) for client in self.clients])

    async def ws_handler(self, ws, uri: str) -> None:
        client = await self._register_new_client_(ws)
        try:
            await client.run()
        finally:
            await self.unregister(client)

    async def distribute(self, ws) -> None:
        async for message in ws:
            await self.send_to_clients(message)


if __name__ == '__main__':
    service = Service()
    start_server = websockets.serve(service.ws_handler,
                                    'localhost',
                                    8123,
                                    process_request=health_check,
                                    ping_interval=3,
                                    ping_timeout=9,
                                    close_timeout=10
                                    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
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

