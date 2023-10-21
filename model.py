from enum import Enum
from dataclasses import dataclass


class Color(Enum):
    Grey = 'grey'
    Green = 'green'
    Yellow = 'yellow'


@dataclass(frozen=True)
class Cell:
    letter: str
    color: Color
    position: int = None
