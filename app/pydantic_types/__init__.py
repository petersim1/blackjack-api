from typing import List, Dict, Optional, Union, Tuple
from pydantic import BaseModel, Field

class RulesI(BaseModel):
    dealer_hit_soft17: bool=False
    push_dealer22: bool=False
    double_after_split: bool=True
    hit_after_split_aces: bool=False
    reduced_blackjack_payout: bool=False
    allow_surrender: bool=True

class DeckI(BaseModel):
    shrink_deck: bool=True
    n_decks: int=6
    ratio_penetrate: float=4/6

class GameParamsI(DeckI):
    rules: RulesI

CardDesctructured = Tuple[Union[str, int], str]

class MessageSend(BaseModel):
    ready: bool = Field(
        default=True,
        description="whether game was initialized and can be dealt"
    )
    round_over: bool = Field(
        default=False,
        description="whether the round is over"
    )
    hand_result: Optional[Tuple[str, float]] = Field(
        default=None,
        description="result of the hand (text, profit)"
    )
    round_profit: Optional[float] = Field(
        default=None,
        description="result of the round (all hands)"
    )
    total_profit: float = Field(
        default=0.0,
        description="running profit per session"
    )
    count: List[Union[int, float]] = Field(
        default_factory=lambda : [0, 0.0],
        description="[running count, true count]"
    )
    cards_remaining: float = Field(
        default=1.0,
        description="percent of cards remaining in shoe"
    )
    player_total: Optional[int] = Field(
        default=None,
        description="total of player's current hand"
    )
    player_cards: List[CardDesctructured] = Field(
        default_factory=lambda : [],
        description="list of cards for player"
    )
    house_total: Optional[int] = Field(
        default=None,
        description="total of house's current hand"
    )
    house_cards: List[CardDesctructured] = Field(
        default_factory=lambda : [],
        description="list of cards for house"
    )
    policy: List[str] = Field(
        default_factory=lambda : [],
        description="current policy for player"
    )
