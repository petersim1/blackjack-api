from starlette.websockets import WebSocket
from starlette.exceptions import WebSocketException
from starlette.endpoints import WebSocketEndpoint
import random
import asyncio
import logging
import json
from app.modules.game import Game

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
        message = json.dumps({
            "count": self.game.count,
            "text": message,
            "policy": ["stay", "hit", "double"]
        })
        await websocket.send_text(message)

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

    async def on_receive(self, websocket: WebSocket, data: str):
        logger.info(data)
        match data:
            case "start_game":
                self.game.init_round([1])
                self.game.deal_init()

                house_card = str(self.game.house.cards[0].cards[0].card)
                player_cards = ", ".join([str(card.card) for card in self.game.players[0].cards[0].cards])
                player_total = str(self.game.players[0].cards[0].total)
                message = {
                    "count": self.game.count,
                    "text": f"House: {house_card} ---- Player: {player_cards} --- {player_total}",
                    "policy": ["stay", "hit", "double"]
                }
                await websocket.send_text(json.dumps(message))

                if (self.game.players[0].cards[0].total == 21):
                    if not self.game.house_blackjack:
                        message = {
                            "count": self.game.count,
                            "text": "Blackjack!",
                            "policy": []
                        }
                        await websocket.send_text(json.dumps(message))
                        self.balance += 1.5
                        message = {"count": self.game.count,"text": f"You have ${self.balance}", "policy": []}
                        await websocket.send_text(json.dumps(message))
                    
            case "hit":
                self.game.step_player(0, "hit")
                house_card = str(self.game.house.cards[0].cards[0].card)
                player_cards = ", ".join([str(card.card) for card in self.game.players[0].cards[0].cards])
                player_total = str(self.game.players[0].cards[0].total)
                message = {
                    "count": self.game.count,
                    "text": f"House: {house_card} ---- Player: {player_cards} --- {player_total}",
                    "policy": self.game.players[0].get_valid_moves()
                }
                await websocket.send_text(json.dumps(message))
                if self.game.players[0].cards[0].total >= 21:
                    self.game.step_house()
                    texts, winnings = self.game.get_results()
                    self.balance += winnings[0][0]
                    message = {
                        "count": self.game.count,
                        "text": f"Result: {texts[0][0]} --- Round Reward: {winnings[0][0]}",
                        "policy": []
                    }
                    await websocket.send_text(json.dumps(message))
                    message = {"count": self.game.count,"text": f"You have ${self.balance}", "policy": []}
                    await websocket.send_text(json.dumps(message))
            case "stay":
                self.game.step_player(0, "stay")
                self.game.step_house()
                house_cards = ", ".join([str(card.card) for card in self.game.house.cards[0].cards])
                player_cards = ", ".join([str(card.card) for card in self.game.players[0].cards[0].cards])
                message = {
                    "count": self.game.count,
                    "text": f"House: {house_cards} ---- Player: {player_cards}",
                    "policy": []
                }
                await websocket.send_text(json.dumps(message))

                texts, winnings = self.game.get_results()
                self.balance += winnings[0][0]
                message = {
                    "count": self.game.count,
                    "text": f"Result: {texts[0][0]} --- Round Reward: {winnings[0][0]}",
                    "policy": []
                }
                await websocket.send_text(json.dumps(message))
                message = {"count": self.game.count,"text": f"You have ${self.balance}", "policy": []}
                await websocket.send_text(json.dumps(message))
            case "double":
                self.game.step_player(0, "double")
                self.game.step_house()
                house_cards = ", ".join([str(card.card) for card in self.game.house.cards[0].cards])
                player_cards = ", ".join([str(card.card) for card in self.game.players[0].cards[0].cards])
                player_total = str(self.game.players[0].cards[0].total)
                await websocket.send_text(f"House: {house_cards} ---- Player: {player_cards} --- {player_total}")

                texts, winnings = self.game.get_results()
                self.balance += winnings[0][0]
                await websocket.send_text(f"Result: {texts[0][0]} --- Round Reward: {winnings[0][0]}")
                await websocket.send_text(f"You have ${self.balance}")
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
            case _:
                self.broadcast(f'Server received {data} from client', websocket)


    async def simulate_long_task(self, websocket: WebSocket):
        await websocket.send_text('start long process')
        await asyncio.sleep(5)
        await websocket.send_text('finish long process')
        self.task = None

    async def on_disconnect(self, websocket, close_code):
        logger.info(f"connection closed {websocket.client_state} {close_code}")
        self.clients.remove(websocket)
        pass