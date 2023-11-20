from typing import List, Dict, Optional, Union, Tuple
from pydantic import BaseModel, Field

class StateActionPair(BaseModel):
    player_show: int
    house_show: int
    useable_ace: bool
    can_split: bool
    move: str

class ReplayBuffer(BaseModel):
    obs: tuple
    action_space: List[str]
    move: str
    reward: float
    done: int
    obs_next: Optional[tuple]
    action_space_next: Optional[List[str]]

class RulesI(BaseModel):
    dealer_hit_soft17: bool=True
    push_dealer22: bool=False
    double_after_split: bool=True
    hit_after_split_aces: bool=False
    reduced_blackjack_payout: bool=False
    allow_surrender: bool=True

class MessageSend(BaseModel):
    ready: bool = Field(
        default=True,
        description="whether game was initialized and can be dealt"
    )
    round_over: bool = Field(
        default=False,
        description="whether the round is over"
    )
    hand_result: Tuple[str, int] = Field(
        description="result of the hand (text, profit)"
    )
    round_profit: float = Field(
        default=0,
        description="result of the round (all hands)"
    )
    total_profit: float = Field(
        default=0.0,
        description="running profit per session"
    )
    count: Tuple[int, float] = Field(
        default_factory=lambda : [0, 0.0],
        description="[running count, true count]"
    )
    cards_remaining: float = Field(
        default=1.0,
        description="percent of cards remaining in shoe"
    )
    player_total: int = Field(
        default=0,
        description="total of player's current hand"
    )
    player_cards: List[Tuple[Union[str, int], str]] = Field(
        default_factory=lambda : [],
        description="list of cards for player"
    )
    house_total: int = Field(
        default=0,
        description="total of house's current hand"
    )
    house_cards: List[Tuple[Union[str, int], str]] = Field(
        default_factory=lambda : [],
        description="list of cards for house"
    )
    policy: List[str] = Field(
        default_factory=lambda : [],
        description="current policy for player"
    )

QMovesI = Dict[str, float]

ConditionalActionSpace = List[List[List[str]]]