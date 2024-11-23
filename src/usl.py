#!/usr/bin/python3.13


import sys, pprint
from termcolor import colored

from rules import RulesBreak
from tokenizer import Tokenizer, Token, Pointer
from errors import *


def main() -> None:
    lines: list[str] = []

    file_name: str = sys.argv[1]

    if not file_name.endswith(".usl"):
        print("Not a .usl file")
        return

    try:
        with open(file_name, "r+") as file:
            lines = file.read().split('\n')

        try:
            tokenizer: Tokenizer = Tokenizer(Pointer(lines))

            tokens: list[Token] = []

            tokens = tokenizer.parse_to_tokens()

            pprint.pprint(tokens)
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


if __name__ == "__main__":
    main()