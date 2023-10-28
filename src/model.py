from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Self

from dataclasses_json import dataclass_json

import utils


class Color(IntEnum):
    GREY = 1
    YELLOW = 2
    GREEN = 3


@dataclass(frozen=True)
class Cell:
    letter: str
    color: Color
    position: int = None


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
