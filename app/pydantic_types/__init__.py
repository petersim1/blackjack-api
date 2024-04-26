from typing import List, Optional, Tuple, Union

from pydantic import BaseModel, Field

CardDesctructured = Tuple[Union[str, int], str]


class MessageSend(BaseModel):
    ready: bool = Field(
        default=True, description="whether game was initialized and can be dealt"
    )
    round_over: bool = Field(default=False, description="whether the round is over")
    hand_result_text: Optional[List[str]] = Field(
        default=None, description="result of the hand (text, profit)"
    )
    hand_result_profit: Optional[List[float]] = Field(
        default=None, description="result of the hand (text, profit)"
    )
    total_profit: float = Field(default=0.0, description="running profit per session")
    count: Tuple[int, float] = Field(
        default=(0, 0.0), description="[running count, true count]"
    )
    cards_remaining: float = Field(
        default=1.0, description="percent of cards remaining in shoe"
    )
    player_total: Optional[List[int]] = Field(
        default=None, description="total of player's hands"
    )
    player_cards: List[List[CardDesctructured]] = Field(
        default_factory=lambda: [[]], description="list of cards for player"
    )
    current_hand: int = Field(default=0, description="current index of player's hand")
    house_total: Optional[int] = Field(
        default=None, description="total of house's current hand"
    )
    house_cards: List[CardDesctructured] = Field(
        default_factory=lambda: [], description="list of cards for house"
    )
    policy: List[str] = Field(
        default_factory=lambda: [], description="current policy for player's hand"
    )
    model: Optional[Tuple[int, int, int]] = Field(
        default=None, description="tuple required for RL model input"
    )
