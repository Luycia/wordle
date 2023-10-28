import multiprocessing
import random
import string
from typing import Any, Dict, List

from termcolor import colored, cprint

import utils
from model import Color, Difficulty, GameConfig, Language, SolverHelp
from solving import Solver


class Wordle:
    def __init__(self, secret_words: List[str], word_list: List[str] = None,
                 config: GameConfig = None, solver: Solver = None, max_guesses: int = 6) -> None:

        self.secret_words = secret_words
        self.word_list = word_list
        self.config = config if config else GameConfig()
        if self.config.difficulty > Difficulty.EASY and not self.word_list:
            raise ValueError(
                "For a higher difficulty level than 'Easy' a word_list must be specified")
        self.solver = solver
        self.max_guesses = max_guesses
        self.letters = {letter: None for letter in string.ascii_lowercase}
        if config.language == Language.DE:
            self.letters = {
                letter: None for letter in string.ascii_lowercase + 'äöüß'}
        else:
            self.letters = {
                letter: None for letter in string.ascii_lowercase}

    def get_pattern_from_guess(self, guess: str, secret_word: str) -> List[Color]:
        pattern = []
        for i, letter in enumerate(guess):
            if letter in secret_word:
                if secret_word[i] == letter:
                    pattern.append(Color.GREEN)
                else:
                    pattern.append(Color.YELLOW)
            else:
                pattern.append(Color.GREY)
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
                if color is not None:
                    color = color.name.lower()
                cprint(letter, color, attrs=['bold'], end=' ')
            if gain:
                print(f'[{gain:.2f} bit]', end='')
            print()
        print()

    def show_letter_panel(self):
        letters = self.letters.copy()
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
            solver_tips = self.solver.start_recomendations[:n_tops]
        else:
            solver_tips = self.solver.get_best_guess(n_tops)

        print("Solver tips: ", [(word, round(bit, 2))
              for word, bit in solver_tips], '\n')

    def pass_difficulty_check(self, user_input: str) -> bool:
        if self.config.difficulty >= Difficulty.MEDIUM:
            if user_input not in self.word_list:
                print("Not in word list")
                return False

            if self.config.difficulty == Difficulty.HARD and self.n_guess > 1:
                for pos, (letter, color) in enumerate(zip(self.guesses[-1],
                                                          self.patterns[-1])):
                    if color == Color.GREEN:
                        if user_input[pos] != letter:
                            print(f"{pos+1}st letter must be {letter}")
                            return False
                    if color == Color.YELLOW:
                        if letter not in user_input:
                            print(f"Guess must contain {letter}")
                            return False

        return True

    def isalpha(self, word):
        return all(letter in self.letters for letter in word)

    def get_guess(self):
        user_input = ""
        while True:
            user_input = input("Next guess ... ").lower().strip()
            if self.solver and user_input == 'tip':
                self.show_solver()
                continue
            if len(user_input) != 5 or not self.isalpha(user_input):
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
                if self.config.solver_help == SolverHelp.ALWAYS:
                    self.show_solver()
            guess = self.get_guess()
            pattern = self.get_pattern_from_guess(guess, secret_word)
            self.guesses.append(guess)
            self.patterns.append(pattern)
            if guess == secret_word:
                self.entropy_gains = None
                self.show_guesses([guess], [pattern])
                print(
                    f"You have won after {n_guess} guesses. The secret word was {colored(secret_word, 'light_green', attrs=['bold'])}.")
                return
            if self.solver:
                self.solver.feed(guess, pattern)
                end_entropy = self.solver.get_words_entropy()
                self.entropy_gains.append(start_entropy - end_entropy)
        print(
            f"You have lost. The secret word was {colored(secret_word, 'light_red', attrs=['bold'])}.")


def load_solver(database: List[str], lang: Language) -> Solver:
    lang = lang.name.lower()
    try:
        start_recomendations_str = utils.read_textlines(
            f'data/{lang}/solver.txt')
        start_recomendations = []
        for line in start_recomendations_str:
            line = [l.strip() for l in line.split(',')]
            start_recomendations.append((line[0], float(line[1])))
    except FileNotFoundError:
        start_recomendations = None
    except Exception as e:
        print(e)

    solver = Solver(database, start_recomendations)
    if not start_recomendations:
        start_recomendations = [
            f'{r[0]}, {r[1]}'for r in solver.start_recomendations]
        utils.write_textlines(f'data/{lang}/solver.txt', start_recomendations)

    return solver


def load_words(lang: Language):
    lang = lang.name.lower()
    secret_words = utils.read_textlines(f'data/{lang}/wordle_words.txt')
    database = utils.read_textlines(f'data/{lang}/database.txt')
    return secret_words, database


def select_options(option):
    cls = type(option)
    help = cls.__name__
    default = str(option.value)
    options = [x.name for x in cls]
    options_str = "  ".join(
        [f"{i+1}: {option}" for i, option in enumerate(options)])
    options_str = f"{help}\t{options_str}"

    while True:
        user_input = input(f"  {options_str}  [{option.name}] ") or default
        if user_input.isnumeric():
            user_input = int(user_input)
            if user_input >= 1 and user_input <= len(options):
                return cls[options[user_input-1]]


def configure_game(path: str) -> GameConfig:
    print("Select game configuration (type number)")
    config = GameConfig.from_file(path)
    for key, default in config.__dict__.items():
        config.__setattr__(key, select_options(default))
    config.to_file(path)
    return config


def main():
    print("Stop the game with ctrl + c (KeyboardInterrupt)")
    config = configure_game(utils.Path.home() / '.wordle/settings.json')
    secret_words, database = load_words(config.language)
    if config.solver_help > SolverHelp.NEVER:
        solver = load_solver(database, config.language)
        print("Type 'tip' for solver recomendations")
    else:
        solver = None

    wordle = Wordle(secret_words, database, config, solver)
    while True:
        wordle.play()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        main()
    except KeyboardInterrupt:
        print('Good Bye :)')
