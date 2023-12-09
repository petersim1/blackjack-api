import asyncio
import json
import logging
from typing import Iterator

from pydantic import ValidationError
from starlette.endpoints import WebSocketEndpoint
from starlette.exceptions import WebSocketException
from starlette.websockets import WebSocket

from app.helpers.ws import gather_responses, handle_init
from app.modules.game import Game
from app.pydantic_types import MessageSend

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL = 5


class Consumer(WebSocketEndpoint):
    task = None
    clients = set()
    game = None
    balance = 0

    async def on_connect(self, websocket: WebSocket):
        logger.info(f"connection started {websocket.client.port}")
        await websocket.accept()

        self.clients.add(websocket)
        message = MessageSend(
            ready=False,
            round_over=True,
        )
        await websocket.send_json(message.model_dump())

    async def on_receive(self, websocket: WebSocket, data: object):
        if self.task is not None:
            # could send a message back to client, but could also just do nothing.
            return
        data: dict = json.loads(data)
        code = data.get("code", None)
        match code:
            case "init":
                # "init" -> setting up the Game module with outlined rules.
                try:
                    game_hyperparams = handle_init(data)
                except ValidationError:
                    return
                self.game = Game(**game_hyperparams)
                message = MessageSend(
                    ready=True,
                    round_over=True,
                )
                await websocket.send_json(message.model_dump())

            case "reset":
                # Handled similarly to on_connect(), completely reset game,
                # and force client to reestablish gameplay.
                self.game = None
                self.balance = 0
                message = MessageSend(
                    ready=False,
                    round_over=True,
                )
                await websocket.send_json(message.model_dump())

            case "start" | "step":
                if not self.game:
                    return
                responses = gather_responses(self, data, code)
                self.task = asyncio.create_task(
                    self.send_sequential_messages(responses, websocket)
                )

            case "close":
                message = {"count": 0, "text": "closing connection", "policy": []}
                await websocket.send_text(json.dumps(message))
                await websocket.close()

            case _:
                # maybe implement a closure?
                pass

    async def send_sequential_messages(
        self, messages: Iterator[MessageSend], websocket: WebSocket
    ) -> None:
        message = next(messages, None)
        while message is not None:
            # this logic only places a timeout between messages,
            # not just after each message. Helps with backend throttling issues.
            await websocket.send_json(message.model_dump())
            message = next(messages, None)
            if message is not None:
                await asyncio.sleep(1)
        self.task = None

    def broadcast(self, message: str, cur_ws: WebSocket):
        client: WebSocket
        for client in self.clients:
            try:
                m = message
                if cur_ws != client:
                    m += " from other client"
                asyncio.create_task(client.send_text(m))
            except WebSocketException:
                # in case that a client closed while something was being broadcasted.
                pass

    async def heartbeat(self, websocket: WebSocket):
        while True:
            try:
                # Send a ping message to the client
                await websocket.send_json({"type": "ping"})

                # Wait for the pong response within a timeout
                message = await asyncio.wait_for(websocket.receive_json(), timeout=3)
                if message["type"] != "pong":
                    raise WebSocketException
            except asyncio.TimeoutError:
                await websocket.close()
                break
            except WebSocketException:
                await websocket.close()
                break

            # Adjust the interval as needed
            await asyncio.sleep(HEARTBEAT_INTERVAL)

    async def on_disconnect(self, websocket: WebSocket, close_code: int):
        logger.info(f"connection closed {websocket.client_state} {close_code}")
        self.clients.remove(websocket)
        pass
