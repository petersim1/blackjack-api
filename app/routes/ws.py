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


async def test_me(websocket: WebSocket):
    await asyncio.sleep(5)
    print(websocket.application_state.name)
    print("k")


class Consumer(WebSocketEndpoint):
    task = None
    clients = set()
    game = None
    balance = 0
    heartbeat_waiting = False

    async def on_connect(self, websocket: WebSocket):
        logger.info(f"connection started {websocket.client.port}")
        await websocket.accept()

        self.clients.add(websocket)
        message = MessageSend(
            ready=False,
            round_over=True,
        )
        asyncio.create_task(self.heartbeat(websocket))
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

            case "pong":
                # Don't know what this id is actually based off of.
                client_id = websocket.scope.get("client", ["", ""])[1]
                logging.info(f"pong received from client {client_id}")
                self.heartbeat_waiting = False

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
        """
        On the client, I actually observe the following flow:
        - WS 1 is opened
        - WS 1 immediately closes
        - WS 2 immediately opens
        So, since this logic is placed within the .on_connect() fct,
        we might actually get an invalidated websocket before the timeout occurs. Fix
        for this after the initial .sleep() interval.
        """
        while True:
            # Time in between pings
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            try:
                # Send a ping message to the client
                if (websocket.client_state.name == "DISCONNECTED"):
                    # depending on the client, this might get hit EXACTLY once
                    # due to initial connection issue.
                    return
                client_id = websocket.scope.get("client", ["", ""])[1]
                logging.info(f"ping sent to client {client_id}")
                await websocket.send_json({"type": "ping"})
                self.heartbeat_waiting = True

                # time allotted for the client to respond properly.
                await asyncio.sleep(3)
                if self.heartbeat_waiting:
                    print("FAILURE TO SEND PONG")
                    raise WebSocketException(code=1001)
            except WebSocketException:
                await websocket.close()
                break

    async def on_disconnect(self, websocket: WebSocket, close_code: int):
        logger.info(f"connection closed {websocket.client_state} {close_code}")
        self.clients.remove(websocket)
        pass
