import itertools
import math
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List, Tuple

from tqdm import tqdm

from model import Color, LetterRule


class Solver:
    def __init__(self, words: List[str],
                 start_recomendations: List[Tuple[str, float]] = None) -> None:
        self.words_letter_count = {word: Counter(word) for word in words}
        self.filtered: List[str] = words
        self.possible_patterns: List[Tuple[Color]] = list(itertools.product(
            [Color.GREY, Color.GREEN, Color.YELLOW], repeat=5))

        if start_recomendations:
            self.start_recomendations = start_recomendations
        else:
            self.start_recomendations = self.get_best_guess()

    def reset(self) -> None:
        self.filtered = list(self.words_letter_count.keys())

    def analyse_pattern(self, word: str, pattern: List[Color]) -> List[LetterRule]:
        rules: Dict[str, LetterRule] = {}
        for pos, color in enumerate(pattern):
            letter = word[pos]
            if letter in rules:
                # After yellow color for a letter a grey color cannot follow
                # e.g. for the word 'speed' grey cannot be followed after grey
                # since first grey means, there is no letter 'e' in the secret word
                if color == Color.YELLOW and Color.GREY in rules[letter].colors:
                    return None
                rules[letter].add_color(color, pos)
            else:
                rules[letter] = LetterRule(letter, color, pos)

        return list(rules.values())

    def filter_words_letter_occurrences(self, letter: str, frequency: int,
                                        operator, words: List[str]) -> List[str]:
        return [word for word in words if operator(self.words_letter_count[word][letter], frequency)]

    def filter_words_position(self, letter, positions, words):
        return [word for word in words if all(word[pos] == letter for pos in positions)]

    def filter_words_not_position(self, letter, positions, words):
        return [word for word in words if all(word[pos] != letter for pos in positions)]

    def filter_words(self, word: str, pattern: List[Color]):
        rules = self.analyse_pattern(word, pattern)
        if rules is None:
            return []

        filtered = self.filtered
        for rule in rules:
            filtered = self.filter_words_letter_occurrences(
                rule.letter, rule.frequency, rule.operator, filtered)
            if len(rule.positions) > 0:
                filtered = self.filter_words_position(
                    rule.letter, rule.positions, filtered)
            if len(rule.not_positions) > 0:
                filtered = self.filter_words_not_position(
                    rule.letter, rule.not_positions, filtered)

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
