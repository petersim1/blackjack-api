from typing import TYPE_CHECKING, Iterator, List, Tuple

from app.pydantic_types import CardDesctructured, DeckI, MessageSend, RulesI

if TYPE_CHECKING:
    from app.routes.ws import Consumer


def handle_init(data: dict):
    """
    will throw an error, which we catch in the fct that
    calls this, if pydantic validation error is thrown.
    """

    rules = data.get("rules", RulesI().model_dump())
    deck = data.get("deck", DeckI().model_dump())
    rules = RulesI(**rules)
    deck = DeckI(**deck)
    game_hyperparams = deck.model_dump()
    game_hyperparams["rules"] = rules.model_dump()
    return game_hyperparams


def get_game_info(
    obj: "Consumer",
) -> Tuple[
    List[List[CardDesctructured]],
    List[List[CardDesctructured]],
    float,
    int,
    List[int],
    List[List[str]],
    int,
]:
    """
    Adopted this to now allow for multiple hands per player (solely due to split)
    where there are mixed types, explicitly force a tuple
    (makes typing prettier + more obvious)
    """
    house_cards = [
        tuple([card.card, card.suit]) for card in obj.game.house.cards[0].cards
    ]
    player_cards = [
        [tuple([card.card, card.suit]) for card in hand.cards]
        for hand in obj.game.players[0].cards
    ]
    c_remaining = len(obj.game.shoe.cards) / (52 * obj.game.n_decks)

    if obj.game.house_played:
        house_total = obj.game.house.cards[0].total
    else:
        house_total = None  # don't want to show this to client
        house_cards[-1] = [
            "Hidden",
            "Hidden",
        ]  # always hide here if house hasn't played.

    player_total = [cards.total for cards in obj.game.players[0].cards]
    policy = obj.game.players[
        0
    ].get_valid_moves()  # don't need a list, as this is only performed on current hand.
    cur_hand = obj.game.players[0].i_hand

    return (
        house_cards,
        player_cards,
        c_remaining,
        house_total,
        player_total,
        policy,
        cur_hand,
    )


def gather_responses(obj: "Consumer", data: dict, code: str) -> Iterator[MessageSend]:
    """
    currently just assume single player, single hand.
        code : start, step
        wager: int (only applicable for code=='start')
        move: hit, stay, double (only applicable for code=='step')
    """
    wager = float(data.get("wager", 1))
    move = data.get("move", "")
    round_over = False
    match code:
        case "start":
            obj.game.init_round([wager])
            obj.game.deal_init()
        case "step":
            obj.game.step_player(0, move)

    h_c, p_c, c_rem, h_t, p_t, policy, cur_hand = get_game_info(obj)

    yield MessageSend(
        cards_remaining=c_rem,
        round_over=round_over,
        total_profit=obj.balance,
        count=tuple([obj.game.count, obj.game.true_count]),
        player_total=p_t,
        player_cards=p_c,
        house_cards=h_c,
        policy=policy,
        current_hand=cur_hand,
    )

    if obj.game.players[0].is_done():
        obj.game.step_house(only_reveal_card=True)  # marks house_played as True
        h_c, p_c, c_rem, h_t, p_t, policy, cur_hand = get_game_info(obj)
        while not obj.game.house_done():
            yield MessageSend(
                cards_remaining=c_rem,
                total_profit=obj.balance,
                count=tuple([obj.game.count, obj.game.true_count]),
                player_total=p_t,
                player_cards=p_c,
                house_total=h_t,
                house_cards=h_c,
                current_hand=cur_hand,
            )
            obj.game.step_house()
            h_c, p_c, c_rem, h_t, p_t, policy, cur_hand = get_game_info(obj)

        texts, winnings = obj.game.get_results()
        obj.balance += sum(winnings[0])

        yield MessageSend(
            cards_remaining=c_rem,
            round_over=True,
            total_profit=obj.balance,
            count=tuple([obj.game.count, obj.game.true_count]),
            hand_result_text=texts[
                0
            ],  # only pull for first player (which will include all their hands)
            hand_result_profit=winnings[
                0
            ],  # only pull for first player (which will include all their hands)
            player_total=p_t,
            player_cards=p_c,
            house_total=h_t,
            house_cards=h_c,
            current_hand=cur_hand,
        )
