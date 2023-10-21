from pathlib import Path
from typing import List
import random
import utils
from solving import Solver
from model import Color
from termcolor import cprint

MAX_GUESSES = 6


def get_pattern_from_guess(guess: str, secret_word: str) -> List[Color]:
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


def show_patterns(guesses: List[str], patterns: List[List[Color]],
                  entropy_gains: List[float] = None):
    print("Last guesses:")
    if not guesses:
        guesses = [5*'?']
    if not patterns:
        patterns = [5*[None]]
    if not entropy_gains:
        entropy_gains = len(guesses) * [None]

    for guess, pattern, gain in zip(guesses, patterns, entropy_gains):
        print('\t', end='')
        for letter, color in zip(guess, pattern):
            if color:
                color = color.value
            cprint(letter, color, attrs=['bold'], end=' ')
        if gain:
            print(f'[{gain:.2f} bit]', end='')
        print()
    print()


def get_input():
    user_input = ""
    while len(user_input) != 5:
        user_input = input("Next guess ... ").lower().strip()
    return user_input


def play(secret_words: List[str], solver: Solver = None):
    if solver:
        print("\nStarting new game with solver")
        solver.reset()
    else:
        print("\nStarting new game")

    secret_word = random.choice(secret_words)
    patterns = []
    guesses = []
    entropy_gains = []

    for n_guess in range(1, MAX_GUESSES + 1):
        print(f"\n\nGuess {n_guess}")
        show_patterns(guesses, patterns, entropy_gains)
        if solver:
            start_entropy = solver.get_words_entropy()
            print(
                f"Before guess entropy {start_entropy:.2f}, {len(solver.filtered)} possible words left")
            solver_tips = solver.get_best_guess(
                5) if n_guess > 1 else solver.start_recomendation[:5]
            print("Solver tips: ", [(word, round(bit, 2))
                  for word, bit in solver_tips], '\n')
        guess = get_input()
        guesses.append(guess)
        patterns.append(get_pattern_from_guess(guess, secret_word))
        if guess == secret_word:
            show_patterns([guesses[-1]], [patterns[-1]])
            print(
                f"You have won after {n_guess} guesses. The secret word was {guess}.")
            return
        if solver:
            solver.feed(guess, patterns[-1])
            end_entropy = solver.get_words_entropy()
            entropy_gains.append(start_entropy - end_entropy)
    print(f"You have lost. The secret word was {guess}.")


def main(use_solver: bool = False):
    print("Stop the game with ctrl + c (KeyboardInterrupt)")
    secret_words = utils.read_lines('data/wordle_words.txt')

    if use_solver:
        five_letter_words = utils.read_lines('data/5_letter_words.txt')
        try:
            start_recomendations_str = utils.read_lines(
                'data/start_recomendations.txt')
            start_recomendations = []
            for line in start_recomendations_str:
                line = [l.strip() for l in line.split(',')]
                start_recomendations.append((line[0], float(line[1])))
        except FileNotFoundError:
            start_recomendations = None

        solver = Solver(five_letter_words, start_recomendations)
        start_recomendation = [
            f'{r[0]}, {r[1]}'for r in solver.start_recomendation]
        utils.write_lines('data/start_recomendations.txt', start_recomendation)
    else:
        solver = None

    while True:
        play(secret_words, solver=solver)


if __name__ == '__main__':
    try:
        main(use_solver=True)
    except KeyboardInterrupt:
        print('Good Bye :)')
