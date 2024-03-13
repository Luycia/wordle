import operator
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import List, Self

from dataclasses_json import dataclass_json

import utils


class Color(IntEnum):
    GREY = 1
    YELLOW = 2
    GREEN = 3


class LetterRule:

    def __init__(self, letter: str, color: Color, position: int = None) -> None:
        self.letter = letter
        self.colors = [color]
        if color == Color.GREY:
            self.frequency = 0
            self.operator = operator.eq
        else:
            self.frequency = 1
            self.operator = operator.ge

        self.positions = [
            position] if position is not None and color == Color.GREEN else []
        self.not_positions = [
            position] if position is not None and color == Color.YELLOW else []

    def add_color(self, color: Color, position: int):
        self.colors.append(color)
        if color == Color.GREY:
            self.operator = operator.eq
        elif color == Color.YELLOW:
            self.frequency += 1
            self.not_positions.append(position)
        elif color == Color.GREEN:
            self.frequency += 1
            self.positions.append(position)

    def __str__(self) -> str:
        return self.__repr__() + f" colors={self.colors}"

    def __repr__(self) -> str:
        return f"{self.letter} {self.operator} {self.frequency} positions={self.positions} not_positions={self.not_positions}"


class Difficulty(IntEnum):
    EASY = 1
    MEDIUM = 2
    HARD = 3


class SolverHelp(IntEnum):
    NEVER = 1
    TIPS = 2
    ALWAYS = 3


class Language(Enum):
    EN = 1
    DE = 2


@dataclass_json
@dataclass
class GameConfig:
    language: Language = Language.EN
    difficulty: Difficulty = Difficulty.MEDIUM
    solver_help: SolverHelp = SolverHelp.TIPS

    def to_file(self, path: str) -> None:
        utils.write_jsons(path, self.to_json())

    def from_file(path: str) -> Self:
        try:
            return GameConfig.from_json(utils.read_file(path))
        except:
            return GameConfig()
