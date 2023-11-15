from starlette.websockets import WebSocket
from starlette.exceptions import WebSocketException
from starlette.endpoints import WebSocketEndpoint
import random
import asyncio
import logging
import json
from typing import List
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
    balance = 100

    async def on_connect(self, websocket: WebSocket):
        logger.info(f"connection started {websocket.client.port}")
        await websocket.accept()
        self.game = Game(**game_hyperparams)
        self.clients.add(websocket)
        message = f"You have ${self.balance}"
        message = MessageSend(
            balance=self.balance,
            count=self.game.count,
            true_count=self.game.true_count,
            player_total=0,
            text="Welcome, start playing",
            policy=["hit", "stand", "double"]
        )
        await websocket.send_json(message.model_dump())

    async def on_receive(self, websocket: WebSocket, data: object):
        responses = gather_responses(self.game, self.balance, json.loads(data))
        logger.info(self.balance)
        await self.send_sequential_messages(responses, websocket)
        
        match data:
            case 'ping':
                if self.task is not None:
                    await websocket.send_text('background task is already running')
                    return

                await websocket.send_text('start background task')
                self.task = asyncio.create_task(self.simulate_long_task(websocket))
            case 'get':
                await websocket.send_json({"name": "pete", "age": 21})
            case 'update':
                self.to_update = random.random()
                self.broadcast(f'updated to {self.to_update}', websocket)
            case 'close':
                message = {"count": 0, "text": "closing connection", "policy": []}
                await websocket.send_text(json.dumps(message))
                await websocket.close()

    async def send_sequential_messages(self, messages: List[MessageSend], websocket: WebSocket) -> None:
        for message in messages:
            await websocket.send_json(message.model_dump())
            await asyncio.sleep(0.5)


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