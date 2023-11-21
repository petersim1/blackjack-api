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
    hand_result_text: Optional[List[str]] = Field(
        default=None,
        description="result of the hand (text, profit)"
    )
    hand_result_profit: Optional[List[float]] = Field(
        default=None,
        description="result of the hand (text, profit)"
    )
    total_profit: float = Field(
        default=0.0,
        description="running profit per session"
    )
    count: Tuple[int, float] = Field(
        default=(0, 0.0),
        description="[running count, true count]"
    )
    cards_remaining: float = Field(
        default=1.0,
        description="percent of cards remaining in shoe"
    )
    player_total: Optional[List[int]] = Field(
        default=None,
        description="total of player's hands"
    )
    player_cards: List[List[CardDesctructured]] = Field(
        default_factory=lambda : [[]],
        description="list of cards for player"
    )
    current_hand: int = Field(
        default=0,
        description="current index of player's hand"
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
        description="current policy for player's hand"
    )
