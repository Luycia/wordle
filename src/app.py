import multiprocessing
import random
import string
from typing import Any, Dict, List

from termcolor import cprint

import utils
from model import Color, Difficulty, GameConfig, SolverHelp
from solving import Solver


class Wordle:
    def __init__(self, secret_words: List[str], word_list: List[str] = None,
                 config: GameConfig = None, solver: Solver = None, max_guesses: int = 6) -> None:

        self.secret_words = secret_words
        self.word_list = word_list
        self.config = config if config else GameConfig()
        if self.config.difficulty > Difficulty.Easy and not self.word_list:
            raise ValueError(
                "For a higher difficulty level than 'Easy' a word_list must be specified")
        self.solver = solver
        self.max_guesses = max_guesses

    def get_pattern_from_guess(self, guess: str, secret_word: str) -> List[Color]:
        pattern = []
        for i, letter in enumerate(guess):
            if letter in secret_word:
                if secret_word[i] == letter:
                    pattern.append(Color.Green)
                else:
                    pattern.append(Color.Yellow)
            else:
                pattern.append(Color.Grey)
        return pattern

    def show_guesses(self, guesses: List[str] = None, patterns: List[List[Color]] = None,
                     entropy_gains: List[float] = None):
        print("Last guesses:")
        if not guesses:
            if self.guesses:
                guesses = self.guesses
            else:
                guesses = [5*'?']
        if not patterns:
            if self.patterns:
                patterns = self.patterns
            else:
                patterns = [5*[None]]

        if not entropy_gains:
            if self.entropy_gains:
                entropy_gains = self.entropy_gains
            else:
                entropy_gains = len(guesses) * [None]

        for guess, pattern, gain in zip(guesses, patterns, entropy_gains):
            print('\t', end='')
            for letter, color in zip(guess, pattern):
                if color:
                    color = color.name.lower()
                cprint(letter, color, attrs=['bold'], end=' ')
            if gain:
                print(f'[{gain:.2f} bit]', end='')
            print()
        print()

    def show_letter_panel(self):
        letters = {letter: None for letter in string.ascii_lowercase}
        for guess, pattern in zip(self.guesses, self.patterns):
            for letter, color in zip(guess, pattern):
                if not letters[letter] or color > letters[letter]:
                    letters[letter] = color

        print('\t', end='')
        for letter, color in letters.items():
            if color:
                color = color.name.lower()
            cprint(letter, color, attrs=['bold'], end=' ')
        print('\n')

    def show_solver(self, n_tops: int = 5):
        start_entropy = self.solver.get_words_entropy()
        print(
            f"Before guess entropy {start_entropy:.2f}, {len(self.solver.filtered)} possible words left")
        if self.n_guess == 1:
            solver_tips = self.solver.start_recomendation[:n_tops]
        else:
            solver_tips = self.solver.get_best_guess(n_tops)

        print("Solver tips: ", [(word, round(bit, 2))
              for word, bit in solver_tips], '\n')

    def pass_difficulty_check(self, user_input: str) -> bool:
        if self.config.difficulty >= Difficulty.Medium:
            if user_input not in self.word_list:
                print("Not in word list")
                return False

            if self.config.difficulty == Difficulty.Hard and self.n_guess > 1:
                for pos, (letter, color) in enumerate(zip(self.guesses[-1],
                                                          self.patterns[-1])):
                    if color == Color.Green:
                        if user_input[pos] != letter:
                            print(f"{pos}st letter must be {letter}")
                            return False
                    if color == Color.Yellow:
                        if letter not in user_input:
                            print(f"Guess must contain {letter}")
                            return False

        return True

    def get_guess(self):
        user_input = ""
        while True:
            user_input = input("Next guess ... ").lower().strip()
            if self.solver and user_input == 'tip':
                self.show_solver()
                continue
            if len(user_input) != 5 or not user_input.isalpha():
                continue

            if self.pass_difficulty_check(user_input):
                break

        return user_input

    def play(self):
        if self.solver:
            print("\nStarting new game with solver")
            self.solver.reset()
        else:
            print("\nStarting new game")

        secret_word = random.choice(self.secret_words)
        self.patterns = []
        self.guesses = []
        self.entropy_gains = []

        for n_guess in range(1, self.max_guesses + 1):
            self.n_guess = n_guess
            print(f"\n\nGuess {n_guess}")
            self.show_guesses()
            self.show_letter_panel()
            if self.solver:
                start_entropy = self.solver.get_words_entropy()
                if self.config.solver_help == SolverHelp.Yes:
                    self.show_solver()
            guess = self.get_guess()
            pattern = self.get_pattern_from_guess(guess, secret_word)
            self.guesses.append(guess)
            self.patterns.append(pattern)
            if guess == secret_word:
                self.entropy_gains = None
                self.show_guesses([guess], [pattern])
                print(
                    f"You have won after {n_guess} guesses. The secret word was {guess}.")
                return
            if self.solver:
                self.solver.feed(guess, pattern)
                end_entropy = self.solver.get_words_entropy()
                self.entropy_gains.append(start_entropy - end_entropy)
        print(f"You have lost. The secret word was {guess}.")


def select_options(options: List[str], default: str = '1') -> str:
    options_str = "  ".join(
        [f"{i+1}: {option}" for i, option in enumerate(options)])
    while True:
        user_input = input(f"  {options_str} [{default}] ") or default
        if user_input.isnumeric():
            user_input = int(user_input)
            if user_input >= 1 and user_input <= len(options):
                return options[user_input-1]


def load_solver(five_letter_words: List[str]) -> Solver:
    try:
        start_recomendations_str = utils.read_lines(
            'data/start_recomendations.txt')
        start_recomendations = []
        for line in start_recomendations_str:
            line = [l.strip() for l in line.split(',')]
            start_recomendations.append((line[0], float(line[1])))
    except FileNotFoundError:
        start_recomendations = None
    except Exception as e:
        print(e)

    solver = Solver(five_letter_words, start_recomendations)
    start_recomendation = [
        f'{r[0]}, {r[1]}'for r in solver.start_recomendation]
    utils.write_lines('data/start_recomendations.txt', start_recomendation)

    return solver


def configure_game() -> GameConfig:
    print("Select game configuration")
    config = {}
    config['solver_help'] = SolverHelp[select_options(
        [d.name for d in SolverHelp], default='1')]
    config['difficulty'] = Difficulty[select_options(
        [d.name for d in Difficulty], default='2')]
    return GameConfig(**config)


def main():
    print("Stop the game with ctrl + c (KeyboardInterrupt)")
    secret_words = utils.read_lines('data/wordle_words.txt')
    five_letter_words = utils.read_lines('data/5_letter_words.txt')
    config = configure_game()
    if config.solver_help > SolverHelp.No:
        solver = load_solver(five_letter_words)
        print("Type 'tip' for solver recomendations")
    else:
        solver = None

    wordle = Wordle(secret_words, five_letter_words, config, solver)
    while True:
        wordle.play()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        main()
    except KeyboardInterrupt:
        print('Good Bye :)')
