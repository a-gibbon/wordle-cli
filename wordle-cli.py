#!/usr/bin/python3


import argparse
import random
import string
import sys
import time

from copy import deepcopy
from os.path import exists
from timeit import default_timer as timer


FG_WHITE = "\033[38;5;255m"
FG_BLACK = "\033[38;5;232m"
BG_WHITE = "\033[48;5;255m"
BG_GRAYS = "\033[48;5;244m"
BG_BLACK = "\033[48;5;240m"
BG_GREEN = "\033[48;5;34m"
BG_AMBER = "\033[48;5;214m"
RESET    = "\033[0m"
SPACE    = "    "


keyboard_layout = (["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
                   ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
                   ["Z", "X", "C", "V", "B", "N", "M"])

keyboard = deepcopy(keyboard_layout)
tracking = deepcopy(keyboard_layout)


class ArgumentParser(argparse.ArgumentParser):
    def _check_value(self, action, value):
        from argparse import ArgumentError
        from gettext import gettext as _
        if action.choices is not None and value not in action.choices:
            args = {'value': value,
                    'choices': action.metavar}
            msg = _('invalid choice: %(value)r (choose from %(choices)s)')
            raise ArgumentError(action, msg % args)


try:
    import msvcrt

    def key_pressed():
        return msvcrt.kbhit()

    def read_key():
        key = msvcrt.getch()
        try:
            key = str(key, encoding="utf8")
        except:
            pass
        return key
    def pause(i):
        try:
            time.sleep(i)
        except KeyboardInterrupt:
            pass
        finally:
            # this will prevent keys being sent to stdout
            # while sleep is occurring
            while key_pressed():
                read_key()
except ImportError:
    import select
    import tty
    import termios
    import atexit

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)

    def restore_settings(old_settings):
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def key_pressed():
        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

    def read_key():
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)
        finally:
            restore_settings(old_settings)
        return key

    def pause(i):
        try:
            time.sleep(i)
        except KeyboardInterrupt:
            pass
        finally:
            # this will prevent keys being sent to stdout
            # while sleep is occurring
            while key_pressed():
                termios.tcflush(fd, termios.TCIOFLUSH)

    atexit.register(restore_settings, old_settings)


def center(char, i=3):
    return char.center(i)


def split(word):
    return [ char for char in word.strip() ]


def create_keyboard():
    for i in range(len(keyboard)):
        for j in range(len(keyboard[i])):
            key = keyboard[i][j]
            keyboard[i][j] = f"{FG_WHITE}{BG_GRAYS}{center(key)}{RESET}"


def update_keyboard(weight, BG_COLOR, key):
    for i in range(len(keyboard)):
        for j in range(len(keyboard[i])):
            if key != keyboard_layout[i][j]:
                continue
            elif key != tracking[i][j]:
                if weight <= tracking[i][j]:
                    continue
            keyboard[i][j] = f"{FG_WHITE}{BG_COLOR}{center(key)}{RESET}"
            tracking[i][j] = weight

def display_keyboard(c):
    keys = ""
    for i in range(len(keyboard)):
        for j in range(len(keyboard[i])):
            keys += keyboard[i][j]
        keys += "\n"
        if i < len(keyboard)-1:
            keys += " " * (i+1)
    if c > 0:
        print(f"\033[{c+4}F{keys}", end="\n"*(c+1))
    else:
        print(keys)


def wordle(word, words):
    create_keyboard()

    is_correct = False
    attempts = 0

    for guess in ([], [], [], [], [], []):
        display_keyboard(attempts)

        # if guess is correct, break
        if is_correct:
            break

        # print empty black squares
        empty = ''.join([center(" ") for _ in range(len(word)) ])
        print(f"{SPACE}{FG_WHITE}{BG_BLACK}{empty}{RESET}", end=f"\r{SPACE}")

        while True:
            start = timer()
            try:
                char = read_key()
            except KeyboardInterrupt:
                exit()
            end = timer()

            # check time it takes to input key
            # this stops arrow key input from breaking loop
            if (end-start) < 0.05:
                continue
            # if key is <CTRL+C>, exit
            elif char == "\x03":
                print()
                return None, None
            # if key is <BACKSPACE>, remove last element in guess
            elif char == "\x7f":
                try:
                    guess.pop()
                except IndexError:
                    pass
            elif char == "\x0d":
                if len(guess) < len(word):
                    print(f"\n{SPACE}Not enough letters", end="")
                    pause(2)
                    print("\033[2K\033[1F", end=f"\r{SPACE}")
                elif ''.join(guess) not in words:
                    print(f"\n{SPACE}Not in word list", end="")
                    pause(2)
                    print("\033[2K\033[1F", end=f"\r{SPACE}")
                else:
                    break
            elif len(guess) < len(word):
                # if char is an ASCII char, append
                if char in string.ascii_letters:
                    char = char.upper()
                    guess.append(char)

            print(f"\r{SPACE}{FG_WHITE}{BG_BLACK}{empty}{RESET}", end="")
            chars = ''.join([center(c) for c in guess])
            print(f"\r{SPACE}{FG_WHITE}{BG_BLACK}{chars}{RESET}", end="")

        chars = ""
        for i in range(len(guess)):
            if guess[i] == word[i]:
                chars += BG_GREEN + center(guess[i])
                update_keyboard(3, BG_GREEN, guess[i])
            elif (guess[0:i+1].count(guess[i]) <= word.count(guess[i])):
                chars += BG_AMBER + center(guess[i])
                update_keyboard(2, BG_AMBER, guess[i])
            else:
                chars += BG_BLACK + center(guess[i])
                update_keyboard(1, BG_BLACK, guess[i])
            pause(0.25)
            print(f"\r{SPACE}{FG_WHITE}{chars}{RESET}", end="")

        print(f"\r{SPACE}{FG_WHITE}{chars}{RESET}")

        attempts += 1

        if guess == word:
            is_correct = True

    return attempts, is_correct


if __name__ == "__main__":
    word_file = 'words.txt'

    if not exists(word_file):
        exit(f"Word file '{word_file}' cannot be found")

    with open(word_file, 'r') as fp:
        words = [ word.upper().strip() for word in fp.readlines() ]

    parser = ArgumentParser()
    parser.add_argument(
        '-w',
        '--word',
        help='select a specific word from the word list by line number',
        type=int,
        choices=range(1, len(words)+1),
        metavar=f'1-{len(words)}',
        dest='WORD_NUMBER')

    args = parser.parse_args()

    if args.WORD_NUMBER:
        word = words[args.WORD_NUMBER-1]
    else:
        word = random.choice(words)

    attempts, is_correct = wordle(split(word), words)

    if attempts is None and is_correct is None:
        exit()

    if not is_correct:
        attempts = 'X'
        print(f"{SPACE}{FG_BLACK}{BG_WHITE}{center(word, len(word)*3)}{RESET}")

    print(f"\nWordle {words.index(word)+1} {attempts}/{len(word)+1}")

