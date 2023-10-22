from enum import IntEnum
from dataclasses import dataclass


class Color(IntEnum):
    Grey = 1
    Yellow = 2
    Green = 3


@dataclass(frozen=True)
class Cell:
    letter: str
    color: Color
    position: int = None


class Difficulty(IntEnum):
    Easy = 1
    Medium = 2
    Hard = 3


class SolverHelp(IntEnum):
    No = 1
    Tips = 2
    Yes = 3


@dataclass
class GameConfig:
    difficulty: Difficulty = Difficulty.Easy
    solver_help: SolverHelp = SolverHelp.No
