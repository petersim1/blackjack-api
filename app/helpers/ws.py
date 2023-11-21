from typing import TYPE_CHECKING, Tuple, List
from app.pydantic_types import MessageSend, RulesI, DeckI, CardDesctructured
from typing import Iterator

if TYPE_CHECKING:
    from app.routes.ws import Consumer

def handle_init(data: dict):
    """ will throw an error, which we catch in the fct that calls this, if pydantic validation error is thrown."""

    rules = data.get("rules", RulesI().model_dump())
    deck = data.get("deck", DeckI().model_dump())
    rules = RulesI(**rules)
    deck = DeckI(**deck)
    game_hyperparams = deck.model_dump()
    game_hyperparams["rules"] = rules.model_dump()
    return game_hyperparams


def get_game_info(obj: "Consumer") -> Tuple[
    List[CardDesctructured],
    List[CardDesctructured],
    float,
    int,
    int,
    List[str]
]:
    house_cards = [[card.card,card.suit] for card in obj.game.house.cards[0].cards]
    player_cards = [[card.card,card.suit] for card in obj.game.players[0].cards[0].cards]
    c_remaining = len(obj.game.shoe.cards) / (52 * obj.game.n_decks)
    house_total = None
    if obj.game.house_played:
        house_total = obj.game.house.cards[0].total
    player_total = obj.game.players[0].cards[0].total
    policy = obj.game.players[0].get_valid_moves()

    return house_cards, player_cards, c_remaining, house_total, player_total, policy


def gather_responses(obj: "Consumer", data: dict, code: str) -> Iterator[MessageSend]:
    '''
    currently just assume single player, single hand.
        code : start, step
        wager: int (only applicable for code=='start')
        move: hit, stay, double (only applicable for code=='step')
    '''
    wager = float(data.get("wager", 1))
    move = data.get("move", "")
    round_over = False
    hand_result = None
    match code:
        case "start":
            obj.game.init_round([wager])
            obj.game.deal_init()
        case "step":
            obj.game.step_player(0, move)

    h_c, p_c, c_rem, h_t, p_t, policy = get_game_info(obj)
    h_c[-1] = ["Hidden", "Hidden"] # always hide here, following logic excludes this.

    yield MessageSend(
        cards_remaining=c_rem,
        round_over=round_over,
        total_profit=obj.balance,
        count=(obj.game.count, obj.game.true_count),
        hand_result=hand_result,
        player_total=p_t,
        player_cards=p_c,
        house_total=h_t,
        house_cards=h_c,
        policy=policy
    )

    if obj.game.players[0].is_done():
        obj.game.step_house(only_reveal_card=True)
        h_c, p_c, c_rem, h_t, p_t, policy = get_game_info(obj)
        while not obj.game.house_done():
            yield MessageSend(
                cards_remaining=c_rem,
                total_profit=obj.balance,
                count=(obj.game.count, obj.game.true_count),
                player_total=p_t,
                player_cards=p_c,
                house_total=h_t,
                house_cards=h_c,
            )
            obj.game.step_house()
            h_c, p_c, c_rem, h_t, p_t, policy = get_game_info(obj)

        texts, winnings = obj.game.get_results()
        obj.balance += winnings[0][0]

        yield MessageSend(
            cards_remaining=c_rem,
            round_over=True,
            total_profit=obj.balance,
            count=(obj.game.count, obj.game.true_count),
            hand_result=(texts[0][0], winnings[0][0]),
            player_total=p_t,
            player_cards=p_c,
            house_total=h_t,
            house_cards=h_c,
        )
    
            