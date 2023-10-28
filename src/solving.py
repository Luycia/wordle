import math
import itertools
from typing import List, Set, Tuple, Final
from model import Color, Cell
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor


class Solver:
    def __init__(self, words: List[str],
                 start_recomendations: List[Tuple[str, float]] = None) -> None:
        self.words: Final[List[str]] = words
        self.filtered: List[str] = words
        self.possible_patterns: List[Tuple[Color]] = list(itertools.product(
            [Color.GREY, Color.GREEN, Color.YELLOW], repeat=5))

        if start_recomendations:
            self.start_recomendations = start_recomendations
        else:
            self.start_recomendations = self.get_best_guess()

    def reset(self):
        self.filtered = self.words

    def analyse_pattern(self, word: str, pattern: List[Color]) -> Set[Cell]:
        knowledge = set()
        for pos, color in enumerate(pattern):
            if color == Color.GREY:
                knowledge.add(Cell(word[pos], Color.GREY))
            else:
                knowledge.add(Cell(word[pos], color, pos))

        return knowledge

    def filter_words_without_letter(self, letter, words):
        return [word for word in words if letter not in word]

    def filter_words_position(self, letter, position, words):
        return [word for word in words if word[position] == letter]

    def filter_words_not_position(self, letter, position, words):
        return [word for word in words if letter in word and word[position] != letter]

    def filter_words(self, word: str, pattern: List[Color]):
        filtered = self.filtered
        pattern = self.analyse_pattern(word, pattern)
        for cell in pattern:
            if cell.color == Color.GREY:
                filtered = self.filter_words_without_letter(
                    cell.letter, filtered)
            elif cell.color == Color.GREEN:
                filtered = self.filter_words_position(
                    cell.letter, cell.position, filtered)
            else:
                filtered = self.filter_words_not_position(
                    cell.letter, cell.position, filtered)
        return filtered

    def feed(self, word: str, pattern: List[Color]):
        self.filtered = self.filter_words(word, pattern)

    def entropy(self, probabilities: List[float]) -> float:
        return sum([p * math.log(1/p, 2) for p in probabilities])

    def expected_information(self, word: str, verbose: bool = False) -> float:
        if len(self.filtered) == 0:
            # No uncertainty
            return 0
        probabilities = []
        for pattern in self.possible_patterns:
            filtered = self.filter_words(word, pattern)
            probability = len(filtered) / len(self.filtered)
            if probability > 0:
                probabilities.append(probability)
            if verbose:
                print(
                    f"{pattern}: top={filtered[:5]} len={len(filtered)} prop={probability:.4f}")

        return self.entropy(probabilities)

    def get_best_guess(self, n_best: int = None) -> List[Tuple[str, float]]:
        word_information = []
        with ProcessPoolExecutor() as pool:
            for entropy, word in tqdm(zip(pool.map(self.expected_information,
                                                   self.filtered),
                                          self.filtered),
                                      total=len(self.filtered)):
                word_information.append((word, entropy))

        word_information = sorted(
            word_information, key=lambda x: x[1], reverse=True)

        if n_best:
            word_information = word_information[:n_best]
        return word_information

    def get_words_entropy(self) -> float:
        return -math.log(1/len(self.filtered), 2) if len(self.filtered) > 0 else 0
