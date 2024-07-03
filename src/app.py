import multiprocessing
import random
import string
from collections import Counter
from typing import Any, Dict, List, Tuple

from termcolor import colored, cprint

import utils
from model import Color, Difficulty, GameConfig, Language, SolverHelp
from solving import Solver


class Wordle:

    def __init__(self, max_guesses: int = 6) -> None:
        print("Stop the game with ctrl + c (KeyboardInterrupt)")
        self.config = configure_game(
            utils.Path.home() / '.wordle/settings.json')
        self.ui_text = utils.read_ini(f'data/{self.config.language.name.lower()}/ui_text.ini',
                                      default=f'data/en/ui_text.ini')
        self.secret_words, self.word_list = load_words(self.config.language)
        if self.config.solver_help > SolverHelp.NEVER:
            self.solver = load_solver(self.word_list, self.config.language)
            print(self.ui_text.get('output', 'solver_hint').format(
                self.ui_text.get('keyboard', 'solver_hint')))
        else:
            self.solver = None

        self.round: Dict = None

        if self.config.difficulty > Difficulty.EASY and not self.word_list:
            raise ValueError(
                "For a higher difficulty level than 'Easy' a word_list must be specified")

        self.max_guesses = max_guesses
        self.letters = {letter: None for letter in string.ascii_lowercase}
        if self.config.language == Language.DE:
            self.letters = {
                letter: None for letter in string.ascii_lowercase + 'äöüß'}
        else:
            self.letters = {
                letter: None for letter in string.ascii_lowercase}

    def get_pattern_from_guess(self, guess: str) -> List[Color]:
        secret_word_freq = self.round['secret_word_freq'].copy()
        possible_yellows = []
        pattern = []

        for i, letter in enumerate(guess):
            if letter in secret_word_freq:
                if self.round['secret_word'][i] == letter:
                    pattern.append(Color.GREEN)
                    secret_word_freq[letter] -= 1
                else:
                    pattern.append(Color.YELLOW)
                    possible_yellows.append(i)
            else:
                pattern.append(Color.GREY)

        for i in possible_yellows:
            letter = guess[i]
            if secret_word_freq[letter] > 0:
                secret_word_freq[letter] -= 1
            else:
                pattern[i] = Color.GREY

        return pattern

    def show_guesses(self, guesses: List[str] = None, patterns: List[List[Color]] = None,
                     entropy_gains: List[float] = None):
        print(self.ui_text.get('output', 'last_guesses'))
        if not guesses:
            if self.round['guesses']:
                guesses = self.round['guesses']
            else:
                guesses = [5*'?']
        if not patterns:
            if self.round['patterns']:
                patterns = self.round['patterns']
            else:
                patterns = [5*[None]]

        if not entropy_gains:
            if self.round['entropy_gains']:
                entropy_gains = self.round['entropy_gains']
            else:
                entropy_gains = len(guesses) * [None]

        for guess, pattern, gain in zip(guesses, patterns, entropy_gains):
            print('\t', end='')
            for letter, color in zip(guess, pattern):
                if color is not None:
                    color = color.name.lower()
                cprint(letter, color, attrs=['bold'], end=' ')
            if gain is not None:
                print(f'[{gain:.2f} bit]', end='')
            print()
        print()

    def show_letter_panel(self):
        letters = self.letters.copy()
        for guess, pattern in zip(self.round['guesses'], self.round['patterns']):
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
        print(self.ui_text.get('output', 'solver_before').format(start_entropy, len(self.solver.filtered)))
        if self.n_guess == 1:
            solver_tips = self.solver.start_recomendations[:n_tops]
        else:
            solver_tips = self.solver.get_best_guess(n_tops)

        print(f"{self.ui_text.get('output', 'solver_tips')} ", [(word, round(bit, 2))
              for word, bit in solver_tips], '\n')

    def pass_difficulty_check(self, user_input: str) -> bool:
        if self.config.difficulty >= Difficulty.MEDIUM:
            if user_input not in self.word_list:
                print(self.ui_text.get('output', 'not_wordlist'))
                return False

            if self.config.difficulty == Difficulty.HARD and self.n_guess > 1:
                for pos, (letter, color) in enumerate(zip(self.round['guesses'][-1],
                                                          self.round['patterns'][-1])):
                    if color == Color.GREEN:
                        if user_input[pos] != letter:
                            print(self.ui_text.get(
                                'output', 'not_letter').format(pos+1, letter))
                            return False
                    if color == Color.YELLOW:
                        if letter not in user_input:
                            print(self.ui_text.get(
                                'output', 'not_contains').format(letter))
                            return False

        return True

    def isalpha(self, word):
        return all(letter in self.letters for letter in word)

    def get_guess(self):
        user_input = ""
        while True:
            user_input = input(
                f"{self.ui_text.get('output', 'next_guess')} ").lower().strip()
            if self.handle_user_input(user_input):
                continue
            if len(user_input) != 5 or not self.isalpha(user_input):
                continue

            if self.pass_difficulty_check(user_input):
                break

        return user_input

    def handle_user_input(self, user_input: str) -> bool:
        if self.solver and user_input == self.ui_text.get('keyboard', 'solver_hint'):
            self.show_solver()
            return True
        return False

    def init_round(self):
        secret_word = random.choice(self.secret_words)
        self.round = {'secret_word': secret_word, 'secret_word_freq': Counter(secret_word),
                      'patterns': [], 'guesses': [], 'entropy_gains': []}

    def play(self):
        if self.solver:
            print(f"\n{self.ui_text.get('output', 'newgame_with_solver')}")
            self.solver.reset()
        else:
            print(f"\n{self.ui_text.get('output', 'newgame_without_solver')}")

        self.init_round()

        for n_guess in range(1, self.max_guesses + 1):
            self.n_guess = n_guess
            print(f"\n\n{self.ui_text.get('output', 'guess_count')} {n_guess}")
            self.show_guesses()
            self.show_letter_panel()
            if self.solver:
                start_entropy = self.solver.get_words_entropy()
                if self.config.solver_help == SolverHelp.ALWAYS:
                    self.show_solver()
            guess = self.get_guess()
            pattern = self.get_pattern_from_guess(guess)
            self.round['guesses'].append(guess)
            self.round['patterns'].append(pattern)
            if guess == self.round['secret_word']:
                self.round['entropy_gains'] = None
                self.show_guesses([guess], [pattern])
                print(self.ui_text.get('output', 'win').format(n_guess, colored(
                    self.round['secret_word'], 'light_green', attrs=['bold'])))

                return
            if self.solver:
                self.solver.feed(guess, pattern)
                end_entropy = self.solver.get_words_entropy()
                self.round['entropy_gains'].append(start_entropy - end_entropy)

        print(self.ui_text.get('output', 'lose').format(colored(
            self.round['secret_word'], 'light_red', attrs=['bold'])))


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


def load_words(lang: Language) -> Tuple[List[str], List[str]]:
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
    wordle = Wordle()
    while True:
        wordle.play()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        main()
    except KeyboardInterrupt:
        print('Good Bye :)')
