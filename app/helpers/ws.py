from app.modules.game import Game
from app.modules.cards import Card, SuitEnum
from app.pydantic_types import MessageSend
from typing import Iterator

def gather_responses(game: Game, balance: float, data: object) -> Iterator[MessageSend]:
    '''
    currently just assume single player, single hand.
        code : start, step, end
        wager: int
        move: null, hit, stay, double
    '''

    code = data.get("code", "reset")
    wager = int(data.get("wager", 1))
    move = data.get("move", "")
    text = ""
    match code:
        case "start":
            game.init_round([wager])
            game.deal_init()
            text = "Game Started!"
        case "step":
            game.step_player(0, move)
        case "end":
            message = MessageSend(
                balance=balance,
                count=game.count,
                true_count=game.true_count,
                player_total=0,
                text="Round Ended"
            )
            yield message
            return
        case _:
            yield MessageSend(text="error")
            return

    house_cards = [card.card for card in game.house.cards[0].cards]
    player_cards = [card.card for card in game.players[0].cards[0].cards]
    player_total = game.players[0].cards[0].total
    policy = game.players[0].get_valid_moves()

    if not game.house_played:
        if not game.house_blackjack:
            house_cards[-1] = "Hidden"
        else:
            text = "House Blackjack :("
            policy = []
    
    yield MessageSend(
        balance=balance,
        count=game.count,
        true_count=game.true_count,
        text=text,
        player_total=player_total,
        player_cards=player_cards,
        house_cards=house_cards,
        policy=policy
    )

    if game.players[0].is_done():
        game.step_house()
        house_cards = [card.card for card in game.house.cards[0].cards]
        player_cards = [card.card for card in game.players[0].cards[0].cards]
        player_total = game.players[0].cards[0].total

        texts, winnings = game.get_results()
        balance += winnings[0][0]

        yield MessageSend(
            balance=balance,
            count=game.count,
            true_count=game.true_count,
            text=texts[0][0],
            player_total=player_total,
            player_cards=player_cards,
            house_cards=house_cards,
        )
    
            