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
    deal_house = False
    deal_player = False
    round_over = False
    match code:
        case "start":
            obj.game.init_round([wager])
            obj.game.deal_init()
            text = "Game Started!"
            deal_house = True
            deal_player = True
        case "step":
            obj.game.step_player(0, move)
            deal_player = move != "stay"
        case "end":
            return

    house_cards = [[card.card,card.suit] for card in obj.game.house.cards[0].cards]
    player_cards = [[card.card,card.suit] for card in obj.game.players[0].cards[0].cards]
    c_remaining = len(obj.game.shoe.cards) / (52 * obj.game.n_decks)
    player_total = obj.game.players[0].cards[0].total
    policy = obj.game.players[0].get_valid_moves()

    if not obj.game.house_played:
        if not obj.game.house_blackjack:
            house_cards[-1] = ["Hidden", "Hidden"]
        else:
            text = "House Blackjack :("
            policy = []
            round_over = True
            if player_total == 21:
                text = "Push"
            else:
                obj.balance -= 1
    
    yield MessageSend(
        cards_remaining=c_remaining,
        round_over=round_over,
        deal_house=deal_house,
        deal_player=deal_player,
        profit=obj.balance,
        count=(obj.game.count, obj.game.true_count),
        text=text,
        player_total=player_total,
        player_cards=player_cards,
        house_cards=house_cards,
        policy=policy
    )

    if obj.game.players[0].is_done():
        obj.game.step_house()
        house_cards = [[card.card,card.suit] for card in obj.game.house.cards[0].cards]
        player_cards = [[card.card,card.suit] for card in obj.game.players[0].cards[0].cards]
        player_total = obj.game.players[0].cards[0].total
        c_remaining = len(obj.game.shoe.cards) / (52 * obj.game.n_decks)

        for i in range(2,len(house_cards)+1):
            yield MessageSend(
                cards_remaining=c_remaining,
                round_over=False,
                deal_house=True,
                deal_player=False,
                profit=obj.balance,
                count=(obj.game.count, obj.game.true_count),
                text=text,
                player_total=player_total,
                player_cards=player_cards,
                house_cards=house_cards[:i],
                policy=policy
            )


        texts, winnings = obj.game.get_results()
        obj.balance += winnings[0][0]

        yield MessageSend(
            cards_remaining=c_remaining,
            round_over=True,
            deal_house=False,
            deal_player=False,
            profit=obj.balance,
            count=(obj.game.count, obj.game.true_count),
            text=texts[0][0],
            player_total=player_total,
            player_cards=player_cards,
            house_cards=house_cards,
        )
    
            