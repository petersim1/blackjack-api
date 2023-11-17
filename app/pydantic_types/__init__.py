from typing import List, Dict, Optional, Union, Tuple
from pydantic import BaseModel
from app.modules.cards import Card

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
    round_over: bool
    profit: float
    count: Tuple[int, float]
    text: str
    player_total: int
    house_cards: List[Tuple[Union[str, int], str]] = []
    player_cards: List[Tuple[Union[str, int], str]] = []
    policy: List[str] = []

QMovesI = Dict[str, float]

ConditionalActionSpace = List[List[List[str]]]