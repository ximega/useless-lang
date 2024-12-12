#!/usr/bin/python3.13

import sys, pprint
from termcolor import colored

from src.rules import RulesBreak
from src.errors import *
from src.tokens.tokenizer import Tokenizer
from src.tokens.tokenclass import Token
from src.tokens.pointer import Pointer


def output(lines: list[str]) -> None:
    tokenizer: Tokenizer = Tokenizer(Pointer(lines))
    tokens: list[Token] = tokenizer.parse_to_tokens()
    pprint.pprint(tokens)

def debug(file_name: str) -> None:
    lines: list[str] = []
    if not file_name.endswith(".usl"):
        print("Not a .usl file")
        return
    try:
        with open(file_name, "r+") as file:
            lines = file.read().split('\n')
        output(lines)
    except FileNotFoundError as exc:
        print(exc.args[1] + ": " + file_name)
        return

def compile() -> None:
    pass

def interpret(file_name: str) -> None:
    lines: list[str] = []
    if not file_name.endswith(".usl"):
        print("Not a .usl file")
        return
    try:
        with open(file_name, "r+") as file:
            lines = file.read().split('\n')
        try:
            output(lines)
        except (
            SyntaxException,
            OwnershipException,
            DuplicationException,
            TokenizerException,
            RulesBreak,
        ) as exc:
            print(
                '\n' +
                colored(exc.args[0], "red", attrs=["bold"]) + ': ' + colored(exc.args[1], "red") + "\n\n" +
                colored(exc.args[2], "white") + '\n' +
                colored(exc.args[3], "magenta", attrs=["bold"])
            )
            return
    except FileNotFoundError as exc:
        print(exc.args[1] + ": " + file_name)
        return

def main() -> None:
    match sys.argv[1]:
        case "--debug" | "-d":
            debug(sys.argv[2])
        case "--compile" | "-c":
            pass
        case "--interpret" | "-i":
            interpret(sys.argv[2])
        case _:
            interpret(sys.argv[1])

if __name__ == "__main__":
    main()