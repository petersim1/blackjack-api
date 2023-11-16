from typing import TYPE_CHECKING
from app.pydantic_types import MessageSend
from typing import Iterator

if TYPE_CHECKING:
    from app.routes.ws import Consumer

def gather_responses(obj: "Consumer", data: object) -> Iterator[MessageSend]:
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
            obj.game.init_round([wager])
            obj.game.deal_init()
            text = "Game Started!"
        case "step":
            obj.game.step_player(0, move)
        case "end":
            return

    house_cards = [card.card for card in obj.game.house.cards[0].cards]
    player_cards = [card.card for card in obj.game.players[0].cards[0].cards]
    player_total = obj.game.players[0].cards[0].total
    policy = obj.game.players[0].get_valid_moves()

    if not obj.game.house_played:
        if not obj.game.house_blackjack:
            house_cards[-1] = "Hidden"
        else:
            text = "House Blackjack :("
            policy = []
    
    yield MessageSend(
        balance=obj.balance,
        count=obj.game.count,
        true_count=obj.game.true_count,
        text=text,
        player_total=player_total,
        player_cards=player_cards,
        house_cards=house_cards,
        policy=policy
    )

    if obj.game.players[0].is_done():
        obj.game.step_house()
        house_cards = [card.card for card in obj.game.house.cards[0].cards]
        player_cards = [card.card for card in obj.game.players[0].cards[0].cards]
        player_total = obj.game.players[0].cards[0].total

        for i in range(2,len(house_cards)+1):
            yield MessageSend(
                balance=obj.balance,
                count=obj.game.count,
                true_count=obj.game.true_count,
                text=text,
                player_total=player_total,
                player_cards=player_cards,
                house_cards=house_cards[:i],
                policy=policy
            )


        texts, winnings = obj.game.get_results()
        obj.balance += winnings[0][0]

        yield MessageSend(
            balance=obj.balance,
            count=obj.game.count,
            true_count=obj.game.true_count,
            text=texts[0][0] + " " + str(winnings[0][0]),
            player_total=player_total,
            player_cards=player_cards,
            house_cards=house_cards,
        )
    
            