from starlette.websockets import WebSocket
from starlette.exceptions import WebSocketException
from starlette.endpoints import WebSocketEndpoint
import random
import asyncio
import logging
import json
from typing import Iterator
from app.modules.game import Game
from app.helpers.ws import gather_responses
from app.pydantic_types import MessageSend

logger = logging.getLogger(__name__)

rules = {
    "dealer_hit_soft17": True,
    "push_dealer22": False,
    "double_after_split": True,
    "hit_after_split_aces": False,
    "reduced_blackjack_payout": False,
    "allow_surrender": True,
}

game_hyperparams = {
    "shrink_deck": True,
    "n_decks": 6,
    "ratio_penetrate": 2/3,
    "rules": rules
}


class Consumer(WebSocketEndpoint):
    to_update = 'text'
    task = None
    clients = set()
    game = None
    balance = 0

    async def on_connect(self, websocket: WebSocket):
        logger.info(f"connection started {websocket.client.port}")
        await websocket.accept()
        self.game = Game(**game_hyperparams)
        self.clients.add(websocket)
        print(self.clients)

        message = MessageSend(
            cards_remaining=1,
            round_over=True,
            deal_house=False,
            deal_player=False,
            profit=self.balance,
            count=(self.game.count, self.game.true_count),
            player_total=0,
            text="Welcome, start playing",
            policy=[]
        )
        await websocket.send_json(message.model_dump())

    async def on_receive(self, websocket: WebSocket, data: object):
        if self.task is not None:
            # message = MessageSend(
            #     balance=self.balance,
            #     count=self.game.count,
            #     true_count=self.game.true_count,
            #     player_total=0,
            #     text="State is updating, hold on.",
            #     policy=["hit", "stand", "double"]
            # )
            # await websocket.send_json(message.model_dump())
            return
        data = json.loads(data)
        code = data.get("code", "reset")
        match code:
            case "start" | "step" | "end":
                responses = gather_responses(self, data)
                self.task = asyncio.create_task(
                    self.send_sequential_messages(responses, websocket)
                )
            case 'ping':
                if self.task is not None:
                    await websocket.send_text('background task is already running')
                    return

                await websocket.send_text('start background task')
                self.task = asyncio.create_task(self.simulate_long_task(websocket))
            case 'update':
                self.to_update = random.random()
                self.broadcast(f'updated to {self.to_update}', websocket)
            case 'close':
                message = {"count": 0, "text": "closing connection", "policy": []}
                await websocket.send_text(json.dumps(message))
                await websocket.close()

    async def send_sequential_messages(self, messages: Iterator[MessageSend], websocket: WebSocket) -> None:
        message = next(messages, None)
        while message is not None:
            # this logic only places a timeout between messages,
            # not just after each message. Helps with backend throttling issues.
            await websocket.send_json(message.model_dump())
            message = next(messages, None)
            if message is not None:
                await asyncio.sleep(1)
        self.task = None


    async def simulate_long_task(self, websocket: WebSocket):
        await websocket.send_text('start long process')
        await asyncio.sleep(5)
        await websocket.send_text('finish long process')
        self.task = None

    def broadcast(self, message, cur_ws):
        for client in self.clients:
            try:
                m = message
                if cur_ws != client:
                    m += " from other client"
                asyncio.create_task(client.send_text(m))
            except WebSocketException:
                # in case that a client closed while something was being broadcasted.
                pass

    async def on_disconnect(self, websocket, close_code):
        logger.info(f"connection closed {websocket.client_state} {close_code}")
        self.clients.remove(websocket)
        pass